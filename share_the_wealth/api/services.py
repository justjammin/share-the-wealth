"""
API service layer - aggregates data for endpoints.
"""

from collections import defaultdict

from share_the_wealth.models import PoliticianTrade
from share_the_wealth.sources import TradeFetcher, HedgeFundRepository, PriceService
from share_the_wealth.api.state import MirrorState
from share_the_wealth.api.fmp_budget import FMPCache, fmp_budget
from share_the_wealth.config import Settings

# Fallback when FMP API fails or returns empty (no key, rate limit, etc.)
_politician_using_fallback = False

CURATED_POLITICIANS = [
    {
        "name": "Nancy Pelosi",
        "party": "D",
        "avatar": "NP",
        "trades": [
            {"ticker": "NVDA", "action": "BUY", "shares": 50, "price": 875.20, "date": "2024-12-10", "value": 43760},
            {"ticker": "MSFT", "action": "BUY", "shares": 100, "price": 415.50, "date": "2024-11-22", "value": 41550},
            {"ticker": "AAPL", "action": "SELL", "shares": 200, "price": 229.00, "date": "2024-11-05", "value": 45800},
            {"ticker": "AMZN", "action": "BUY", "shares": 75, "price": 196.30, "date": "2024-10-18", "value": 14722},
        ],
    },
    {
        "name": "Dan Crenshaw",
        "party": "R",
        "avatar": "DC",
        "trades": [
            {"ticker": "XOM", "action": "BUY", "shares": 300, "price": 118.40, "date": "2024-12-05", "value": 35520},
            {"ticker": "CVX", "action": "BUY", "shares": 150, "price": 156.20, "date": "2024-11-30", "value": 23430},
            {"ticker": "LMT", "action": "BUY", "shares": 80, "price": 520.00, "date": "2024-11-14", "value": 41600},
        ],
    },
    {
        "name": "Tommy Tuberville",
        "party": "R",
        "avatar": "TT",
        "trades": [
            {"ticker": "RTX", "action": "BUY", "shares": 200, "price": 121.50, "date": "2024-12-01", "value": 24300},
            {"ticker": "GD", "action": "BUY", "shares": 100, "price": 272.00, "date": "2024-11-20", "value": 27200},
            {"ticker": "GOOGL", "action": "BUY", "shares": 50, "price": 175.40, "date": "2024-10-30", "value": 8770},
        ],
    },
    {
        "name": "Josh Gottheimer",
        "party": "D",
        "avatar": "JG",
        "trades": [
            {"ticker": "META", "action": "BUY", "shares": 40, "price": 580.00, "date": "2024-12-08", "value": 23200},
            {"ticker": "TSLA", "action": "BUY", "shares": 60, "price": 352.00, "date": "2024-11-28", "value": 21120},
            {"ticker": "NFLX", "action": "SELL", "shares": 30, "price": 820.00, "date": "2024-11-10", "value": 24600},
        ],
    },
]


class PoliticianService:
    def __init__(self):
        self._fetcher = TradeFetcher()
        self._prices = PriceService()

    def _party_from_name(self, name: str) -> str:
        name_lower = (name or "").lower()
        if any(x in name_lower for x in ["pelosi", "warren", "sanders", "gottheimer", "schumer"]):
            return "D"
        if any(x in name_lower for x in ["crenshaw", "tuberville", "mcconnell", "mccarthy"]):
            return "R"
        return "I"

    def _trade_to_api(self, t: PoliticianTrade, current_price: float | None) -> dict:
        amount_str = str(t.amount_range or "")
        price = 0.0
        for part in amount_str.replace(",", "").split():
            try:
                price = float(part)
                break
            except ValueError:
                pass
        if not price and current_price:
            price = current_price
        if not price:
            price = 100.0
        value_est = 15000.0
        shares = int(value_est / price) if price else 50
        action = "BUY" if "Purchase" in t.transaction_type or "Buy" in str(t.transaction_type) else "SELL"
        return {
            "ticker": t.symbol,
            "action": action,
            "shares": shares,
            "price": round(price, 2),
            "date": (t.transaction_date or "")[:10],
            "value": round(shares * price, 0),
        }

    def _fetch_politicians_internal(self) -> list[dict]:
        global _politician_using_fallback
        try:
            trades = self._fetcher.fetch_all(limit_per_chamber=25)
        except Exception:
            trades = []
        symbols = list({t.symbol for t in trades})
        prices = self._prices.get_prices(symbols)

        by_politician: dict[str, list[PoliticianTrade]] = defaultdict(list)
        for t in trades:
            by_politician[t.politician_name or "Unknown"].append(t)

        result = []
        seen = set()
        for name, pol_trades in by_politician.items():
            if not name or name in seen:
                continue
            seen.add(name)
            words = name.split()
            avatar = "".join(w[0] for w in words[-2:])[:2].upper() if len(words) >= 2 else name[:2].upper()
            result.append({
                "name": name,
                "party": self._party_from_name(name),
                "avatar": avatar,
                "trades": [self._trade_to_api(t, prices.get(t.symbol)) for t in pol_trades[:10]],
            })
        if not result:
            _politician_using_fallback = True
            return CURATED_POLITICIANS
        _politician_using_fallback = False
        return result

    def get_politicians_with_trades(self, fresh: bool = False) -> list[dict]:
        global _politician_using_fallback
        if not fresh and Settings.READ_FROM_WAREHOUSE:
            from share_the_wealth.warehouse.repository import load_latest_politicians
            snap = load_latest_politicians()
            if snap is not None:
                pols, fb = snap
                _politician_using_fallback = fb
                return pols
        return _politician_cache.get(fresh)


def _fetch_politicians_cached() -> list[dict]:
    svc = PoliticianService()
    return svc._fetch_politicians_internal()


_politician_cache = FMPCache(_fetch_politicians_cached)


class PortfolioService:
    def __init__(self, mirror_state: MirrorState):
        self._mirror = mirror_state
        self._politician_svc = PoliticianService()
        self._fund_repo = HedgeFundRepository()
        self._prices = PriceService()

    def get_positions(self) -> list[dict]:
        politicians = self._politician_svc.get_politicians_with_trades()
        funds = self._fund_repo.list_all()["funds"]
        pol_mirrored = self._mirror.politicians
        fund_mirrored = self._mirror.funds

        positions = []
        symbols = set()

        for p in politicians:
            if p["name"] not in pol_mirrored:
                continue
            for t in p["trades"]:
                if t["action"] != "BUY":
                    continue
                symbols.add(t["ticker"])
                positions.append({
                    "ticker": t["ticker"],
                    "source": p["name"],
                    "type": "Politician",
                    "shares": t["shares"],
                    "cost": t["price"],
                    "current": t["price"],
                    "pl": 0,
                    "value": t["shares"] * t["price"],
                })

        for f in funds:
            if f["name"] not in fund_mirrored:
                continue
            for h in f["holdings"]:
                symbols.add(h["ticker"])
                positions.append({
                    "ticker": h["ticker"],
                    "source": f["name"],
                    "type": "Hedge Fund",
                    "shares": 100,
                    "cost": 100,
                    "current": 100,
                    "pl": h["change"],
                    "value": 10000,
                })

        prices = self._prices.get_prices(list(symbols))
        for pos in positions:
            curr = prices.get(pos["ticker"], pos["current"])
            pos["current"] = curr
            pos["pl"] = ((curr - pos["cost"]) / pos["cost"] * 100) if pos["cost"] else 0
            pos["value"] = pos["shares"] * curr

        return positions


class ContextBuilder:
    def __init__(self, mirror_state: MirrorState):
        self._mirror = mirror_state
        self._politician_svc = PoliticianService()
        self._fund_repo = HedgeFundRepository()

    def build(self) -> str:
        pol_names = ", ".join(self._mirror.politicians or ["none"])
        fund_names = ", ".join(self._mirror.funds or ["none"])
        politicians = self._politician_svc.get_politicians_with_trades()
        funds = self._fund_repo.list_all()["funds"]

        pol_trades = []
        for p in politicians:
            if p["name"] in self._mirror.politicians:
                for t in p["trades"]:
                    pol_trades.append(f"{p['name']}: {t['action']} {t['ticker']} x{t['shares']} @ ${t['price']}")

        fund_holdings = []
        for f in funds:
            if f["name"] in self._mirror.funds:
                for h in f["holdings"]:
                    fund_holdings.append(f"{f['name']}: {h['ticker']} ({h['pct']}% of portfolio)")

        return (
            f"Mirrored Politicians: {pol_names}\n"
            f"Mirrored Funds: {fund_names}\n\n"
            f"Congressional Trades:\n" + "\n".join(pol_trades or ["None"]) + "\n\n"
            f"Hedge Fund Holdings:\n" + "\n".join(fund_holdings or ["None"])
        )

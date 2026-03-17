"""
API service layer - aggregates data for endpoints.
"""

from collections import defaultdict

from share_the_wealth.models import PoliticianTrade
from share_the_wealth.sources import TradeFetcher, HedgeFundRepository, PriceService
from share_the_wealth.api.state import MirrorState


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

    def get_politicians_with_trades(self) -> list[dict]:
        try:
            trades = self._fetcher.fetch_all(limit_per_chamber=50)
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
        return result


class PortfolioService:
    def __init__(self, mirror_state: MirrorState):
        self._mirror = mirror_state
        self._politician_svc = PoliticianService()
        self._fund_repo = HedgeFundRepository()
        self._prices = PriceService()

    def get_positions(self) -> list[dict]:
        politicians = self._politician_svc.get_politicians_with_trades()
        funds = self._fund_repo.list_all()
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
        funds = self._fund_repo.list_all()

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

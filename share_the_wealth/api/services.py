"""
API service layer.
"""

from share_the_wealth.sources import HedgeFundRepository, PriceService
from share_the_wealth.api.state import MirrorState
from share_the_wealth.config import Settings


class PortfolioService:
    def __init__(self, mirror_state: MirrorState):
        self._mirror = mirror_state
        self._fund_repo = HedgeFundRepository()
        self._prices = PriceService()

    def get_positions(self) -> list[dict]:
        funds = self._fund_repo.list_all()["funds"]
        fund_mirrored = self._mirror.funds

        positions = []
        symbols: set[str] = set()

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
        self._fund_repo = HedgeFundRepository()

    def build(self) -> str:
        fund_names = ", ".join(self._mirror.funds or ["none"])
        funds = self._fund_repo.list_all()["funds"]

        fund_holdings = []
        for f in funds:
            if f["name"] in self._mirror.funds:
                for h in f["holdings"]:
                    fund_holdings.append(f"{f['name']}: {h['ticker']} ({h['pct']}% of portfolio)")

        return (
            f"Mirrored Funds: {fund_names}\n\n"
            f"Hedge Fund Holdings:\n" + "\n".join(fund_holdings or ["None"])
        )

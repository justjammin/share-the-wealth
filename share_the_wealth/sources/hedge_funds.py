"""
Hedge fund 13F-style holdings repository.
"""

from share_the_wealth.models import HedgeFund, Holding


class HedgeFundRepository:
    _FUNDS: list[HedgeFund] = [
        HedgeFund(
            name="Berkshire Hathaway",
            manager="Warren Buffett",
            avatar="BH",
            aum="$900B",
            holdings=[
                Holding("AAPL", 42.8, "905M", "$174B", -0.8),
                Holding("BAC", 9.6, "1.03B", "$39B", 2.1),
                Holding("AXP", 8.7, "151M", "$35B", 1.4),
                Holding("KO", 7.2, "400M", "$29B", 0.3),
                Holding("CVX", 5.1, "118M", "$21B", -1.2),
            ],
        ),
        HedgeFund(
            name="Pershing Square",
            manager="Bill Ackman",
            avatar="PS",
            aum="$16B",
            holdings=[
                Holding("HLT", 18.4, "13.5M", "$2.9B", 3.2),
                Holding("CMG", 16.2, "2.4M", "$2.6B", 1.8),
                Holding("QSR", 14.1, "24M", "$2.2B", -0.5),
                Holding("CP", 12.8, "22M", "$2.0B", 0.9),
                Holding("GOOG", 10.3, "5.6M", "$1.6B", 2.4),
            ],
        ),
        HedgeFund(
            name="Tiger Global",
            manager="Chase Coleman",
            avatar="TG",
            aum="$22B",
            holdings=[
                Holding("META", 22.1, "8.2M", "$4.9B", 4.1),
                Holding("MSFT", 17.6, "10.1M", "$3.9B", 1.2),
                Holding("NVDA", 15.3, "3.8M", "$3.4B", 5.8),
                Holding("AMZN", 12.4, "18.6M", "$2.7B", 2.6),
                Holding("SNOW", 8.7, "17.4M", "$1.9B", -1.4),
            ],
        ),
    ]

    def list_all(self) -> list[dict]:
        return [
            {
                "name": f.name,
                "manager": f.manager,
                "avatar": f.avatar,
                "aum": f.aum,
                "holdings": [
                    {"ticker": h.ticker, "pct": h.pct, "shares": h.shares, "value": h.value, "change": h.change}
                    for h in f.holdings
                ],
            }
            for f in self._FUNDS
        ]

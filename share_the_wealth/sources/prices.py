"""
Bulk current prices via yfinance.
"""

import yfinance as yf

from share_the_wealth.config import Settings


class PriceService:
    def get_prices(self, symbols: list[str]) -> dict[str, float]:
        if not symbols:
            return {}
        symbols = list(set(s.upper() for s in symbols if s))
        result = {}
        for sym in symbols:
            try:
                t = yf.Ticker(sym)
                info = t.info
                price = info.get("regularMarketPrice") or info.get("previousClose") or info.get("currentPrice")
                if price is not None:
                    result[sym] = float(price)
            except Exception:
                pass
        return result

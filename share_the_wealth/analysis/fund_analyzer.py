"""
Maps politician trades to executable alternatives using user's funds/ETFs.
"""

from typing import Literal

import yfinance as yf
from yahooquery import Ticker

from share_the_wealth.models import PoliticianTrade, MappedTrade


class FundAnalyzer:
    SECTOR_ETFS = {
        "Technology": ["QQQ", "XLK", "VGT", "SMH"],
        "Healthcare": ["XLV", "VHT", "IBB"],
        "Financials": ["XLF", "VFH", "KRE"],
        "Consumer Discretionary": ["XLY", "VCR"],
        "Consumer Staples": ["XLP", "VDC"],
        "Energy": ["XLE", "VDE"],
        "Industrials": ["XLI", "VIS"],
        "Materials": ["XLB", "VAW"],
        "Utilities": ["XLU", "VPU"],
        "Real Estate": ["XLRE", "VNQ"],
    }
    BROAD_ETFS = ["SPY", "QQQ", "VOO", "VTI", "IWM"]

    def _get_stock_sector(self, symbol: str) -> str | None:
        try:
            info = yf.Ticker(symbol).info
            return info.get("sector") or info.get("industry")
        except Exception:
            return None

    def _get_etf_holdings(self, etf_symbol: str) -> dict[str, float]:
        try:
            t = Ticker(etf_symbol)
            info = t.fund_holding_info
            if not info or not isinstance(info, dict):
                return {}
            holdings = info.get(etf_symbol, {})
            if isinstance(holdings, dict):
                positions = holdings.get("holdings", []) or holdings.get("position", [])
            else:
                positions = []
            result = {}
            for p in positions if isinstance(positions, list) else []:
                if isinstance(p, dict):
                    sym = p.get("symbol") or p.get("holdingSymbol")
                    pct = p.get("holdingPercent") or p.get("percent") or p.get("weight")
                    if sym:
                        result[str(sym).upper()] = float(pct or 0)
            return result
        except Exception:
            return {}

    def _etf_holds_stock(self, etf_symbol: str, stock: str) -> bool:
        holdings = self._get_etf_holdings(etf_symbol)
        return stock.upper() in (h.upper() for h in holdings)

    def map_trade_to_funds(
        self,
        trade: PoliticianTrade,
        user_funds: list[str],
        allow_direct_stock: bool = True,
    ) -> list[MappedTrade]:
        symbol = trade.symbol.upper()
        results = []
        sector = self._get_stock_sector(symbol)
        sector_etfs = self.SECTOR_ETFS.get(sector, []) if sector else []

        for fund in user_funds:
            fund_upper = fund.upper()
            if fund_upper == symbol and allow_direct_stock:
                results.append(MappedTrade(
                    original_trade=trade,
                    executable_symbol=fund_upper,
                    executable_type="stock",
                    match_reason="Direct stock match",
                    sector=sector,
                    confidence=1.0,
                ))
                continue
            if self._etf_holds_stock(fund_upper, symbol):
                results.append(MappedTrade(
                    original_trade=trade,
                    executable_symbol=fund_upper,
                    executable_type="etf",
                    match_reason=f"ETF holds {symbol}",
                    sector=sector,
                    confidence=0.95,
                ))

        for etf in sector_etfs + self.BROAD_ETFS:
            if etf in (m.executable_symbol for m in results):
                continue
            if self._etf_holds_stock(etf, symbol):
                results.append(MappedTrade(
                    original_trade=trade,
                    executable_symbol=etf,
                    executable_type="etf",
                    match_reason=f"Sector/broad ETF holds {symbol}",
                    sector=sector,
                    confidence=0.85,
                ))

        if sector and not results:
            for etf in sector_etfs:
                if etf not in user_funds:
                    continue
                results.append(MappedTrade(
                    original_trade=trade,
                    executable_symbol=etf,
                    executable_type="etf",
                    match_reason=f"Sector exposure ({sector})",
                    sector=sector,
                    confidence=0.6,
                ))

        return sorted(results, key=lambda m: -m.confidence)

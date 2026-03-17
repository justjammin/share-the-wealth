"""
Trade-related domain models.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class PoliticianTrade:
    symbol: str
    transaction_type: Literal["Purchase", "Sale", "Exchange"]
    transaction_date: str
    disclosure_date: str
    politician_name: str
    chamber: Literal["Senate", "House"]
    amount_range: str | None
    asset_type: str | None
    owner: str | None
    raw: dict


@dataclass
class MappedTrade:
    original_trade: PoliticianTrade
    executable_symbol: str
    executable_type: Literal["stock", "etf"]
    match_reason: str
    sector: str | None
    confidence: float

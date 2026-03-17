"""
Fund and holding domain models.
"""

from dataclasses import dataclass


@dataclass
class Holding:
    ticker: str
    pct: float
    shares: str
    value: str
    change: float


@dataclass
class HedgeFund:
    name: str
    manager: str
    avatar: str
    aum: str
    holdings: list[Holding]

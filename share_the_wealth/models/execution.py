"""
Execution/order domain models.
"""

from dataclasses import dataclass


@dataclass
class OrderResult:
    success: bool
    order_id: str | None
    message: str
    filled_qty: float | None = None
    filled_avg_price: float | None = None

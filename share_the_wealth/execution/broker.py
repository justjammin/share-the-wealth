"""
Brokerage execution via Alpaca (paper trading by default).
"""

from typing import Literal

from share_the_wealth.config import Settings
from share_the_wealth.models import OrderResult


class Broker:
    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
        paper: bool | None = None,
    ):
        self._api_key = api_key or Settings.ALPACA_API_KEY
        self._secret_key = secret_key or Settings.ALPACA_SECRET_KEY
        self._paper = paper if paper is not None else Settings.ALPACA_PAPER

    def _get_client(self):
        from alpaca.trading.client import TradingClient
        return TradingClient(self._api_key, self._secret_key, paper=self._paper)

    def get_account(self) -> dict | None:
        try:
            client = self._get_client()
            acc = client.get_account()
            return {
                "id": str(acc.id),
                "cash": float(acc.cash),
                "portfolio_value": float(acc.portfolio_value),
                "buying_power": float(acc.buying_power),
            }
        except Exception:
            return None

    def get_positions(self) -> list[dict]:
        try:
            client = self._get_client()
            positions = client.get_all_positions()
            return [
                {
                    "symbol": str(p.symbol),
                    "qty": float(p.qty),
                    "market_value": float(p.market_value),
                    "cost_basis": float(p.cost_basis),
                }
                for p in positions
            ]
        except Exception:
            return []

    def place_market_order(
        self,
        symbol: str,
        qty: float,
        side: Literal["buy", "sell"],
    ) -> OrderResult:
        try:
            from alpaca.trading.enums import OrderSide
            from alpaca.trading.requests import MarketOrderRequest

            client = self._get_client()
            req = MarketOrderRequest(
                symbol=symbol.upper(),
                qty=qty,
                side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
            )
            order = client.submit_order(req)
            return OrderResult(
                success=True,
                order_id=str(order.id),
                message="Order submitted",
                filled_qty=float(order.filled_qty) if order.filled_qty else None,
                filled_avg_price=float(order.filled_avg_price) if order.filled_avg_price else None,
            )
        except Exception as e:
            return OrderResult(success=False, order_id=None, message=str(e))

    def place_order_by_dollars(
        self,
        symbol: str,
        notional: float,
        side: Literal["buy", "sell"] = "buy",
    ) -> OrderResult:
        try:
            from alpaca.trading.enums import OrderSide
            from alpaca.trading.requests import MarketOrderRequest

            client = self._get_client()
            req = MarketOrderRequest(
                symbol=symbol.upper(),
                notional=notional,
                side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
            )
            order = client.submit_order(req)
            return OrderResult(
                success=True,
                order_id=str(order.id),
                message="Order submitted",
                filled_qty=float(order.filled_qty) if order.filled_qty else None,
                filled_avg_price=float(order.filled_avg_price) if order.filled_avg_price else None,
            )
        except Exception as e:
            return OrderResult(success=False, order_id=None, message=str(e))

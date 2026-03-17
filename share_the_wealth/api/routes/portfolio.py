"""
Portfolio routes.
"""

from fastapi import APIRouter

from share_the_wealth.api.deps import mirror_state
from share_the_wealth.api.services import PortfolioService

router = APIRouter(prefix="/api", tags=["portfolio"])
_portfolio_svc = PortfolioService(mirror_state)


@router.get("/portfolio")
def get_portfolio():
    return {"positions": _portfolio_svc.get_positions()}

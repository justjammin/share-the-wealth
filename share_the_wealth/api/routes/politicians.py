"""
Politician and data routes.
"""

from fastapi import APIRouter, HTTPException

from share_the_wealth.api.services import PoliticianService
from share_the_wealth.sources import HedgeFundRepository, PriceService

router = APIRouter(prefix="/api", tags=["data"])
_politician_svc = PoliticianService()
_fund_repo = HedgeFundRepository()
_price_svc = PriceService()


@router.get("/politicians")
def get_politicians():
    try:
        return {"politicians": _politician_svc.get_politicians_with_trades()}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/hedge-funds")
def get_hedge_funds():
    return {"funds": _fund_repo.list_all()}


@router.get("/prices")
def get_prices(symbols: str = ""):
    sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
    return {"prices": _price_svc.get_prices(sym_list)}

"""
Politician and data routes.
"""

from fastapi import APIRouter, HTTPException

from share_the_wealth.api.services import PoliticianService, _politician_cache
from share_the_wealth.api.fmp_budget import fmp_budget
from share_the_wealth.sources import HedgeFundRepository, PriceService

router = APIRouter(prefix="/api", tags=["data"])
_politician_svc = PoliticianService()
_fund_repo = HedgeFundRepository()
_price_svc = PriceService()


@router.get("/politicians")
def get_politicians(fresh: bool = False):
    try:
        return {"politicians": _politician_svc.get_politicians_with_trades(fresh=fresh)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/politicians/refresh")
def refresh_politicians():
    if not fmp_budget.can_fresh():
        raise HTTPException(429, "Fresh pull budget exhausted for today (50 calls reserved)")
    try:
        data = _politician_svc.get_politicians_with_trades(fresh=True)
        sched, fresh = fmp_budget.remaining()
        return {"politicians": data, "remaining": {"scheduled": sched, "fresh": fresh}}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/politicians/budget")
def get_budget():
    sched, fresh = fmp_budget.remaining()
    return {"scheduled": sched, "fresh": fresh}


@router.get("/hedge-funds")
def get_hedge_funds():
    return {"funds": _fund_repo.list_all()}


@router.get("/prices")
def get_prices(symbols: str = ""):
    sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
    return {"prices": _price_svc.get_prices(sym_list)}

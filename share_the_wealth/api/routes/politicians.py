"""
Data routes — hedge funds and prices.
"""

from fastapi import APIRouter

from share_the_wealth.sources import HedgeFundRepository, PriceService

router = APIRouter(prefix="/api", tags=["data"])
_fund_repo = HedgeFundRepository()
_price_svc = PriceService()


@router.get("/hedge-funds")
def get_hedge_funds():
    res = _fund_repo.list_all()
    return {"funds": res["funds"], "using_fallback": res.get("using_fallback", False)}


@router.get("/prices")
def get_prices(symbols: str = ""):
    sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
    return {"prices": _price_svc.get_prices(sym_list)}

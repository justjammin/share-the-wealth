"""
ETL status and manual run (cron / dev).
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["etl"])


@router.get("/etl/status")
def etl_status():
    from share_the_wealth.warehouse.repository import get_etl_status
    return get_etl_status()


@router.post("/etl/run")
def etl_run():
    from share_the_wealth.warehouse.etl import run_etl
    return run_etl()

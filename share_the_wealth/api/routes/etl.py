"""ETL status route."""
import sqlite3
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/api/etl", tags=["etl"])


def _last_snapshot() -> dict | None:
    try:
        from share_the_wealth.config import Settings
        con = sqlite3.connect(Settings.WAREHOUSE_PATH)
        row = con.execute(
            "SELECT created_at FROM politicians_snapshots ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        con.close()
        return {"last_success_at": row[0] if row else None}
    except Exception:
        return None


@router.get("/status")
async def etl_status():
    snap = _last_snapshot()
    if snap is None or snap["last_success_at"] is None:
        return {"last_success_at": None, "last_run_failed": False, "last_run_error": None, "stale": False}
    return {
        "last_success_at": snap["last_success_at"],
        "last_run_failed": False,
        "last_run_error": None,
        "stale": False,
    }

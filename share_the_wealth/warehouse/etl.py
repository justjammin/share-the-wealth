"""
ETL: extract from existing services (live + dummy fallback), load into warehouse.
"""

from __future__ import annotations

import traceback

from share_the_wealth.api.services import PoliticianService
from share_the_wealth.sources import HedgeFundRepository
from share_the_wealth.warehouse.db import ensure_db
from share_the_wealth.warehouse.repository import record_failed_run, replace_snapshot


def _snapshot_politicians() -> tuple[list[dict], bool]:
    svc = PoliticianService()
    data = svc._fetch_politicians_internal()
    from share_the_wealth.api.services import _politician_using_fallback
    return data, _politician_using_fallback


def _snapshot_funds() -> tuple[list[dict], bool]:
    res = HedgeFundRepository().list_all(skip_warehouse=True)
    return res["funds"], res.get("using_fallback", False)


def persist_snapshot(
    politicians: list[dict],
    funds: list[dict],
    politicians_fallback: bool,
    funds_fallback: bool,
) -> dict:
    """Write an already-fetched snapshot to the warehouse (no extra API calls)."""
    conn = ensure_db()
    try:
        run_id = replace_snapshot(conn, politicians, funds, politicians_fallback, funds_fallback)
        return {"ok": True, "run_id": run_id, "politicians_fallback": politicians_fallback, "funds_fallback": funds_fallback}
    except Exception as e:
        try:
            record_failed_run(ensure_db(), f"{e}\n{traceback.format_exc()}")
        except Exception:
            pass
        return {"ok": False, "error": str(e)}


def run_etl() -> dict:
    """
    Fetch politicians + funds (same paths as API, including curated fallback), persist to SQLite.
    On failure, records a failed run row without wiping a prior successful snapshot.
    """
    try:
        politicians, pol_fb = _snapshot_politicians()
        funds, fund_fb = _snapshot_funds()
        run_id = replace_snapshot(ensure_db(), politicians, funds, pol_fb, fund_fb)
        return {"ok": True, "run_id": run_id, "politicians_fallback": pol_fb, "funds_fallback": fund_fb}
    except Exception as e:
        try:
            record_failed_run(ensure_db(), f"{e}\n{traceback.format_exc()}")
        except Exception:
            pass
        return {"ok": False, "error": str(e)}

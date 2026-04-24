"""ETL: fetch funds and persist snapshot to SQLite."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from share_the_wealth.config import Settings


def _db() -> sqlite3.Connection:
    path = Path(Settings.WAREHOUSE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.execute("""
        CREATE TABLE IF NOT EXISTS funds_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            using_fallback INTEGER NOT NULL DEFAULT 0,
            payload TEXT NOT NULL
        )
    """)
    con.commit()
    return con


def run_etl() -> dict:
    from share_the_wealth.sources.hedge_funds import HedgeFundRepository, CURATED_FUNDS

    now = datetime.now(timezone.utc).isoformat()
    result: dict = {"ok": False, "funds": None, "funds_fallback": False, "errors": []}

    fund_payload: list[dict] = []
    fund_fallback = False
    try:
        repo = HedgeFundRepository()
        res = repo.list_all(skip_warehouse=True)
        fund_payload = res.get("funds", [])
        fund_fallback = res.get("using_fallback", False)
        result["funds"] = len(fund_payload)
    except Exception as e:
        result["errors"].append(f"funds: {e}")
        fund_fallback = True
        from dataclasses import asdict
        fund_payload = [
            {"name": f.name, "manager": f.manager, "avatar": f.avatar, "aum": f.aum,
             "holdings": [asdict(h) for h in f.holdings]}
            for f in CURATED_FUNDS
        ]
        result["funds"] = len(fund_payload)

    try:
        con = _db()
        con.execute(
            "INSERT INTO funds_snapshots (created_at, using_fallback, payload) VALUES (?, ?, ?)",
            (now, int(fund_fallback), json.dumps(fund_payload)),
        )
        con.commit()
        con.close()
        result["ok"] = True
        result["funds_fallback"] = fund_fallback
        result["saved_at"] = now
    except Exception as e:
        result["errors"].append(f"db write: {e}")

    return result

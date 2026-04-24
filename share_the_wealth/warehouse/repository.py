"""Read/write fund snapshots from the SQLite warehouse."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from share_the_wealth.config import Settings


def _db() -> sqlite3.Connection:
    path = Path(Settings.WAREHOUSE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(path))


def load_latest_funds() -> tuple[list[dict], bool] | None:
    try:
        con = _db()
        row = con.execute(
            "SELECT payload, using_fallback FROM funds_snapshots ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        con.close()
        if row is None:
            return None
        return json.loads(row[0]), bool(row[1])
    except Exception:
        return None


def persist_funds(funds: list[dict], using_fallback: bool) -> None:
    now = datetime.now(timezone.utc).isoformat()
    try:
        con = _db()
        con.execute("""
            CREATE TABLE IF NOT EXISTS funds_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                using_fallback INTEGER NOT NULL DEFAULT 0,
                payload TEXT NOT NULL
            )
        """)
        con.execute(
            "INSERT INTO funds_snapshots (created_at, using_fallback, payload) VALUES (?, ?, ?)",
            (now, int(using_fallback), json.dumps(funds)),
        )
        con.commit()
        con.close()
    except Exception:
        pass

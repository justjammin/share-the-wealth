"""Read snapshots from the SQLite warehouse."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from share_the_wealth.config import Settings


def _db() -> sqlite3.Connection:
    path = Path(Settings.WAREHOUSE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(path))


def load_latest_politicians() -> tuple[list[dict], bool] | None:
    try:
        con = _db()
        row = con.execute(
            "SELECT payload, using_fallback FROM politicians_snapshots ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        con.close()
        if row is None:
            return None
        return json.loads(row[0]), bool(row[1])
    except Exception:
        return None


def load_latest_funds() -> tuple[list[dict], bool] | None:
    """Returns (list[dict], using_fallback) — dicts have same shape as fetch_all_funds()."""
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


def persist_snapshot(
    politicians: list[dict],
    funds: list[dict],
    pol_fallback: bool,
    fund_fallback: bool,
) -> None:
    """Write a new snapshot row for both politicians and funds."""
    import sqlite3 as _sq
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    try:
        con = _db()
        con.executescript("""
            CREATE TABLE IF NOT EXISTS politicians_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                using_fallback INTEGER NOT NULL DEFAULT 0,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS funds_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                using_fallback INTEGER NOT NULL DEFAULT 0,
                payload TEXT NOT NULL
            );
        """)
        con.execute(
            "INSERT INTO politicians_snapshots (created_at, using_fallback, payload) VALUES (?, ?, ?)",
            (now, int(pol_fallback), json.dumps(politicians)),
        )
        con.execute(
            "INSERT INTO funds_snapshots (created_at, using_fallback, payload) VALUES (?, ?, ?)",
            (now, int(fund_fallback), json.dumps(funds)),
        )
        con.commit()
        con.close()
    except Exception:
        pass

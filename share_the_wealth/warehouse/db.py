"""
SQLite connection and schema for the warehouse.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from share_the_wealth.config import Settings

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS etl_run (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    error_message TEXT,
    politicians_fallback INTEGER NOT NULL DEFAULT 0,
    funds_fallback INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pol_trade (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    politician_name TEXT NOT NULL,
    party TEXT NOT NULL,
    avatar TEXT NOT NULL,
    ticker TEXT NOT NULL,
    action TEXT NOT NULL,
    shares REAL NOT NULL,
    price REAL NOT NULL,
    trade_date TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES etl_run(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS fund_holding (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    fund_name TEXT NOT NULL,
    manager TEXT NOT NULL,
    avatar TEXT NOT NULL,
    aum TEXT NOT NULL,
    ticker TEXT NOT NULL,
    pct REAL NOT NULL,
    shares TEXT NOT NULL,
    value TEXT NOT NULL,
    change REAL NOT NULL,
    FOREIGN KEY (run_id) REFERENCES etl_run(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pol_run ON pol_trade(run_id);
CREATE INDEX IF NOT EXISTS idx_fund_run ON fund_holding(run_id);
"""


def warehouse_path() -> Path:
    p = Settings.WAREHOUSE_PATH
    path = Path(p) if Path(p).is_absolute() else Path(__file__).resolve().parent.parent.parent / p
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def connect() -> sqlite3.Connection:
    path = warehouse_path()
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def ensure_db() -> sqlite3.Connection:
    conn = connect()
    init_schema(conn)
    return conn

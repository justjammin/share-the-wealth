"""
Read/write silver snapshot + ETL status.
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from share_the_wealth.config import Settings
from share_the_wealth.warehouse.db import connect, init_schema, warehouse_path


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_latest_politicians() -> tuple[list[dict[str, Any]], bool] | None:
    """Return API-shaped politicians + using_fallback, or None if no successful snapshot."""
    conn = connect()
    init_schema(conn)
    row = conn.execute(
        "SELECT id, politicians_fallback FROM etl_run WHERE status = 'success' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if not row:
        conn.close()
        return None
    run_id, pol_fb = row["id"], bool(row["politicians_fallback"])
    rows = conn.execute(
        "SELECT politician_name, party, avatar, ticker, action, shares, price, trade_date FROM pol_trade WHERE run_id = ? ORDER BY id",
        (run_id,),
    ).fetchall()
    conn.close()
    if not rows:
        return None
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for r in rows:
        key = (r["politician_name"], r["party"], r["avatar"])
        grouped[key].append({
            "ticker": r["ticker"],
            "action": r["action"],
            "shares": int(r["shares"]) if r["shares"] == int(r["shares"]) else r["shares"],
            "price": float(r["price"]),
            "date": r["trade_date"],
            "value": round(float(r["shares"]) * float(r["price"])),
        })
    politicians = []
    for (name, party, avatar), trades in grouped.items():
        politicians.append({"name": name, "party": party, "avatar": avatar, "trades": trades})
    politicians.sort(key=lambda p: p["name"])
    return politicians, pol_fb


def load_latest_funds() -> tuple[list[dict[str, Any]], bool] | None:
    conn = connect()
    init_schema(conn)
    row = conn.execute(
        "SELECT id, funds_fallback FROM etl_run WHERE status = 'success' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if not row:
        conn.close()
        return None
    run_id, fund_fb = row["id"], bool(row["funds_fallback"])
    rows = conn.execute(
        """SELECT fund_name, manager, avatar, aum, ticker, pct, shares, value, change
           FROM fund_holding WHERE run_id = ? ORDER BY id""",
        (run_id,),
    ).fetchall()
    conn.close()
    if not rows:
        return None
    grouped: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
    for r in rows:
        key = (r["fund_name"], r["manager"], r["avatar"], r["aum"])
        grouped[key].append({
            "ticker": r["ticker"],
            "pct": float(r["pct"]),
            "shares": r["shares"],
            "value": r["value"],
            "change": float(r["change"]),
        })
    funds = []
    for (name, manager, avatar, aum), holdings in grouped.items():
        funds.append({
            "name": name,
            "manager": manager,
            "avatar": avatar,
            "aum": aum,
            "holdings": holdings,
        })
    funds.sort(key=lambda f: f["name"])
    return funds, fund_fb


def get_etl_status() -> dict[str, Any]:
    """For /api/etl/status and UI banner."""
    conn = connect()
    init_schema(conn)
    last = conn.execute(
        "SELECT id, started_at, finished_at, status, error_message FROM etl_run ORDER BY id DESC LIMIT 1"
    ).fetchone()
    last_success = conn.execute(
        "SELECT finished_at FROM etl_run WHERE status = 'success' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    stale_seconds = Settings.ETL_STALE_SECONDS
    now = datetime.now(timezone.utc)
    stale = False
    last_success_at: str | None = None
    if last_success and last_success["finished_at"]:
        last_success_at = last_success["finished_at"]
        dt = _parse_iso(last_success_at)
        if dt:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            stale = (now - dt).total_seconds() > stale_seconds

    out: dict[str, Any] = {
        "warehouse_path": str(warehouse_path()),
        "read_from_warehouse": Settings.READ_FROM_WAREHOUSE,
        "last_success_at": last_success_at,
        "stale": stale,
        "stale_after_seconds": stale_seconds,
    }

    if not last:
        out["last_run_status"] = "none"
        out["last_run_error"] = None
        out["last_run_failed"] = False
        return out

    out["last_run_status"] = last["status"]
    out["last_run_at"] = last["finished_at"] or last["started_at"]
    out["last_run_error"] = last["error_message"]
    out["last_run_failed"] = last["status"] == "failed"
    return out


def purge_failed_runs_old(conn: sqlite3.Connection, days: int = 90) -> None:
    """Drop old failed run rows (audit noise)."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    conn.execute(
        "DELETE FROM etl_run WHERE status = 'failed' AND finished_at IS NOT NULL AND finished_at < ?",
        (cutoff,),
    )


def replace_snapshot(
    conn: sqlite3.Connection,
    politicians: list[dict],
    funds: list[dict],
    politicians_fallback: bool,
    funds_fallback: bool,
) -> int:
    """Atomically replace the successful snapshot. Returns run id."""
    started = _utc_now_iso()
    conn.execute("BEGIN")
    try:
        conn.execute("DELETE FROM pol_trade")
        conn.execute("DELETE FROM fund_holding")
        conn.execute("DELETE FROM etl_run")
        conn.execute(
            """INSERT INTO etl_run (started_at, finished_at, status, error_message, politicians_fallback, funds_fallback)
               VALUES (?, ?, 'success', NULL, ?, ?)""",
            (started, _utc_now_iso(), int(politicians_fallback), int(funds_fallback)),
        )
        run_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
        for p in politicians:
            for t in p.get("trades") or []:
                conn.execute(
                    """INSERT INTO pol_trade (run_id, politician_name, party, avatar, ticker, action, shares, price, trade_date)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        run_id,
                        p["name"],
                        p["party"],
                        p["avatar"],
                        t["ticker"],
                        t["action"],
                        float(t["shares"]),
                        float(t["price"]),
                        str(t.get("date") or "")[:10],
                    ),
                )
        for f in funds:
            for h in f.get("holdings") or []:
                conn.execute(
                    """INSERT INTO fund_holding (run_id, fund_name, manager, avatar, aum, ticker, pct, shares, value, change)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        run_id,
                        f["name"],
                        f["manager"],
                        f["avatar"],
                        f["aum"],
                        h["ticker"],
                        float(h["pct"]),
                        str(h["shares"]),
                        str(h["value"]),
                        float(h["change"]),
                    ),
                )
        purge_failed_runs_old(conn, days=90)
        conn.commit()
        return run_id
    except Exception:
        conn.rollback()
        raise


def record_failed_run(conn: sqlite3.Connection, error: str) -> None:
    started = _utc_now_iso()
    safe_err = (error or "unknown")[:2000]
    conn.execute(
        """INSERT INTO etl_run (started_at, finished_at, status, error_message, politicians_fallback, funds_fallback)
           VALUES (?, ?, 'failed', ?, 0, 0)""",
        (started, _utc_now_iso(), safe_err),
    )
    conn.commit()

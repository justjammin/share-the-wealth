"""ETL: fetch politicians + funds and persist snapshots to SQLite."""
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
    con.commit()
    return con


def run_etl() -> dict:
    from share_the_wealth.sources.trade_fetcher import TradeFetcher
    from share_the_wealth.sources.hedge_funds import HedgeFundRepository, CURATED_FUNDS

    now = datetime.now(timezone.utc).isoformat()
    result: dict = {"ok": False, "politicians": None, "funds": None, "politicians_fallback": False, "funds_fallback": False, "errors": []}

    # ── Politicians ──────────────────────────────────────────────────────────
    pol_payload: list[dict] = []
    pol_fallback = False
    try:
        fetcher = TradeFetcher()
        trades = fetcher.fetch_all(limit_per_chamber=25)
        # Group by politician name into the dict format the API layer expects
        by_pol: dict[str, dict] = {}
        for t in trades:
            name = t.politician_name
            if name not in by_pol:
                party = "R" if t.chamber == "Senate" else "D"  # rough heuristic; real data has party
                by_pol[name] = {
                    "name": name,
                    "party": party,
                    "avatar": name[:3].upper(),
                    "trades": [],
                }
            by_pol[name]["trades"].append({
                "ticker": t.symbol,
                "action": "BUY" if t.transaction_type == "Purchase" else "SELL",
                "shares": 0,
                "price": 0.0,
                "date": t.transaction_date,
            })
        pol_payload = list(by_pol.values())
        result["politicians"] = len(pol_payload)
    except Exception as e:
        result["errors"].append(f"politicians: {e}")
        pol_fallback = True
        pol_payload = []

    # ── Funds ────────────────────────────────────────────────────────────────
    fund_payload: list[dict] = []
    fund_fallback = False
    try:
        repo = HedgeFundRepository()
        res = repo.list_all(skip_warehouse=True)
        funds = res.get("funds", [])
        fund_fallback = res.get("using_fallback", False)
        # funds are already dicts from fetch_all_funds()
        fund_payload = funds if isinstance(funds[0], dict) else [
            {"name": f.name, "manager": f.manager, "avatar": f.avatar, "aum": f.aum,
             "holdings": [h.__dict__ for h in f.holdings]}
            for f in funds
        ] if funds else []
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

    # ── Persist ──────────────────────────────────────────────────────────────
    try:
        con = _db()
        con.execute(
            "INSERT INTO politicians_snapshots (created_at, using_fallback, payload) VALUES (?, ?, ?)",
            (now, int(pol_fallback), json.dumps(pol_payload)),
        )
        con.execute(
            "INSERT INTO funds_snapshots (created_at, using_fallback, payload) VALUES (?, ?, ?)",
            (now, int(fund_fallback), json.dumps(fund_payload)),
        )
        con.commit()
        con.close()
        result["ok"] = True
        result["politicians_fallback"] = pol_fallback
        result["funds_fallback"] = fund_fallback
        result["saved_at"] = now
    except Exception as e:
        result["errors"].append(f"db write: {e}")

    return result

"""
Fetches hedge fund 13F holdings via Forms13F API (free, no auth).
https://forms13f.com / https://forms13f.github.io/api-docs/
"""

import requests
from collections import defaultdict

FORMS13F_BASE = "https://forms13f.com/api/v1"

FUND_CIKS = {
    "Berkshire Hathaway": ("0001067983", "Warren Buffett", "BH", "$900B"),
    "Pershing Square": ("0001336528", "Bill Ackman", "PS", "$16B"),
    "Tiger Global": ("0001167483", "Chase Coleman", "TG", "$22B"),
}


def _fmt_shares(n: float) -> str:
    if n >= 1e9:
        return f"{n/1e9:.1f}B"
    if n >= 1e6:
        return f"{n/1e6:.1f}M"
    if n >= 1e3:
        return f"{n/1e3:.1f}K"
    return str(int(n))


def _fmt_value(n: float) -> str:
    if n >= 1e9:
        return f"${n/1e9:.1f}B"
    if n >= 1e6:
        return f"${n/1e6:.1f}M"
    if n >= 1e3:
        return f"${n/1e3:.1f}K"
    return f"${n:,.0f}"


def fetch_fund_holdings(cik: str, limit: int = 5) -> list[dict] | None:
    """Fetch latest 13F form and return holdings. Value is in thousands."""
    try:
        resp = requests.get(
            f"{FORMS13F_BASE}/forms",
            params={"cik": cik, "from": "2024-01-01", "to": "2026-12-31", "limit": limit},
            timeout=15,
        )
        resp.raise_for_status()
        forms = resp.json()
        if not forms or not isinstance(forms, list):
            return None
        latest = next((f for f in forms if f.get("submission_type") == "13F-HR" and not f.get("is_amendment")), forms[0])
        acc = latest.get("accession_number")
        if not acc:
            return None
        form_resp = requests.get(
            f"{FORMS13F_BASE}/form",
            params={"accession_number": acc, "cik": cik, "limit": 500},
            timeout=30,
        )
        form_resp.raise_for_status()
        rows = form_resp.json()
        if not rows or not isinstance(rows, list):
            return None
        by_ticker: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            ticker = (r.get("ticker") or "").strip().upper()
            if not ticker or r.get("put_call"):
                continue
            by_ticker[ticker].append(r)
        holdings = []
        total_thousands = sum((r.get("value") or 0) for r in rows) or 1
        total_val = total_thousands * 1000
        for ticker, ticker_rows in by_ticker.items():
            val_thousands = sum((r.get("value") or 0) for r in ticker_rows)
            val = val_thousands * 1000
            shares = sum((r.get("ssh_prnamt") or 0) for r in ticker_rows)
            pct = (val_thousands / total_thousands) * 100 if total_thousands else 0
            holdings.append({
                "ticker": ticker,
                "pct": round(pct, 1),
                "shares": _fmt_shares(shares),
                "value": _fmt_value(val),
                "change": 0,
            })
        return sorted(holdings, key=lambda h: -h["pct"])[:10]
    except Exception:
        return None


def fetch_all_funds() -> list[dict]:
    """Fetch holdings for all known funds. Returns empty on failure."""
    result = []
    for name, (cik, manager, avatar, aum) in FUND_CIKS.items():
        holdings = fetch_fund_holdings(cik)
        if holdings:
            result.append({
                "name": name,
                "manager": manager,
                "avatar": avatar,
                "aum": aum,
                "holdings": holdings,
            })
    return result

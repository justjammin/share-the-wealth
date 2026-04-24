"""
Hedge fund 13F holdings — free sources, no paid API required.

Priority per fund:
  1. SEC EDGAR direct (free, official, no auth — data.sec.gov)
  2. Forms13F API (free, no auth — forms13f.com)
  3. Returns None (caller falls back to curated data)

EDGAR path: submissions API → filing index → infotable XML → OpenFIGI CUSIP→ticker
OpenFIGI: free, 25 req/min without key (https://www.openfigi.com)
"""

import re
import xml.etree.ElementTree as ET
from collections import defaultdict

import requests

_HEADERS = {"User-Agent": "share-the-wealth/1.0 research jamin.echols.05@gmail.com"}
_FORMS13F_BASE = "https://forms13f.com/api/v1"
_EDGAR_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
_EDGAR_FILING_BASE = "https://www.sec.gov/Archives/edgar/data"
_OPENFIGI_URL = "https://api.openfigi.com/v3/mapping"

# CIK, manager display name, avatar initials, AUM display
FUND_CIKS: dict[str, tuple[str, str, str, str]] = {
    "Berkshire Hathaway":   ("0001067983", "Warren Buffett",        "BH", "$900B"),
    "Pershing Square":      ("0001336528", "Bill Ackman",           "PS", "$16B"),
    "Tiger Global":         ("0001167483", "Chase Coleman",         "TG", "$22B"),
    "Bridgewater Associates": ("0001350694", "Ray Dalio",           "BW", "$124B"),
    "Appaloosa Management": ("0001418814", "David Tepper",          "AM", "$13B"),
    "Soros Fund Management":("0001029160", "George Soros",          "SF", "$28B"),
    "Third Point LLC":      ("0001040273", "Dan Loeb",              "TP", "$12B"),
    "Coatue Management":    ("0001555280", "Philippe Laffont",      "CM", "$30B"),
}


# ── Formatting helpers ───────────────────────────────────────────────────────

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


# ── OpenFIGI CUSIP → ticker ──────────────────────────────────────────────────

def _cusip_to_tickers(cusips: list[str]) -> dict[str, str]:
    if not cusips:
        return {}
    try:
        payload = [{"idType": "ID_CUSIP", "idValue": c} for c in cusips[:100]]
        r = requests.post(_OPENFIGI_URL, json=payload,
                          headers={"Content-Type": "application/json"}, timeout=15)
        if not r.ok:
            return {}
        mapping: dict[str, str] = {}
        for cusip, result in zip(cusips, r.json()):
            items = result.get("data") or []
            # Prefer US equity, exchCode "US"
            us = [i for i in items if i.get("exchCode") == "US"
                  and i.get("securityType2") == "Common Stock"]
            chosen = (us or items)
            if chosen and chosen[0].get("ticker"):
                mapping[cusip] = chosen[0]["ticker"]
        return mapping
    except Exception:
        return {}


# ── EDGAR 13F XML parser ─────────────────────────────────────────────────────

def _parse_13f_xml(xml_text: str, limit: int) -> list[dict] | None:
    # Strip namespace so findall works without prefix juggling
    clean = re.sub(r'\s+xmlns[^>]*', '', xml_text, count=5)
    try:
        root = ET.fromstring(clean)
    except ET.ParseError:
        return None

    by_cusip: dict[str, dict] = {}
    for info in root.iter("infoTable"):
        cusip = (info.findtext("cusip") or "").strip()
        if not cusip:
            continue
        if info.findtext("putCall"):  # skip options
            continue
        try:
            val = float(info.findtext("value") or "0")
        except ValueError:
            val = 0
        sh_node = info.find("shrsOrPrnAmt")
        shares = 0.0
        if sh_node is not None:
            try:
                shares = float(sh_node.findtext("sshPrnamt") or "0")
            except ValueError:
                pass
        if cusip in by_cusip:
            by_cusip[cusip]["value"] += val
            by_cusip[cusip]["shares"] += shares
        else:
            by_cusip[cusip] = {"value": val, "shares": shares}

    if not by_cusip:
        return None

    total_val = sum(h["value"] for h in by_cusip.values()) or 1

    # Scale detection: EDGAR spec says thousands, but many filers use actual dollars.
    # If total implies an absurd portfolio (>$50T when treated as thousands), it's dollars.
    if total_val * 1000 > 50e12:
        scale = 1       # values are already in dollars
    else:
        scale = 1000    # values are in thousands → multiply

    sorted_cusips = sorted(by_cusip, key=lambda c: -by_cusip[c]["value"])
    top_cusips = sorted_cusips[: limit * 3]  # fetch extra to account for lookup failures
    tickers = _cusip_to_tickers(top_cusips)

    result: list[dict] = []
    for cusip in top_cusips:
        ticker = tickers.get(cusip)
        if not ticker:
            continue
        h = by_cusip[cusip]
        dollar_val = h["value"] * scale
        pct = (h["value"] / total_val) * 100
        result.append({
            "ticker": ticker,
            "pct": round(pct, 1),
            "shares": _fmt_shares(h["shares"]),
            "value": _fmt_value(dollar_val),
            "change": 0,
        })
        if len(result) >= limit:
            break

    return result or None


# ── EDGAR fetcher ────────────────────────────────────────────────────────────

def _edgar_fetch(cik: str, limit: int = 10) -> list[dict] | None:
    cik_num = cik.lstrip("0")
    cik_padded = cik_num.zfill(10)

    # 1. Get latest 13F-HR accession number
    try:
        sub = requests.get(
            _EDGAR_SUBMISSIONS.format(cik=cik_padded),
            headers=_HEADERS, timeout=15,
        ).json()
    except Exception:
        return None

    recent = sub.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accessions = recent.get("accessionNumber", [])
    acc = next((a for f, a in zip(forms, accessions) if f == "13F-HR"), None)
    if not acc:
        return None

    acc_clean = acc.replace("-", "")

    # 2. Scan the filing index for XML files (infotable is a non-primary XML)
    try:
        idx_html = requests.get(
            f"{_EDGAR_FILING_BASE}/{cik_num}/{acc_clean}/",
            headers=_HEADERS, timeout=15,
        ).text
    except Exception:
        return None

    xml_files = re.findall(r'href="(/Archives/edgar/data/[^"]+\.xml)"', idx_html)
    if not xml_files:
        return None

    # primary_doc.xml is the cover; infotable is everything else
    infotable_path = next(
        (p for p in xml_files if "primary_doc" not in p.lower()),
        xml_files[-1],
    )

    # 3. Fetch and parse infotable XML
    try:
        xml_text = requests.get(
            f"https://www.sec.gov{infotable_path}",
            headers=_HEADERS, timeout=30,
        ).text
    except Exception:
        return None

    return _parse_13f_xml(xml_text, limit)


# ── Forms13F fallback ────────────────────────────────────────────────────────

def _forms13f_fetch(cik: str, limit: int = 10) -> list[dict] | None:
    try:
        resp = requests.get(
            f"{_FORMS13F_BASE}/forms",
            params={"cik": cik, "from": "2024-01-01", "to": "2026-12-31", "limit": 5},
            timeout=15,
        )
        resp.raise_for_status()
        forms = resp.json()
        if not forms or not isinstance(forms, list):
            return None
        latest = next(
            (f for f in forms if f.get("submission_type") == "13F-HR" and not f.get("is_amendment")),
            forms[0],
        )
        acc = latest.get("accession_number")
        if not acc:
            return None
        rows_resp = requests.get(
            f"{_FORMS13F_BASE}/form",
            params={"accession_number": acc, "cik": cik, "limit": 500},
            timeout=30,
        )
        rows_resp.raise_for_status()
        rows = rows_resp.json()
        if not rows or not isinstance(rows, list):
            return None

        by_ticker: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            ticker = (r.get("ticker") or "").strip().upper()
            if not ticker or r.get("put_call"):
                continue
            by_ticker[ticker].append(r)

        total_thousands = sum(r.get("value") or 0 for r in rows) or 1
        holdings = []
        for ticker, ticker_rows in by_ticker.items():
            val_k = sum(r.get("value") or 0 for r in ticker_rows)
            shares = sum(r.get("ssh_prnamt") or 0 for r in ticker_rows)
            pct = (val_k / total_thousands) * 100
            holdings.append({
                "ticker": ticker,
                "pct": round(pct, 1),
                "shares": _fmt_shares(shares),
                "value": _fmt_value(val_k * 1000),
                "change": 0,
            })
        return sorted(holdings, key=lambda h: -h["pct"])[:limit] or None
    except Exception:
        return None


# ── Public interface ─────────────────────────────────────────────────────────

def fetch_fund_holdings(cik: str, limit: int = 10) -> list[dict] | None:
    return _edgar_fetch(cik, limit) or _forms13f_fetch(cik, limit)


def fetch_all_funds() -> list[dict]:
    result = []
    for name, (cik, manager, avatar, aum) in FUND_CIKS.items():
        holdings = fetch_fund_holdings(cik)
        if holdings:
            result.append({"name": name, "manager": manager,
                           "avatar": avatar, "aum": aum, "holdings": holdings})
    return result

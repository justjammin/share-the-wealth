"""
Fetches politician (Congress) stock trades via Financial Modeling Prep API.
"""

import requests

from share_the_wealth.config import Settings
from share_the_wealth.models import PoliticianTrade


class TradeFetcher:
    BASE_URL = "https://financialmodelingprep.com/stable"

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or Settings.FMP_API_KEY

    def _fetch(self, endpoint: str, params: dict | None = None) -> list[dict]:
        params = dict(params or {})
        params["apikey"] = self._api_key
        resp = requests.get(f"{self.BASE_URL}/{endpoint}", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and "error" in data:
            raise ValueError(data.get("message", str(data)))
        return data if isinstance(data, list) else []

    def _normalize_trade(self, raw: dict, chamber: str) -> PoliticianTrade | None:
        symbol = raw.get("ticker") or raw.get("symbol") or raw.get("asset")
        if not symbol or not isinstance(symbol, str):
            return None
        symbol = str(symbol).strip().upper()
        tx_type = raw.get("transactionType") or raw.get("type") or raw.get("transaction_type", "")
        if isinstance(tx_type, str):
            tx_type = tx_type.strip()
            if "purchase" in tx_type.lower() or tx_type == "Buy":
                tx_type = "Purchase"
            elif "sale" in tx_type.lower() or tx_type == "Sell":
                tx_type = "Sale"
            else:
                tx_type = tx_type or "Purchase"
        first = raw.get("firstName", "")
        last = raw.get("lastName", "")
        politician_name = (
            raw.get("politician")
            or raw.get("representative")
            or raw.get("senator")
            or (f"{first} {last}".strip() if (first or last) else "")
        )
        return PoliticianTrade(
            symbol=symbol,
            transaction_type=tx_type,
            transaction_date=str(raw.get("transactionDate", raw.get("transaction_date", ""))),
            disclosure_date=str(raw.get("disclosureDate", raw.get("disclosure_date", ""))),
            politician_name=str(politician_name or "Unknown"),
            chamber=chamber,
            amount_range=raw.get("amount") or raw.get("amountRange"),
            asset_type=raw.get("assetType") or raw.get("asset_type"),
            owner=raw.get("owner"),
            raw=raw,
        )

    def fetch_senate(self, limit: int = 100, page: int = 0) -> list[PoliticianTrade]:
        data = self._fetch("senate-latest", {"limit": limit, "page": page})
        return [t for r in data if (t := self._normalize_trade(r, "Senate"))]

    def fetch_house(self, limit: int = 100, page: int = 0) -> list[PoliticianTrade]:
        data = self._fetch("house-latest", {"limit": limit, "page": page})
        return [t for r in data if (t := self._normalize_trade(r, "House"))]

    def fetch_all(self, limit_per_chamber: int = 50) -> list[PoliticianTrade]:
        senate = self.fetch_senate(limit=limit_per_chamber)
        house = self.fetch_house(limit=limit_per_chamber)
        return senate + house

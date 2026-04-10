"""
Application settings loaded from environment.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")


def _int_env(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


class Settings:
    FMP_API_KEY: str = os.getenv("FMP_API_KEY", "")
    FMP_SCHEDULED_BUDGET: int = int(os.getenv("FMP_SCHEDULED_BUDGET", "200"))
    FMP_FRESH_BUDGET: int = int(os.getenv("FMP_FRESH_BUDGET", "50"))
    ALPACA_API_KEY: str = os.getenv("ALPACA_API_KEY", "")
    ALPACA_SECRET_KEY: str = os.getenv("ALPACA_SECRET_KEY", "")
    ALPACA_PAPER: bool = os.getenv("ALPACA_PAPER", "true").lower() in ("true", "1", "yes")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    # Local RAG (sentence-transformers; no embedding API cost)
    USE_LOCAL_RAG: bool = os.getenv("USE_LOCAL_RAG", "true").lower() in ("true", "1", "yes")
    ST_EMBEDDING_MODEL: str = os.getenv("ST_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    RAG_TOP_K: int = _int_env("RAG_TOP_K", 6)
    # Silver warehouse (SQLite)
    WAREHOUSE_PATH: str = os.getenv("WAREHOUSE_PATH", "data/warehouse.db")
    READ_FROM_WAREHOUSE: bool = os.getenv("READ_FROM_WAREHOUSE", "true").lower() in ("true", "1", "yes")
    ETL_STALE_SECONDS: int = _int_env("ETL_STALE_SECONDS", 7200)

"""
Application settings loaded from environment.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")


class Settings:
    FMP_API_KEY: str = os.getenv("FMP_API_KEY", "")
    FMP_SCHEDULED_BUDGET: int = int(os.getenv("FMP_SCHEDULED_BUDGET", "200"))
    FMP_FRESH_BUDGET: int = int(os.getenv("FMP_FRESH_BUDGET", "50"))
    ALPACA_API_KEY: str = os.getenv("ALPACA_API_KEY", "")
    ALPACA_SECRET_KEY: str = os.getenv("ALPACA_SECRET_KEY", "")
    ALPACA_PAPER: bool = os.getenv("ALPACA_PAPER", "true").lower() in ("true", "1", "yes")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

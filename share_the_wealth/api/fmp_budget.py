"""
FMP API call budget: 200 for scheduled syncs, 50 for fresh pulls per day.
Each full politician fetch = 2 calls (senate + house).
"""

import threading
from datetime import date
from typing import Callable

from share_the_wealth.config import Settings

FMP_CALLS_PER_FETCH = 2
SCHEDULED_BUDGET = Settings.FMP_SCHEDULED_BUDGET
FRESH_BUDGET = Settings.FMP_FRESH_BUDGET


class FMPBudget:
    def __init__(self):
        self._lock = threading.Lock()
        self._scheduled_used = 0
        self._fresh_used = 0
        self._last_reset = date.today()

    def _maybe_reset(self) -> None:
        today = date.today()
        if today > self._last_reset:
            self._scheduled_used = 0
            self._fresh_used = 0
            self._last_reset = today

    def can_fresh(self) -> bool:
        with self._lock:
            self._maybe_reset()
            return self._fresh_used + FMP_CALLS_PER_FETCH <= FRESH_BUDGET

    def can_scheduled(self) -> bool:
        with self._lock:
            self._maybe_reset()
            return self._scheduled_used + FMP_CALLS_PER_FETCH <= SCHEDULED_BUDGET

    def consume_fresh(self) -> bool:
        with self._lock:
            self._maybe_reset()
            if self._fresh_used + FMP_CALLS_PER_FETCH <= FRESH_BUDGET:
                self._fresh_used += FMP_CALLS_PER_FETCH
                return True
            return False

    def consume_scheduled(self) -> bool:
        with self._lock:
            self._maybe_reset()
            if self._scheduled_used + FMP_CALLS_PER_FETCH <= SCHEDULED_BUDGET:
                self._scheduled_used += FMP_CALLS_PER_FETCH
                return True
            return False

    def remaining(self) -> tuple[int, int]:
        with self._lock:
            self._maybe_reset()
            return (
                max(0, SCHEDULED_BUDGET - self._scheduled_used),
                max(0, FRESH_BUDGET - self._fresh_used),
            )


fmp_budget = FMPBudget()


class FMPCache:
    def __init__(self, fetcher: Callable[[], list]):
        self._fetcher = fetcher
        self._data: list | None = None
        self._lock = threading.Lock()

    def get(self, fresh: bool = False) -> list:
        with self._lock:
            if fresh:
                if fmp_budget.consume_fresh():
                    self._data = self._fetcher()
                return self._data or []
            if self._data is not None:
                return self._data
            if fmp_budget.consume_scheduled():
                self._data = self._fetcher()
            elif fmp_budget.consume_fresh():
                self._data = self._fetcher()
            return self._data or []

    def refresh_scheduled(self) -> bool:
        with self._lock:
            if fmp_budget.consume_scheduled():
                self._data = self._fetcher()
                return True
            return False

    def invalidate(self) -> None:
        with self._lock:
            self._data = None

"""
FastAPI application factory.
"""

import threading
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from share_the_wealth.api.routes import politicians, mirror, portfolio, ai
from share_the_wealth.api.deps import mirror_state
from share_the_wealth.api.services import _politician_cache

PROJECT_ROOT = Path(__file__).parent.parent.parent
STATIC_DIR = PROJECT_ROOT / "static"

SCHEDULED_INTERVAL_SEC = 14 * 60


def _scheduled_sync_loop() -> None:
    while True:
        time.sleep(SCHEDULED_INTERVAL_SEC)
        try:
            _politician_cache.refresh_scheduled()
        except Exception:
            pass


def create_app() -> FastAPI:
    app = FastAPI(title="Share the Wealth")

    app.include_router(politicians.router)
    app.include_router(mirror.router)
    app.include_router(portfolio.router)
    app.include_router(ai.router)

    @app.on_event("startup")
    def startup():
        mirror_state.load()
        try:
            _politician_cache.refresh_scheduled()
        except Exception:
            pass
        t = threading.Thread(target=_scheduled_sync_loop, daemon=True)
        t.start()

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    def index():
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(
                index_file,
                headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
            )
        return {"message": "Share the Wealth API", "docs": "/docs"}

    return app

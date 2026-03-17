"""
FastAPI application factory.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from share_the_wealth.api.routes import politicians, mirror, portfolio, ai
from share_the_wealth.api.deps import mirror_state

PROJECT_ROOT = Path(__file__).parent.parent.parent
STATIC_DIR = PROJECT_ROOT / "static"


def create_app() -> FastAPI:
    app = FastAPI(title="Share the Wealth")

    app.include_router(politicians.router)
    app.include_router(mirror.router)
    app.include_router(portfolio.router)
    app.include_router(ai.router)

    @app.on_event("startup")
    def startup():
        mirror_state.load()

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    def index():
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Share the Wealth API", "docs": "/docs"}

    return app

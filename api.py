#!/usr/bin/env python3
"""
Entry point for Share the Wealth API server.
"""

import uvicorn

from share_the_wealth.api import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

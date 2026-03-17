#!/usr/bin/env sh
# Share the Wealth - one-time setup
set -e
python3 -m venv venv
./venv/bin/pip install -e .
test -f .env || cp .env.example .env
echo ""
echo "Done. Next steps:"
echo "  1. source venv/bin/activate"
echo "  2. Edit .env with your API keys"
echo "  3. stw track   # or: make track / just track"

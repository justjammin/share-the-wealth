#!/usr/bin/env sh
# Share the Wealth - one-time setup
set -e
python3 -m venv venv
./venv/bin/pip install -e .
test -f .env || cp .env.example .env
echo ""
echo "Done. Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. make track   # or: ./bin/stw track | just track"
echo ""
echo "  (Or: source venv/bin/activate  then  stw track)"

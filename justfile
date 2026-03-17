# Share the Wealth - run: just <command>
# Install just: brew install just  (or cargo install just)

# Use venv stw if available (backtick captures output)
stw := `[ -f venv/bin/stw ] && echo './venv/bin/stw' || echo 'stw'`

# Default recipe - show help
default:
    @just help

# Show help and available commands
help:
    @echo "Share the Wealth - commands:"
    @echo ""
    @echo "  just setup         Create venv, install deps, copy .env.example"
    @echo "  just install       Install package (enables 'stw' command)"
    @echo "  just track        Show recent politician trades"
    @echo "  just map          Map trades to your funds"
    @echo "  just execute      Preview orders (dry-run)"
    @echo "  just execute-live Execute orders (live)"
    @echo "  just server       Start web UI on http://localhost:8007"
    @echo "  just help         Show this help"
    @echo ""
    @echo "Or: stw track | stw map | stw execute | stw run | stw help"

# Create venv, install deps, copy .env.example
setup:
    ./setup.sh

# Install package (enables 'stw' command)
install:
    pip install -e .

# Show recent politician trades
track limit="25":
    {{stw}} track -n {{limit}}

# Map trades to your funds
map limit="25":
    {{stw}} map -n {{limit}}

# Preview orders (dry-run)
execute size="100":
    {{stw}} execute --dry-run -s {{size}}

# Execute orders (live)
execute-live size="100":
    {{stw}} execute -s {{size}}

# Start web UI
server:
    {{stw}} run

# Dev server with auto-reload on file changes
dev:
    {{stw}} run --reload

# Share the Wealth - run: just <command>
# Install just: brew install just  (or cargo install just)

# Use venv stw if available (backtick captures output)
stw := `[ -f venv/bin/stw ] && echo './venv/bin/stw' || echo 'stw'`

# Default recipe
default:
    @just --list

# Create venv, install deps, copy .env.example
setup:
    ./setup.sh

# Install package (enables 'stw' command)
install:
    pip install -e .

# Show recent politician trades
track limit="50":
    {{stw}} track -n {{limit}}

# Map trades to your funds
map limit="50":
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

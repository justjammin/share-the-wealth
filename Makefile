.PHONY: setup install track map execute execute-live server help

STW = $(if $(wildcard venv/bin/stw),./venv/bin/stw,stw)

# Default target
help:
	@echo "Share the Wealth - commands:"
	@echo "  make setup        # Create venv, install deps, copy .env.example"
	@echo "  make install      # Install package (enables 'stw' command)"
	@echo "  make track       # Show recent politician trades"
	@echo "  make map         # Map trades to your funds"
	@echo "  make execute     # Preview orders (dry-run)"
	@echo "  make execute-live # Execute orders (live)"
	@echo "  make server      # Start web UI on http://localhost:8000"
	@echo ""
	@echo "Or: stw track | stw map | stw execute | stw run"

setup:
	@./setup.sh

install:
	pip install -e .

track:
	$(STW) track

map:
	$(STW) map

execute:
	$(STW) execute --dry-run

execute-live:
	$(STW) execute

server:
	$(STW) run

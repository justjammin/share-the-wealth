.PHONY: setup install track map execute execute-live server help

STW = $(if $(wildcard venv/bin/stw),./venv/bin/stw,stw)

# Default target
help:
	@echo "Share the Wealth - commands:"
	@echo ""
	@echo "  make setup         Create venv, install deps, copy .env.example"
	@echo "  make install      Install package (enables 'stw' command)"
	@echo "  make track        Show recent politician trades"
	@echo "  make map          Map trades to your funds"
	@echo "  make execute      Preview orders (dry-run)"
	@echo "  make execute-live Execute orders (live)"
	@echo "  make server       Start web UI on http://localhost:8007"
	@echo "  make dev          Start with auto-reload (for development)"
	@echo "  make help         Show this help"
	@echo ""
	@echo "Or: stw track | stw map | stw execute | stw run | stw help"

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

# Dev server with auto-reload on file changes
dev:
	$(STW) run --reload

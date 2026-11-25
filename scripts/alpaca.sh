#!/usr/bin/env bash
# Thin wrapper so the agent always calls: bash scripts/alpaca.sh <command> [args]
exec python3 "$(dirname "$0")/alpaca.py" "$@"

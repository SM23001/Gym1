#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "[ERROR] Virtual environment not found."
    echo "Run: python -m venv .venv  and  pip install -r requirements.txt"
    exit 1
fi

python cli.py

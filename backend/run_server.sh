#!/usr/bin/env bash
set -e

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)

# Prefer local virtual environments when available.
if [ -x "$ROOT_DIR/backend/.venv/Scripts/python.exe" ]; then
	"$ROOT_DIR/backend/.venv/Scripts/python.exe" "$ROOT_DIR/backend/chad_rag_backend.py"
elif [ -x "$ROOT_DIR/backend/.venv/bin/python" ]; then
	"$ROOT_DIR/backend/.venv/bin/python" "$ROOT_DIR/backend/chad_rag_backend.py"
elif [ -x "$HOME/chadgpt-venv/bin/python" ]; then
	"$HOME/chadgpt-venv/bin/python" "$ROOT_DIR/backend/chad_rag_backend.py"
elif command -v python3 >/dev/null 2>&1; then
	python3 "$ROOT_DIR/backend/chad_rag_backend.py"
elif command -v py >/dev/null 2>&1; then
	py -3 "$ROOT_DIR/backend/chad_rag_backend.py"
elif command -v python >/dev/null 2>&1; then
	python "$ROOT_DIR/backend/chad_rag_backend.py"
else
	echo "Python not found. Install Python 3 and backend requirements." >&2
	exit 1
fi

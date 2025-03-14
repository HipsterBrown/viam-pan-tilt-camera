#!/usr/bin/env bash

cd "$(dirname "$0")" || exit

export PATH="$PATH:$HOME/.local/bin"
VENV_NAME=".venv-build"

source "./$VENV_NAME/bin/activate"

if ! uv pip install pyinstaller -q; then
  exit 1
fi

uv run pyinstaller --onefile -p src src/main.py
tar -czvf dist/archive.tar.gz ./dist/main meta.json

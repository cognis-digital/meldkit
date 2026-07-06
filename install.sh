#!/usr/bin/env sh
# Cross-platform (macOS / Linux) installer for Confluex (cognis-vanguard).
# Idempotent: safe to re-run. Creates a local .venv and installs the CLI.
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

# 1. Pick a Python interpreter (prefer python3, fall back to python).
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "ERROR: Python 3.9+ is required but neither 'python3' nor 'python' was found on PATH." >&2
  echo "Install Python from https://www.python.org/downloads/ and re-run ./install.sh" >&2
  exit 1
fi

echo ">> Using interpreter: $($PY --version 2>&1) ($PY)"

# 2. Create the virtual environment if it does not already exist.
if [ ! -d ".venv" ]; then
  echo ">> Creating virtual environment at .venv"
  "$PY" -m venv .venv
else
  echo ">> Reusing existing virtual environment at .venv"
fi

VENV_PY="$HERE/.venv/bin/python"

# 3. Upgrade pip tooling.
echo ">> Upgrading pip"
"$VENV_PY" -m pip install --upgrade pip >/dev/null

# 4. Install runtime deps from requirements*.txt if any exist (repo currently
#    ships zero third-party deps, but this keeps the script future-proof).
for req in requirements.txt requirements-dev.txt; do
  if [ -f "$req" ]; then
    echo ">> Installing from $req"
    "$VENV_PY" -m pip install -r "$req"
  fi
done

# 5. Editable install. Include the 'dev' extra only if it is declared.
if grep -Eq '^\s*(dev|test)\s*=' pyproject.toml 2>/dev/null || \
   grep -Eq '\[project\.optional-dependencies\]' pyproject.toml 2>/dev/null; then
  echo ">> Installing package (editable) with dev extra"
  "$VENV_PY" -m pip install -e ".[dev]" || "$VENV_PY" -m pip install -e .
else
  echo ">> Installing package (editable)"
  "$VENV_PY" -m pip install -e .
fi

# 6. Verify the console script is callable.
echo ">> Verifying installation: confluex --help"
"$HERE/.venv/bin/confluex" --help >/dev/null
echo ">> OK: 'confluex' console script is installed and runnable."

# 7. Next steps.
cat <<EOF

============================================================
 Confluex (cognis-vanguard) is installed.
============================================================
 Activate the virtual environment:
   bash / zsh :   source .venv/bin/activate
   fish       :   source .venv/bin/activate.fish
   csh / tcsh :   source .venv/bin/activate.csh

 Then run the CLI:
   confluex --help
   confluex demo                 # end-to-end demo on bundled reporting
   confluex demo-fusion          # full multi-INT fusion / COP demo

 Or without activating:
   .venv/bin/confluex demo
============================================================
EOF

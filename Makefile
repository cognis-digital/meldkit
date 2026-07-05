# Obsidia (cognis-vanguard) developer tasks.
# Uses a local .venv created by ./install.sh (POSIX) so targets are self-contained.

VENV := .venv
PY   := $(VENV)/bin/python
PIP  := $(PY) -m pip
BIN  := $(VENV)/bin/obsidia

.PHONY: install test demo lint clean

## Create venv and install the package (editable).
install:
	@sh ./install.sh

## Run the test suite.
test:
	$(PY) -m pytest -q

## Run a real, representative CLI demo (falls back to --help if unavailable).
demo:
	@$(BIN) demo-fusion || $(BIN) --help

## Lint: ruff if available, otherwise a stdlib byte-compile check.
lint:
	@if $(PY) -c "import ruff" >/dev/null 2>&1; then \
		$(PY) -m ruff check obsidia tests bench examples ; \
	else \
		echo "ruff not installed; running python -m compileall as a fallback" ; \
		$(PY) -m compileall obsidia bench examples ; \
	fi

## Remove build artefacts, caches, and the virtual environment.
clean:
	rm -rf $(VENV) build dist *.egg-info .pytest_cache .cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.py[cod]' -delete

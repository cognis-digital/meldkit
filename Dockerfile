# Obsidia (cognis-vanguard) — thin CLI container.
# Pure-Python stdlib tool: no build deps, no third-party wheels required.
# NOTE: the optional local-model backend (Ollama) is intentionally NOT bundled;
# this image is a portable wrapper around the offline-by-default CLI.
FROM python:3.12-slim

LABEL org.opencontainers.image.title="Obsidia (cognis-vanguard)" \
      org.opencontainers.image.description="Self-hosted, edge-capable multi-INT fusion & agent orchestration CLI" \
      org.opencontainers.image.source="https://github.com/cognis-digital/cognis-vanguard" \
      org.opencontainers.image.licenses="COCL-1.0" \
      org.opencontainers.image.vendor="Cognis Digital LLC"

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir .

ENTRYPOINT ["obsidia"]
CMD ["--help"]

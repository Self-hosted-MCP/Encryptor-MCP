# encryptor-mcp as a web server (serve mode): the control center and AI apps over HTTPS. Works on amd64 and arm64.
FROM python:3.14-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.11.19 /uv /bin/uv

WORKDIR /app

# dependencies first, so code changes rebuild fast
COPY pyproject.toml uv.lock README.md LICENSE NOTICE ./
RUN uv sync --frozen --no-install-project --no-dev

COPY src ./src
RUN uv sync --frozen --no-dev

# /data keeps what must survive a restart: page settings, connected apps, remembered sign-ins, logs, fingerprints.
# Vaults are folders: mount them under /vaults (a synced folder, or an rclone mount; see docker-compose.yml).
# Keys only ever live in memory: a restart locks every vault.
ENV HOST=0.0.0.0 \
    PORT=8767 \
    ENCRYPTOR_CONFIG_DIR=/data \
    ENCRYPTOR_FINDER=off \
    PATH="/app/.venv/bin:$PATH"
EXPOSE 8767

RUN useradd --create-home --uid 10001 encryptor && mkdir -p /data /vaults && chown encryptor /data
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
# The entrypoint drops to the user "encryptor" (uid 10001) at once: see docker-entrypoint.sh.
ENTRYPOINT ["docker-entrypoint.sh"]

HEALTHCHECK --interval=60s --timeout=5s CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\", \"8767\")}/health')"

CMD ["encryptor-mcp", "serve"]

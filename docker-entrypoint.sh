#!/bin/sh
# Starts encryptor-mcp as the unprivileged user "encryptor" (uid 10001).
# Hosting companies (Railway, Render) mount their disk at /data owned by root, and start the container as root:
# then this makes /data belong to that user first, and drops root before anything else runs.
set -eu
if [ "$(id -u)" = "0" ]; then
  mkdir -p /data/vaults
  [ "$(stat -c %u /data)" = "10001" ] && [ "$(stat -c %u /data/vaults)" = "10001" ] || chown -R 10001:10001 /data
  exec setpriv --reuid=10001 --regid=10001 --init-groups "$@"
fi
exec "$@"

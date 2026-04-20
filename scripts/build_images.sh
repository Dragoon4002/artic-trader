#!/usr/bin/env bash
# Build artic-agent + artic-user-server images and save as tarballs
# into hub/docker/images/ for serving via /internal/v1/images/*.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

RELEASE_TAG="${RELEASE_TAG:-v0}"
OUT_DIR="hub/docker/images"
mkdir -p "$OUT_DIR"

echo "=== build artic-agent:${RELEASE_TAG} ==="
docker build -t "artic-agent:${RELEASE_TAG}" hub/docker/agent/

echo "=== build artic-user-server:${RELEASE_TAG} ==="
docker build -t "artic-user-server:${RELEASE_TAG}" -f user-server/Dockerfile .

echo "=== save tarballs ==="
docker save "artic-agent:${RELEASE_TAG}" | gzip > "${OUT_DIR}/artic-agent-${RELEASE_TAG}.tar.gz"
docker save "artic-user-server:${RELEASE_TAG}" | gzip > "${OUT_DIR}/artic-user-server-${RELEASE_TAG}.tar.gz"

echo "=== done ==="
ls -lh "${OUT_DIR}"/*.tar.gz

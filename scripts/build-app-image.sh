#!/bin/bash
# Build the artic-app Docker image from repo root
# Hub's docker/manager.py expects image name: artic-app:latest

set -e
cd "$(dirname "$0")/.."

echo "Building artic-app:latest..."
docker build -f app/Dockerfile -t artic-app:latest .
echo "Done. Image: artic-app:latest"

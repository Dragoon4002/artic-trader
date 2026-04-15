#!/bin/bash
# Create artic-net bridge network if it doesn't exist
docker network inspect artic-net >/dev/null 2>&1 || \
  docker network create artic-net
echo "artic-net ready"

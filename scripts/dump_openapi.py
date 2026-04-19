"""Dump hub FastAPI OpenAPI schema to stdout as YAML."""
from __future__ import annotations

import sys

import yaml

from hub.server import app


def main() -> None:
    yaml.safe_dump(app.openapi(), sys.stdout, sort_keys=False)


if __name__ == "__main__":
    main()

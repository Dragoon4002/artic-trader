"""Auth-protected tarball server for baseline Docker images.

The golden snapshot build pulls `artic-agent` and `artic-user-server` from here
via `curl | docker load`. Keeps images off public registries while still letting
Morph VM fetch them during snapshot build.

Tarballs are produced by `scripts/build_images.sh`:

    docker build -t artic-agent:v0 hub/docker/agent/
    docker save artic-agent:v0 | gzip > hub/docker/images/artic-agent-v0.tar.gz

Guard: X-Hub-Secret header must match settings.INTERNAL_SECRET.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import FileResponse

from ..config import settings

router = APIRouter(prefix="/internal/v1/images", tags=["internal-images"])

_IMAGE_DIR = Path(__file__).resolve().parents[1] / "docker" / "images"

# Whitelist. Only these filenames are served — no traversal.
_ALLOWED = {
    "artic-agent-v0.tar.gz",
    "artic-user-server-v0.tar.gz",
}


def _require_hub_secret(x_hub_secret: str | None) -> None:
    if not settings.INTERNAL_SECRET:
        raise HTTPException(status_code=503, detail="hub secret unset")
    if x_hub_secret != settings.INTERNAL_SECRET:
        raise HTTPException(status_code=401, detail="bad X-Hub-Secret")


@router.get("/{name}")
def get_image(name: str, x_hub_secret: str | None = Header(default=None)) -> FileResponse:
    _require_hub_secret(x_hub_secret)
    if name not in _ALLOWED:
        raise HTTPException(status_code=404, detail="image not in whitelist")
    path = _IMAGE_DIR / name
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"{name} not built (run scripts/build_images.sh)",
        )
    return FileResponse(
        path,
        media_type="application/gzip",
        filename=name,
    )


@router.get("")
def list_images(x_hub_secret: str | None = Header(default=None)) -> dict:
    _require_hub_secret(x_hub_secret)
    present = []
    for name in _ALLOWED:
        path = _IMAGE_DIR / name
        if path.is_file():
            present.append({"name": name, "size": path.stat().st_size})
    return {"available": present, "expected": sorted(_ALLOWED)}

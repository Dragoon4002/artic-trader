"""One-shot: build the Morph 'golden' snapshot for Artic VMs.

Prerequisites:
    - `scripts/build_images.sh` has produced the image tarballs:
        hub/docker/images/artic-agent-<tag>.tar.gz
        hub/docker/images/artic-user-server-<tag>.tar.gz
    - hub is running + reachable from the internet at $HUB_PUBLIC_URL
    - env: MORPH_API_KEY, BASE_SNAPSHOT_ID, HUB_PUBLIC_URL, INTERNAL_SECRET
    - optional: RELEASE_TAG (default "v0")

Flow:
    1. Start instance from BASE_SNAPSHOT_ID
    2. apt-install postgresql-14 + docker.io + curl
    3. Create 'artic' postgres user + 'artic' db
    4. Curl both image tarballs from hub → docker load
    5. Snapshot the instance
    6. Stop the instance
    7. Print MORPH_GOLDEN_SNAPSHOT_ID — paste into .env.dev

Re-run this per release (when images change) to produce a fresh golden.
"""

from __future__ import annotations

import os
import sys
import textwrap

try:
    from morphcloud.api import MorphCloudClient
except ImportError:
    sys.exit("morphcloud not installed — pip install morphcloud")


def require(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        sys.exit(f"missing env: {name}")
    return val


def main() -> None:
    api_key = require("MORPH_API_KEY")
    base_snapshot = require("BASE_SNAPSHOT_ID")
    hub_url = require("HUB_PUBLIC_URL").rstrip("/")
    hub_secret = require("INTERNAL_SECRET")
    release = os.environ.get("RELEASE_TAG", "v0")

    client = MorphCloudClient(api_key=api_key)

    print(f"[1/7] starting instance from base snapshot {base_snapshot}…")
    instance = client.instances.start(snapshot_id=base_snapshot)
    instance.wait_until_ready(timeout=120)
    print(f"      instance {instance.id} ready")

    try:
        setup = textwrap.dedent(f"""
            set -euxo pipefail
            export DEBIAN_FRONTEND=noninteractive
            apt-get update
            apt-get install -y postgresql-14 docker.io curl ca-certificates
            systemctl enable --now postgresql
            systemctl enable --now docker
            sudo -u postgres psql -c "DO $$ BEGIN
              IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='artic') THEN
                CREATE ROLE artic WITH LOGIN SUPERUSER PASSWORD 'artic';
              END IF;
            END $$;" postgres
            sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='artic'" | grep -q 1 \\
              || sudo -u postgres createdb -O artic artic
        """).strip()
        print("[2/7] apt install + postgres setup…")
        result = instance.exec(f"bash -lc '{setup}'")
        if result.exit_code != 0:
            raise SystemExit(
                f"setup failed (exit {result.exit_code}): {result.stderr[-2000:]}"
            )

        load_script = textwrap.dedent(f"""
            set -euxo pipefail
            HDR='X-Hub-Secret: {hub_secret}'
            URL={hub_url}/internal/v1/images
            curl -fSL -H "$HDR" "$URL/artic-user-server-{release}.tar.gz" \\
              | gunzip | docker load
            curl -fSL -H "$HDR" "$URL/artic-agent-{release}.tar.gz" \\
              | gunzip | docker load
            docker images | grep -E 'artic-(agent|user-server)'
        """).strip()
        print(f"[3/7] curl + docker load images from {hub_url}…")
        result = instance.exec(f"bash -lc '{load_script}'")
        if result.exit_code != 0:
            raise SystemExit(
                f"image load failed (exit {result.exit_code}): {result.stderr[-2000:]}"
            )

        print("[4/7] fsync…")
        instance.exec("bash -lc 'sync'")

        print("[5/7] snapshot (may take 30-60s)…")
        snap = instance.snapshot()
        print(f"      snapshot id: {snap.id}")

    finally:
        print("[6/7] stopping build instance…")
        try:
            instance.stop()
        except Exception as e:
            print(f"      (warning: stop failed: {e})")

    print("[7/7] done")
    print()
    print("══════════════════════════════════════════════════════════════")
    print(f"  MORPH_GOLDEN_SNAPSHOT_ID={snap.id}")
    print("══════════════════════════════════════════════════════════════")
    print()
    print("Paste the line above into .env.dev and restart the hub.")


if __name__ == "__main__":
    main()

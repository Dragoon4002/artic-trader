"""One-shot: build the Morph 'golden' snapshot for Artic VMs.

Prerequisites:
    - `scripts/build_images.sh` has produced the image tarballs:
        hub/docker/images/artic-agent-<tag>.tar.gz
        hub/docker/images/artic-user-server-<tag>.tar.gz
    - env: MORPH_API_KEY, BASE_SNAPSHOT_ID
    - optional: RELEASE_TAG (default "v0")

Flow:
    1. Start instance from BASE_SNAPSHOT_ID
    2. apt-install postgresql + docker.io
    3. Create 'artic' postgres user + 'artic' db
    4. Upload tarballs via SFTP + docker load (no HTTP server needed)
    5. Snapshot the instance
    6. Stop the instance
    7. Print MORPH_GOLDEN_SNAPSHOT_ID — paste into .env.dev

Re-run this per release (when images change) to produce a fresh golden.
"""

from __future__ import annotations

import os
import shlex
import sys
import textwrap
import time

try:
    from morphcloud.api import MorphCloudClient
except ImportError:
    sys.exit("morphcloud not installed — pip install morphcloud")


def exec_with_retry(instance, cmd: str, retries: int = 10, delay: float = 8.0):
    import morphcloud.api as _mapi
    for attempt in range(1, retries + 1):
        try:
            return instance.exec(cmd)
        except _mapi.ApiError as e:
            if e.status_code == 502 and attempt < retries:
                print(f"      exec 502 (attempt {attempt}/{retries}), retrying in {delay}s…")
                time.sleep(delay)
                continue
            raise


def require(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        sys.exit(f"missing env: {name}")
    return val


def main() -> None:
    api_key = require("MORPH_API_KEY")
    base_snapshot = require("BASE_SNAPSHOT_ID")
    release = os.environ.get("RELEASE_TAG", "v0")

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    agent_tar = os.path.join(root, "hub", "docker", "images", f"artic-agent-{release}.tar.gz")
    userserver_tar = os.path.join(root, "hub", "docker", "images", f"artic-user-server-{release}.tar.gz")

    for path in (agent_tar, userserver_tar):
        if not os.path.isfile(path):
            sys.exit(f"tarball not found: {path}\nRun: bash scripts/build_images.sh")

    client = MorphCloudClient(api_key=api_key)

    print(f"[1/7] starting instance from base snapshot {base_snapshot}…")
    instance = client.instances.start(snapshot_id=base_snapshot)
    instance.wait_until_ready(timeout=120)
    print(f"      instance {instance.id} ready — waiting 15s for exec endpoint…")
    time.sleep(15)

    try:
        setup = textwrap.dedent("""
            set -euxo pipefail
            export DEBIAN_FRONTEND=noninteractive
            systemd-run --property="After=apt-daily.service apt-daily-upgrade.service" --wait true 2>/dev/null || true
            flock -w 120 /var/lib/dpkg/lock-frontend apt-get update
            flock -w 120 /var/lib/dpkg/lock-frontend apt-get install -y postgresql docker.io ca-certificates
            systemctl enable --now postgresql
            systemctl enable --now docker
            sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='artic'" | grep -q 1 \\
              || sudo -u postgres psql -c "CREATE ROLE artic WITH LOGIN SUPERUSER PASSWORD 'artic'"
            sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='artic'" | grep -q 1 \\
              || sudo -u postgres createdb -O artic artic
        """).strip()
        print("[2/7] apt install + postgres setup…")
        result = exec_with_retry(instance, f"bash -lc {shlex.quote(setup)}")
        if result.exit_code != 0:
            raise SystemExit(f"setup failed (exit {result.exit_code}): {result.stderr[-2000:]}")

        print("[3/7] uploading image tarballs via SFTP…")
        instance.upload(agent_tar, f"/tmp/artic-agent-{release}.tar.gz")
        print(f"      uploaded artic-agent-{release}.tar.gz")
        instance.upload(userserver_tar, f"/tmp/artic-user-server-{release}.tar.gz")
        print(f"      uploaded artic-user-server-{release}.tar.gz")

        load_script = textwrap.dedent(f"""
            set -euxo pipefail
            docker load < /tmp/artic-agent-{release}.tar.gz
            docker load < /tmp/artic-user-server-{release}.tar.gz
            rm -f /tmp/artic-agent-{release}.tar.gz /tmp/artic-user-server-{release}.tar.gz
            docker images | grep -E 'artic-(agent|user-server)'
        """).strip()
        print("[4/7] docker load images…")
        result = exec_with_retry(instance, f"bash -lc {shlex.quote(load_script)}")
        if result.exit_code != 0:
            raise SystemExit(f"image load failed (exit {result.exit_code}): {result.stderr[-2000:]}")

        print("[5/7] fsync…")
        exec_with_retry(instance, "bash -lc 'sync'")

        print("[6/7] snapshot (may take 30-60s)…")
        snap = instance.snapshot()
        print(f"      snapshot id: {snap.id}")

    finally:
        print("[7/7] stopping build instance…")
        try:
            instance.stop()
        except Exception as e:
            print(f"      (warning: stop failed: {e})")

    print()
    print("══════════════════════════════════════════════════════════════")
    print(f"  MORPH_GOLDEN_SNAPSHOT_ID={snap.id}")
    print("══════════════════════════════════════════════════════════════")
    print()
    print("Paste the line above into .env.dev and restart the hub.")


if __name__ == "__main__":
    main()

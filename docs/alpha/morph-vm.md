# Morph VM — Provider Spec

How Artic uses [Morph Cloud](https://cloud.morph.so/docs/) as the user-VM substrate. Scope: **snapshot create**, **instance start**, **launch user-server + agents (Docker)**, **snapshot save**, **instance delete**. Anything else (branch, FUSE, reverse tunnels) is out of scope until beta.

> Connects to: [plans/user-vm.md](plans/user-vm.md) (lifecycle), [plans/hub.md](plans/hub.md) (vm module), [system-map.md](system-map.md) (call graph), [security-model.md](security-model.md) (secrets, sandbox). Reference implementation we're cloning patterns from: [morph-server.md](morph-server.md).

---

## 1. Mental model

| Primitive | What it is | Lifetime | Cost driver |
|-----------|------------|----------|-------------|
| **Image** | Read-only base rootfs (e.g. `morphvm-minimal`) | Provider-managed | none |
| **Snapshot** | Frozen VM disk + RAM + config; bootable, content-addressed | Until deleted (or TTL) | storage |
| **Instance** | Running (or paused) VM booted from a snapshot | Until stopped (or TTL action) | vCPU + RAM + disk per second |

Two snapshots in the system:

| Snapshot | Built when | Holds | Stored where |
|----------|-----------|-------|--------------|
| **Base** (`BASE_SNAPSHOT_ID`) | Once, manually | Blank Ubuntu + nothing | env var on hub |
| **Golden** (`MORPH_GOLDEN_SNAPSHOT_ID`) | Per release, by CI | Base + dockerd + Postgres + `artic-user-server` image + `artic-agent` image | hub config |
| **Per-user** (`users.vm_snapshot_id`) | On every drain | Golden + user's Postgres data + RAM state of running agents | hub Postgres `users` table |

Flow: `base → (release build) → golden → (user wake) → instance → (drain) → per-user → (resume) → instance → … → delete`.

### Inside the VM

```
Morph instance (one per user)
├── Postgres 14            ← installed on rootfs (apt), not containerized
├── dockerd                ← installed on rootfs
├── user-server container  ← mounts /var/run/docker.sock, spawns agents
└── agent-<id> container   ← one per agent, started by user-server
    agent-<id> container
    agent-<id> container
```

Postgres lives on the rootfs (not in a container) so its data path `/var/lib/postgresql/14/main` is captured cleanly by `instance.snapshot()` and resumes with the VM. user-server is in a container so releases ship via `docker pull`. Each agent gets its own container for per-agent log/resource/lifecycle isolation — user-server controls them via the mounted Docker socket.

---

## 2. Operations Artic uses

| # | Op | When | Caller | Morph SDK call (TS) |
|---|----|------|--------|---------------------|
| 1 | Build golden snapshot | per release | CI / hub bootstrap | start instance from base → install → `instance.snapshot()` → `instance.stop()` |
| 2 | Start instance from snapshot | user wake | `hub.vm.wake(user_id)` | `client.instances.start({ snapshotId, ttlSeconds, ttlAction: "pause" })` |
| 3 | Configure wake-on-HTTP | right after step 2 | `hub.vm.wake` | raw REST `POST /api/instance/{id}/wake-on` (SDK doesn't expose) |
| 4 | Launch user-server + expose URL | first boot of every wake | `hub.vm.wake` after instance ready | `instance.exec("docker run … artic-user-server …")` then `instance.exposeHttpService("user-server", 80)` |
| 5 | Save snapshot from instance | drain | `hub.vm.drain(user_id)` | `instance.snapshot()` |
| 6 | Delete instance | post-drain | `hub.vm.drain` after save | `instance.stop()` |
| 7 | Delete old per-user snapshot | post-save | `hub.vm.drain` cleanup | `(await client.snapshots.get({ snapshotId })).delete()` |

Anything not in this table is **out of scope for alpha**. New row first, then code.

Agent containers are spawned **inside** the VM by user-server (`docker run -d --name agent-<id> artic-agent`). Hub doesn't see them — they're an implementation detail of the user-server, documented in [plans/user-vm.md](plans/user-vm.md).

---

## 3. Auth + setup

| Item | Value |
|------|-------|
| API key env | `MORPH_API_KEY` |
| REST base env | `MORPH_BASE_URL` (needed for `wake-on` — not in SDK) |
| Base snapshot env | `BASE_SNAPSHOT_ID` (blank Morph VM, used as build host for golden) |
| Golden snapshot env | `MORPH_GOLDEN_SNAPSHOT_ID` (output of release build) |
| Source for keys | https://cloud.morph.so/web/keys |
| TS install | `npm install morphcloud` |
| Python install | `pip install morphcloud --upgrade` (3.10+) |
| HTTP base | `https://cloud.morph.so/api` |
| Auth header | `Authorization: Bearer $MORPH_API_KEY` |
| `.env` rule | values must NOT be double-quoted when using `--env-file` (Bun/Docker quirk) |

Hub is the **only** component that holds `MORPH_API_KEY`. user-server and agents never see it — they cannot self-snapshot or self-delete.

---

## 4. Op-by-op detail

All examples in TypeScript (matches morph-server.md). Python is symmetric — see [SDK README](https://github.com/morph-labs/morph-python-sdk).

### 4.1 Build golden snapshot

Run once per release. Pattern: start a build instance from the base, install everything, snapshot it, stop the build instance. Output is a `snapshotId` recorded in hub config as `MORPH_GOLDEN_SNAPSHOT_ID`.

```typescript
import { MorphCloudClient } from "morphcloud";

const client = new MorphCloudClient({ apiKey: process.env.MORPH_API_KEY });

const build = await client.instances.start({
    snapshotId: process.env.BASE_SNAPSHOT_ID!,
});
await build.waitUntilReady(60);

const setup = `
    set -euo pipefail
    apt-get update
    apt-get install -y postgresql-14 docker.io
    systemctl enable --now postgresql docker
    sudo -u postgres createuser -s artic
    sudo -u postgres createdb -O artic artic
    docker pull ghcr.io/silonelabs/artic-user-server:${process.env.RELEASE_TAG}
    docker pull ghcr.io/silonelabs/artic-agent:${process.env.RELEASE_TAG}
`;
await build.exec(`bash -lc '${setup}'`);

const golden = await build.snapshot();
console.log("golden:", golden.id);
await build.stop();
```

| Param | Alpha default | Notes |
|-------|---------------|-------|
| Base image (in `BASE_SNAPSHOT_ID`) | `morphvm-minimal` derivative | provider-supplied |
| `vcpus` | 2 | tune per cost test |
| `memory` (MB) | **2044** | quirk inherited from morph-server; not 2048 |
| `diskSize` (MB) | 10000 | rootfs + dockerd images + per-user Postgres |

> Note: morph-server.md flags that `vcpus`/`memory`/`diskSize` accepted in its pipeline are **not forwarded** to `instances.start`. We must forward them; track in [build-checklist.md](build-checklist.md).

**REST**: `POST /api/snapshot` (cold create from image, blank); `POST /api/instance/{id}/snapshot` (snapshot a running instance — what we use).

### 4.2 Start instance from snapshot

Called on user wake. `snapshotId` is golden (first wake) or per-user (subsequent wakes).

```typescript
const instance = await client.instances.start({
    snapshotId,
    ttlSeconds: 240,
    ttlAction: "pause",
});
await instance.waitUntilReady(30);
```

| Param | Value | Why |
|-------|-------|-----|
| `ttlSeconds` | 240 | safety net — auto-pause if hub forgets to drain |
| `ttlAction` | `"pause"` | pause (not stop) so wake-on-HTTP can resume; cheaper than stop+restart |

Persist `instance.id` against `users.vm_instance_id` in hub Postgres ([data-model.md](data-model.md)).

**REST**: `POST /api/instance` (body: `snapshot_id`, `ttl_seconds`, `ttl_action`).

### 4.3 Configure wake-on-HTTP

The SDK doesn't expose this. Hit raw REST right after `instances.start`:

```typescript
await fetch(`${process.env.MORPH_BASE_URL}/api/instance/${instance.id}/wake-on`, {
    method: "POST",
    headers: {
        "Authorization": `Bearer ${process.env.MORPH_API_KEY}`,
        "Content-Type": "application/json",
    },
    body: JSON.stringify({ wake_on_http: true, wake_on_ssh: false }),
});
```

After this call, an inbound HTTP request to the instance's exposed service auto-resumes the paused VM. This is the cost mechanism: idle 240s → pause → next dashboard request → wake → serve. User-server + agents come back at the exact RAM state they were paused in (Postgres connections survive, in-flight ticks survive).

`wake_on_ssh: false` because hub uses `instance.exec` (Morph-native) for control, not raw SSH.

### 4.4 Launch user-server + expose URL

After `waitUntilReady`, start the user-server container, then mint the public URL.

```typescript
const runCmd = `
    docker run -d --rm \
        --name user-server \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -e DATABASE_URL=postgres://artic@localhost:5432/artic \
        -e HUB_URL=${process.env.HUB_URL} \
        -e USER_ID=${userId} \
        -e USER_TOKEN=${userToken} \
        -p 80:8000 \
        ghcr.io/silonelabs/artic-user-server:${releaseTag}
`;
await instance.exec(`bash -lc '${runCmd}'`);

// Wait for user-server to be ready before exposing the URL.
// Avoids the 502 race documented in morph-server.md.
await instance.exec(
    `bash -lc 'for i in $(seq 1 30); do curl -fs http://localhost:80/healthz && exit 0; sleep 1; done; exit 1'`
);

const service = await instance.exposeHttpService("user-server", 80);
// service.url → "https://user-server-<instanceId>.morph.so" (or similar)
```

Key choices:
- `--name user-server` — fixed name; one per VM, no collision
- Docker socket mount lets user-server `docker run`/`rm` agent containers (op handed off to user-server, see [plans/user-vm.md](plans/user-vm.md))
- `localhost:5432` works because Postgres runs on the rootfs, same network namespace as the container (no `--network host` needed if we publish Postgres on the host loopback — confirm in build-checklist)
- Container port 8000 → host port 80 → `exposeHttpService("user-server", 80)`
- **Healthz poll before expose** — fixes the [morph-server.md §4 caveat](morph-server.md) about un-awaited `docker run` racing the public URL

Save `service.url` against `users.vm_url` for the dashboard to proxy through.

**REST**: `POST /api/instance/{id}/exec` (sync) or `POST /api/instance/{id}/http` (expose service).

### 4.5 Save snapshot from instance

Called on drain (idle threshold, credit halt, or release upgrade). New snapshot id replaces `users.vm_snapshot_id`.

Drain sequence (hub-side):

```typescript
// 1. Tell user-server to flush.
await fetch(`${userVmUrl}/drain`, { method: "POST" });
// 2. Wait for confirmation (user-server flushes trades, fsyncs Postgres, stops agents).
await waitFor(() => fetch(`${userVmUrl}/drain/status`).then(r => r.json()).then(s => s.done));
// 3. Snapshot the instance.
const newSnapshot = await instance.snapshot();
// 4. Update hub DB.
await db.user.update({ where: { id: userId }, data: { vmSnapshotId: newSnapshot.id } });
// 5. Delete previous per-user snapshot (op 4.7).
if (oldSnapshotId) {
    const old = await client.snapshots.get({ snapshotId: oldSnapshotId });
    await old.delete();
}
// 6. Stop the instance (op 4.6).
await instance.stop();
```

`instance.snapshot()` blocks the VM briefly (RAM serialize). The drain hook in user-server should make this idempotent — if hub re-runs steps 1-2 it should not produce duplicate trades.

**REST**: `POST /api/instance/{id}/snapshot`.

### 4.6 Delete instance

After snapshot is durable.

```typescript
await instance.stop();
```

Releases vCPU/RAM/disk billing. Hub clears `users.vm_instance_id` to NULL.

**REST**: `DELETE /api/instance/{id}`.

### 4.7 Delete old per-user snapshot

Cleanup after every successful save. The SDK pattern (matches morph-server.md `cleanUp` helper):

```typescript
const snap = await client.snapshots.get({ snapshotId: oldSnapshotId });
await snap.delete();
```

Note: there is **no** `client.snapshots.delete(id)` — must `get` first, then call `.delete()` on the returned object.

Run this in the same drain transaction as 4.5–4.6. If it fails, log and let a cleanup cron retry — never block user wake.

**REST**: `DELETE /api/snapshot/{id}`.

---

## 5. Failure handling

| Failure | Detection | Response |
|---------|-----------|----------|
| `instances.start` times out | `waitUntilReady` rejects | hub retries once with backoff; second fail → mark user `vm_status=error`, page ops |
| `wake-on` REST returns non-2xx | response check | log + retry once; second fail → continue without wake-on (instance will hard-stop on TTL instead of pause — degraded but functional) |
| `instance.exec` for `docker run` non-zero | exit code in result | hub aborts wake, `instance.stop()`, mark `vm_status=boot_failed` |
| Healthz poll exhausted (30s) | exec exit 1 | abort wake, `instance.stop()`, mark `vm_status=boot_failed` |
| `exposeHttpService` rejects | exception | abort wake, `instance.stop()` |
| `instance.snapshot()` raises mid-drain | exception | **do not** stop instance; retry up to 3×; final fail → keep instance alive, alert |
| `instance.stop()` raises after snapshot saved | exception | log + retry; provider TTL is the safety net |
| Old snapshot delete fails | exception | log; rerun in cleanup cron — never blocks user wake |

**Invariant**: never `stop()` an instance whose latest user-state snapshot has not been confirmed durable. Losing the snapshot loses user trades + Postgres state.

**Invariant**: never re-use an `instance.id` after `stop()` — Morph rejects it. Always wake a fresh instance from the latest snapshot.

---

## 6. Cost + TTL knobs

| Setting | Where | Alpha default |
|---------|-------|---------------|
| Instance idle TTL | `instances.start({ ttlSeconds })` | 240 s |
| Instance idle action | `instances.start({ ttlAction })` | `"pause"` (NOT `"stop"` — keeps wake-on-HTTP useful) |
| wake-on-HTTP | raw REST `wake-on` | `true` |
| wake-on-SSH | raw REST `wake-on` | `false` |
| Per-user snapshot TTL | not set | none (must persist) |
| Build/CI snapshot TTL | `snapshots.create({ ttl })` if applicable | 24 h |
| Resource limits | golden snapshot config | vcpus=2, memory=2044 MB, disk=10000 MB |

Cost flow per active user: bursts of vCPU/RAM during dashboard sessions and agent ticks; pause between. Idle users pay only snapshot storage (one per-user snapshot).

---

## 7. What we deliberately don't use (alpha)

| Feature | Why skipped |
|---------|------------|
| `instance.branch()` | no staging-clone use case yet |
| Explicit `pause` / `resume` | TTL `pause` + wake-on-HTTP covers it |
| FUSE / file-management endpoints | all state in VM Postgres + Docker volumes; no host↔guest sync |
| Instance metadata API | user/VM mapping lives in hub Postgres, single source of truth |
| `exec/sse` (streaming) | hub uses sync `exec` for boot; agent logs ship via user-server → hub OTel pipe |
| `client.snapshots.create` (cold) | we always snapshot from a running instance, not from an image |
| Multiple `exposeHttpService` calls | one URL per VM (`user-server`); agents are not directly addressable from outside |

If any of these become necessary, add a row to §2 first.

---

## 8. Known gaps inherited from morph-server.md

Things to fix in our adaptation, not just copy:

| Gap | Fix in Artic |
|-----|--------------|
| `validateApiKey` middleware empty stub | Hub-issued JWT, validated in user-server boot |
| `vcpus`/`memory`/`diskSize` not forwarded to `instances.start` | Forward them — see §4.1 |
| `docker run` not awaited → 502 race vs `exposeHttpService` | Healthz poll between run and expose — see §4.4 |
| Hardcoded image tag `hello-world-example` | Templated by `RELEASE_TAG` env |
| Hardcoded service name `express-app` | Fixed but renamed `user-server` (one per VM is fine) |
| No instance-stop or snapshot-delete routes | Wired into hub `vm.drain` — see §4.6, §4.7 |
| `console.log` only | Replace with hub OTel exporter |

---

## 9. References

- Morph docs root: https://cloud.morph.so/docs/
- Python SDK: https://github.com/morph-labs/morph-python-sdk
- TypeScript SDK: https://github.com/morph-labs/morph-typescript-sdk
- API reference index: https://morph.so/docs/api-reference
- Examples: https://github.com/morph-labs/morphcloud-examples-public
- Reference impl we cloned patterns from: [morph-server.md](morph-server.md)

# Morph Server — Internal Workings

Detailed walkthrough of how `servers/morph-server` drives the MorphCloud SDK to provision snapshots, launch instances, run Docker inside them, expose HTTP services, and tear down resources.

## 1. High-level Architecture

- Runtime: Bun + Hono HTTP server, entrypoint [src/index.ts](../src/index.ts). Listens on port `8080` with `idleTimeout: 255`.
- Wraps the `morphcloud` TS SDK. Every request gets a fresh `MorphCloudClient` injected via middleware.
- Two public endpoints (v1):
  - `POST /api/v1/snapshot/create` — build a reusable Docker image snapshot from an uploaded zip.
  - `POST /api/v1/instance/start` — launch an instance from a snapshot, run the container, expose an HTTP service URL.
- Helper `cleanUp` (not wired to a route yet) deletes snapshots in bulk.

Flow:

```
client ──▶ /api/v1/snapshot/create ──▶ createAndInitializeSnapshot() ──▶ snapshotId
client ──▶ /api/v1/instance/start  ──▶ createInstanceFromSnapshotId() ──▶ { instanceId, url }
```

## 2. Middleware & Env Wiring

File: [src/middleware/index.ts](../src/middleware/index.ts)

- `morphCloudMiddleware` — per-request, constructs `new MorphCloudClient({ apiKey: process.env.MORPH_API_KEY })` and stashes it as `c.get("mc")`.
- `corsMiddleware` — allowlists `CLIENT_URL` and `WORKER_URL` origins. Allows `X-API-Key`, `Authorization`, `Content-Type` headers.
- `validateApiKey` — placeholder, not implemented.

Required env vars:

| Var | Used in | Purpose |
|---|---|---|
| `MORPH_API_KEY` | middleware, pipelines | Auth for MorphCloud SDK + raw REST (`wake-on`) |
| `MORPH_BASE_URL` | pipelines | Base URL for raw MorphCloud REST (wake-on endpoint) |
| `BASE_SNAPSHOT_ID` | pipelines | Snapshot ID of the blank Morph VM used as build host |
| `API_KEY` | pipelines | Auth header for the upload service (`UD_URL`) |
| `UD_URL` | pipelines | Upload-download service base URL (fetches user zip by `fileId`) |
| `CLIENT_URL`, `WORKER_URL` | CORS | Allowed origins |

> README note: when supplying `--env-file`, values must NOT be double-quoted.

## 3. Creating a Snapshot

Endpoint: `POST /api/v1/snapshot/create`
Handler: [src/controllers/morph.controller.ts:8](../src/controllers/morph.controller.ts#L8)
Pipeline: [src/pipelines/index.ts:4](../src/pipelines/index.ts#L4) `createAndInitializeSnapshot`

Request body:

```json
{
  "fileId": "<id returned by the upload service>",
  "port":   3000
}
```

Defaults (pipeline-level): `fileId="yhh442kn5d4g"`, `PORT=3000`, `vcpus=2`, `memory=2044`, `diskSize=10000`.

Step-by-step:

1. **Start a build instance** off the base snapshot:
   ```ts
   mc.instances.start({ snapshotId: process.env.BASE_SNAPSHOT_ID! })
   ```
2. **Download the user zip** into the instance and unzip to `app/`:
   ```
   curl -H "X-API-Key: $API_KEY" -o downloaded.zip $UD_URL/download/$fileId
   unzip downloaded.zip -d app
   ```
   (executed via `instance.exec(...)`).
3. **Docker build** inside the VM — `set -euo pipefail` aborts the whole chain on any failure:
   ```
   bash -lc 'set -euo pipefail; cd app; docker build -t hello-world-example .'
   ```
4. **Verify image exists**:
   ```
   bash -lc 'docker image inspect hello-world-example > /dev/null 2>&1'
   ```
5. **Snapshot the instance**: `await instance.snapshot()` — this captures the Docker image layer inside the VM disk.
6. **Stop the build instance**: `await instance.stop()` once the snapshot is persisted.
7. **Response**:
   ```json
   { "message": "Created new Snapshot", "data": "<snapshotId>", "success": true }
   ```

Error handling: on any failure in steps 3-5, the pipeline stops the instance (inside a nested `try/catch` to swallow stop errors) and rethrows — no snapshot is taken. The controller returns HTTP 500 with `success: false`.

Notes:
- The image tag is hardcoded to `hello-world-example`. Change-log confirms this replaced the earlier approach of snapshotting without a pre-built image.
- `vcpus`, `memory`, `diskSize` params exist in the pipeline signature but are NOT passed to `mc.instances.start` — they're currently dead arguments.
- `port` is returned in the pipeline's return object but the controller only forwards `snapshotId`.

## 4. Creating an Instance (Docker Init + Service URL)

Endpoint: `POST /api/v1/instance/start`
Handler: [src/controllers/morph.controller.ts:33](../src/controllers/morph.controller.ts#L33)
Pipeline: [src/pipelines/index.ts:71](../src/pipelines/index.ts#L71) `createInstanceFromSnapshotId`

Request body:

```json
{
  "snapshotId": "snapshot_xxxxx",
  "apiKeyList": [["KEY", "value"], ["OTHER_KEY", "value"]],
  "port": 3000
}
```

`apiKeyList` → `-e KEY=value` flags passed to `docker run`. Optional; defaults to empty.
`port` → container-internal port (defaults 3000). Host port is hardcoded to 80.

Step-by-step:

1. **Start instance** from snapshot with auto-pause:
   ```ts
   mc.instances.start({
     snapshotId,
     ttlSeconds: 240,
     ttlAction: "pause",
   })
   ```
   After 240s of idle, the instance pauses (not destroyed).
2. **Configure wake-on-HTTP** via raw Morph REST (SDK doesn't expose it):
   ```
   POST $MORPH_BASE_URL/api/instance/$instanceId/wake-on
   Authorization: Bearer $MORPH_API_KEY
   body: { "wake_on_http": true, "wake_on_ssh": false }
   ```
   Paused instance auto-resumes on inbound HTTP.
3. **Build env-var flag string** from `apiKeyList`:
   ```
   -e KEY1=val1 -e KEY2=val2 ...
   ```
4. **Run the container**. Note: uses `instance.exec(...)` WITHOUT `await` — fire-and-forget:
   ```
   cd app
   docker run -d -p 80:$PORT <env-flags> --name app-<snapshotId> hello-world-example
   ```
   Image `hello-world-example` comes from the baked snapshot. Container bound to host port 80.
5. **Expose HTTP service** through Morph's ingress:
   ```ts
   const serviceUrl = await instance.exposeHttpService("express-app", 80)
   ```
   Service name is hardcoded to `express-app`; target port is 80 (the host port mapped above).
6. **Response**:
   ```json
   { "success": true, "data": { "instanceId": "...", "url": "https://..." } }
   ```

Caveats:
- The `docker run` `exec` is not awaited. If startup is slow, the exposed URL may 502 until the container is up — the `wake_on_http` + Docker daemon boot race is not guarded.
- `--name app-<snapshotId>` means re-running the same snapshot twice in the same instance would collide — fine because each instance is fresh.

## 5. Stopping an Instance

No HTTP endpoint exists for explicit stop. Stopping happens in two places:

- **Inside the snapshot pipeline** ([src/pipelines/index.ts:46](../src/pipelines/index.ts#L46), [:63](../src/pipelines/index.ts#L63)): build instance is always stopped after snapshot completes or on error.
- **Implicitly via TTL** for service instances: `ttlSeconds: 240`, `ttlAction: "pause"` — paused, not stopped. Resumes on HTTP (if `wake_on_http` configured).

To stop programmatically, call `instance.stop()` on the SDK-returned `instance` object. To do it via REST:

```
DELETE $MORPH_BASE_URL/api/instance/$instanceId
Authorization: Bearer $MORPH_API_KEY
```

(Not currently wired; would need a new controller/route.)

## 6. Removing a Snapshot

Helper: [src/helpers/morph.ts:3](../src/helpers/morph.ts#L3) `cleanUp`

```ts
export const cleanUp = async (ids: string[], mc: MorphCloudClient) => {
  await Promise.all(ids.map(async (id) => {
    const smap = await mc.snapshots.get({ snapshotId: id });
    await smap.delete();
  }));
};
```

- Accepts array of snapshot IDs; deletes in parallel.
- NOT exposed via a route yet — imported-but-unused utility. To wire up, add a `POST /snapshot/delete` route that calls `cleanUp` with the parsed IDs.

## 7. Docker Image Lifecycle Summary

```
zip (from UD_URL)
   │
   ▼
base snapshot → start instance → curl zip → unzip → docker build
                                                         │
                                                         ▼
                                                 docker image inspect (verify)
                                                         │
                                                         ▼
                                                 instance.snapshot()
                                                         │
                                                         ▼
                                                  snapshotId persisted
                                                         │
 ┌───────────────────────────────────────────────────────┘
 ▼
start instance (ttl=240s, pause) → wake-on-http → docker run -d -p 80:PORT
                                                         │
                                                         ▼
                                          instance.exposeHttpService → public URL
```

## 8. Running the Server

From [README.md](../README.md):

```bash
docker build -t morph-server .
docker run -p 8080:8080 --env-file .env morph-server
```

Dev: `bun run dev` (hot reload). Prod: `bun run start`.

## 9. Known Gaps / TODOs (from code + change.log)

- `validateApiKey` middleware is an empty stub — no auth on public endpoints.
- `fileId` controller comment: `"Check if the API key is valid"` — not implemented.
- Service name for `exposeHttpService` is hardcoded (`express-app`). Code comment flags this: `TODO: generate a service name`.
- Image tag `hello-world-example` hardcoded.
- `vcpus`/`memory`/`diskSize` parameters accepted but never forwarded.
- `docker run` is not awaited — possible race against `exposeHttpService`.
- No endpoint for instance stop or snapshot delete — `cleanUp` exists but unrouted.
- Logs are `console.log` only — pipeline TODO mentions streaming console logs to the caller.

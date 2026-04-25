# Deploying Hub on Render

Guide for deploying `hub/` as a Render Web Service. Hub is FastAPI + Postgres. User-server runs on Morph VMs (not Render). Render hosts **only hub**.

## Prerequisites

- Render account with billing enabled (free tier won't persist secrets reliably)
- Morph account with API key + base snapshot ID already built (see `scripts/build_golden_snapshot.py`)
- External Postgres (Render Postgres, Neon, or Supabase) — hub's `user_vms`, `users`, `user_secrets` live here
- Domain name (optional; Render provides `*.onrender.com` free)

## Architecture with Render

```
[Web Dashboard]
      ↓ HTTPS
[Render Web Service: hub]  ← this is what we're deploying
      ↓ (VM provisioning)
[Morph Cloud]
      ↓ (per-user VMs)
[user-server + agent containers on each VM]
```

Render holds: hub code, hub Postgres, encrypted user secrets, VM registry.
Morph holds: user VMs, per-user user-server, agent trading containers.

## Part 1 — Code changes before deploy

### 1.1 Switch hub's Postgres driver for Render

`psycopg2-binary` is fine. Confirm `requirements.txt` pins both the sync (for alembic) and async (for runtime) drivers:

```
asyncpg>=0.29
psycopg2-binary>=2.9  # for alembic
```

### 1.2 Make port configurable via `PORT` env

Render injects `PORT` env var; hub currently reads `HUB_PORT`. Update `hub/server.py` entrypoint to honor `PORT` first:

```python
# at bottom of hub/server.py
if __name__ == "__main__":
    import uvicorn, os
    port = int(os.getenv("PORT") or settings.HUB_PORT or 8000)
    uvicorn.run("hub.server:app", host="0.0.0.0", port=port)
```

### 1.3 Run alembic migrations on startup

Add to `hub/Dockerfile`:
```dockerfile
CMD ["sh", "-c", "alembic upgrade head && python -m hub.server"]
```

(Alternative: Render pre-deploy hook. The above is simpler.)

### 1.4 Remove docker CLI dependency

`hub/Dockerfile` currently installs `docker.io`. Hub doesn't spawn containers — that's user-server on Morph VMs. Remove that line:

```dockerfile
# was: RUN apt-get update && apt-get install -y --no-install-recommends docker.io && rm -rf /var/lib/apt/lists/*
# replace with (only needed if build-from-source Python deps):
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
```

### 1.5 Mount images volume is not possible on Render

`docker-compose.dev.yml` mounts `./hub/docker/images:/app/hub/docker/images:ro` so `/internal/v1/images/*` can serve tarballs. On Render, there's no volume for that. Two options:

- **Option A (recommended)**: bake tarballs into the image at build time. Add to `hub/Dockerfile`:
  ```dockerfile
  COPY hub/docker/images/ /app/hub/docker/images/
  ```
  And check tarballs into git (or an S3/R2 sidecar — see Option B). **Caveat**: this bloats the image by ~260MB. Acceptable for Render's build pipeline but slow.

- **Option B**: move tarball hosting to Cloudflare R2 / S3 / GitHub Releases. Change `scripts/build_golden_snapshot.py` to curl from there. Bonus: decouples snapshot rebuilds from hub redeploys. Already mitigated since our `build_golden_snapshot.py` now uses SFTP upload (no HTTP server needed) — so **you can delete `hub/internal/images.py` and skip this entirely** unless you still want ad-hoc HTTP distribution.

### 1.6 CORS for production dashboard

Check `hub/server.py` for CORS middleware. Add your dashboard's public origin:
```python
allow_origins=["https://<your-vercel-app>.vercel.app", "https://artic.trade"]
```

### 1.7 JWT & KEK rotation

Generate production secrets locally:
```bash
python3 -c "import os,base64; print('KEK=' + base64.b64encode(os.urandom(32)).decode())"
python3 -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(48))"
python3 -c "import secrets; print('INTERNAL_SECRET=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('HUB_SECRET=' + secrets.token_urlsafe(32))"
```

## Part 2 — Render setup

### 2.1 Create the Postgres database

Render Dashboard → **New → PostgreSQL**
- Name: `artic-hub-db`
- Database: `artic`
- User: `artic`
- Region: same as web service
- Plan: Starter ($7/mo) minimum for persistence

Copy the **Internal Database URL** (format: `postgresql://...render.com/...`). Needed in step 2.3.

### 2.2 Create the Web Service

Render Dashboard → **New → Web Service**
- Connect your GitHub repo
- Branch: `main` (or whichever)
- Root Directory: leave blank (repo root — Dockerfile path references repo root)
- Runtime: **Docker**
- Dockerfile Path: `hub/Dockerfile`
- Docker Build Context Directory: `.` (repo root — hub/ imports from shared/)
- Region: same as DB
- Plan: Starter ($7/mo) or higher

### 2.3 Environment variables

Add in Render's Environment tab. **Bold** = required.

| Key | Value | Notes |
|---|---|---|
| **`DATABASE_URL`** | copy from step 2.1, prefix `postgresql+asyncpg://` | convert sync → async prefix |
| **`ENV`** | `prod` | |
| **`KEK`** | 32-byte base64 (from 1.7) | rotating this invalidates all stored user secrets |
| **`JWT_SECRET`** | random 48+ chars (from 1.7) | rotating logs all users out |
| **`INTERNAL_SECRET`** | random 32+ chars (from 1.7) | must match user-server's INTERNAL_SECRET (baked into golden snapshot env or pushed at wake) |
| **`HUB_SECRET`** | random 32+ chars (from 1.7) | must match user-server's HUB_SECRET (baked into golden snapshot) |
| **`VM_PROVIDER`** | `morph` | |
| **`MORPH_API_KEY`** | from Morph dashboard | |
| **`MORPH_BASE_URL`** | `https://cloud.morph.so/api` | default fine |
| **`MORPH_GOLDEN_SNAPSHOT_ID`** | from `scripts/build_golden_snapshot.py` output | update each rebuild |
| **`BASE_SNAPSHOT_ID`** | same as above, but for rebuilds | can omit if not running rebuilds from Render |
| **`HUB_PUBLIC_URL`** | `https://<your-service>.onrender.com` | set after first deploy |
| **`TWELVE_DATA_API_KEY`** | Twelve Data dashboard | platform-shared key for market data |
| **`PYTH_HERMES_URL`** | `https://hermes.pyth.network` | default fine |
| **`AUTH_MESSAGE_DOMAIN`** | `artic.trade` (or your domain) | |
| **`AUTH_SUPPORTED_CHAINS`** | `initia-testnet` | |
| **`VM_WAKE_TIMEOUT_SECONDS`** | `60` | Morph VM wake can be slow on cold start |
| **`HSK_RPC_URL`** | Initia MiniEVM RPC endpoint | required for on-chain logging |
| **`PLATFORM_WALLET_KEY`** | platform wallet private key | funds & gas |

Optional:
- `OTEL_COLLECTOR_URL` — observability endpoint
- `INITIA_NAME_SERVICE_URL` — for `.init` username reverse lookup

### 2.4 Health Check Path

Under Settings → Health Check Path: `/health`

### 2.5 Disk (not needed)

Skip. Hub is stateless; Postgres handles persistence.

### 2.6 Custom domain (optional)

Settings → Custom Domains → Add `api.artic.trade` (or your chosen subdomain). Render provisions TLS automatically.

Update `HUB_PUBLIC_URL` env var to match the custom domain.

## Part 3 — Post-deploy

### 3.1 First-deploy checks

Once Render marks the service "Live":

```bash
curl https://<your-service>.onrender.com/health
# expect: {"ok": true} or similar
```

Check logs in Render dashboard for `alembic upgrade head` success.

### 3.2 Update web client to point at prod hub

In `clients/web/` (wherever it's deployed — Vercel, etc.), set env:
```
NEXT_PUBLIC_HUB_URL=https://<your-service>.onrender.com
```

### 3.3 Golden snapshot: rebuild to match prod secrets

Critical: the `INTERNAL_SECRET` and `HUB_SECRET` you put in Render must match what's baked into the user-server inside the golden snapshot. If you've rotated them for prod, rebuild:

```bash
# Locally, with prod secrets in .env.dev:
bash scripts/build_images.sh
python3 scripts/build_golden_snapshot.py
# paste MORPH_GOLDEN_SNAPSHOT_ID into Render env vars, redeploy
```

### 3.4 DB migrations for future changes

Every deploy runs `alembic upgrade head` thanks to step 1.3. No manual action needed for schema changes — just push.

## Part 4 — Known gotchas

### 4.1 Cold-start latency

Render's free tier sleeps after 15 min idle — first request takes ~30s. Morph VM wake on top of that = poor UX. Use at least Starter plan.

### 4.2 Outbound egress to Morph

Render allows outbound HTTPS to `cloud.morph.so` by default. No allowlist needed.

### 4.3 Docker images baked into hub image

If you chose Option A in 1.5, tarballs are in the Render-built image. Each snapshot rebuild means: rebuild tarballs locally → commit to git → push → Render rebuilds → deploy. Heavy cycle. Prefer R2/S3 for prod (Option B).

### 4.4 Secrets rotation

Rotating `KEK` means all `user_secrets` encrypted values become unrecoverable — users must re-enter their API keys. Plan a migration path if rotating.

### 4.5 `HUB_PUBLIC_URL` and Morph

The only thing on Morph VMs that used to hit `HUB_PUBLIC_URL` was the golden snapshot build step (curling image tarballs). Now that we SFTP-upload, **`HUB_PUBLIC_URL` is not strictly required** — but leave it set in case future features (e.g. on-chain indexer push-back) need hub to be reachable from VMs.

## Summary checklist

- [ ] Code changes 1.1 – 1.7 applied + committed
- [ ] Render Postgres created
- [ ] Render Web Service created pointing at `hub/Dockerfile`
- [ ] All env vars from 2.3 set
- [ ] Health check responds
- [ ] Golden snapshot rebuilt with prod secrets
- [ ] Web client env updated to prod hub URL
- [ ] Test: create user → create agent → start → logs + trades flow through

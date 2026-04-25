0 · Start the stack

make dev          # hub + user-server-db + hub-db containers up
make migrate      # runs alembic head on both DBs
Verify: curl -s localhost:8000/health → {"ok":true}.

1 · Auth — get a JWT + session_id
All /api/v1/u/* calls require Authorization: Bearer <JWT> — the wake-proxy middleware reads the JWT to know which VM to wake.

1a · POST /auth/nonce — get a challenge
URL	http://localhost:8000/auth/nonce
Method	POST
Headers	Content-Type: application/json
Auth	none
Body	{"address": "init1xy…yourbech32", "chain": "initia-testnet"}
Response:


{
  "nonce": "q2a4…ZzT",
  "message": "artic.trade wants you to sign in with your initia-testnet account:\ninit1xy…\n\nSession public key: <session_pub>\nScope: authenticated-actions\nNonce: q2a4…ZzT\nIssued At: 2026-04-20T12:00:00+00:00\nExpires At: 2026-04-20T20:00:00+00:00",
  "expires_at": "2026-04-20T12:05:00+00:00"
}
Save: nonce.

1b · Sign locally — can't be done in Postman alone
The signature is over the real message the hub will rebuild at verify time. The preview message returned above is a placeholder (it uses <session_pub> literally). You must rebuild the message with your own session key and ADR-36 sign it. Minimal Python helper:


# scripts/dev_sign.py  —  pip install cosmpy ecdsa bech32 httpx
import base64, hashlib, json, secrets, sys
from datetime import datetime, timedelta, timezone
import httpx
from ecdsa import SigningKey, SECP256k1
from bech32 import bech32_encode, convertbits

HUB = "http://localhost:8000"
CHAIN = "initia-testnet"

def ripemd160(b): h = hashlib.new("ripemd160"); h.update(b); return h.digest()

# 1. Permanent wallet key (fake)
sk = SigningKey.generate(curve=SECP256k1)
pub = sk.get_verifying_key().to_string("compressed")            # 33 bytes
addr_bytes = ripemd160(hashlib.sha256(pub).digest())
address = bech32_encode("init", convertbits(addr_bytes, 8, 5))
pub_b64 = base64.b64encode(pub).decode()

# 2. Ephemeral session key
sess_sk = SigningKey.generate(curve=SECP256k1)
sess_pub_b64 = base64.b64encode(sess_sk.get_verifying_key().to_string("compressed")).decode()

# 3. /auth/nonce
r = httpx.post(f"{HUB}/auth/nonce", json={"address": address, "chain": CHAIN}); r.raise_for_status()
nonce = r.json()["nonce"]

# 4. Rebuild the exact message the hub will rebuild at verify time.
issued_at = datetime.now(timezone.utc)                          # hub uses nonce_row.created_at — NEAR enough
session_expires = issued_at + timedelta(hours=8)
msg = (
    f"artic.trade wants you to sign in with your {CHAIN} account:\n"
    f"{address}\n\n"
    f"Session public key: {sess_pub_b64}\n"
    f"Scope: authenticated-actions\n"
    f"Nonce: {nonce}\n"
    f"Issued At: {issued_at.isoformat()}\n"
    f"Expires At: {session_expires.isoformat()}"
)

# 5. ADR-36 sign doc (amino JSON, sorted keys, no whitespace)
doc = {
    "chain_id": "", "account_number": "0", "sequence": "0",
    "fee": {"gas": "0", "amount": []},
    "msgs": [{"type": "sign/MsgSignData", "value": {
        "signer": address,
        "data": base64.b64encode(msg.encode()).decode(),
    }}],
    "memo": "",
}
sign_bytes = json.dumps(doc, separators=(",", ":"), sort_keys=True).encode()
sig = sk.sign_digest(hashlib.sha256(sign_bytes).digest())
sig_b64 = base64.b64encode(sig).decode()

print(json.dumps({
    "address": address, "chain": CHAIN, "nonce": nonce,
    "signature": sig_b64, "pubkey": pub_b64,
    "session_pub": sess_pub_b64,
    "session_scope": "authenticated-actions",
    "session_expires_at": session_expires.isoformat(),
}, indent=2))
Known caveat: hub rebuilds issued_at from nonce_row.created_at (DB insert time), not your datetime.now(). In practice they agree to within a few ms; if the hub reconstructs with exactly the DB value and your signer used now() a moment later, the message differs → signature invalid.

Two fixes (pick one, recommend first):

Hub patch — return issued_at in /auth/nonce response and sign exactly that. One-line add to NonceResponse.
Dev bypass — add POST /auth/dev-token guarded by ENV=dev that mints a JWT for a fixed user. 10 lines; swap for /auth/verify below.
1c · POST /auth/verify — exchange for JWT + session_id
URL	http://localhost:8000/auth/verify
Method	POST
Headers	Content-Type: application/json
Auth	none
Body	output of the signer script (step 1b)
Response:


{
  "access_token": "eyJ…",
  "token_type": "bearer",
  "session_id": "uuid-session",
  "init_username": null
}
Save as Postman environment vars:

{{JWT}} = access_token
{{SESSION_ID}} = session_id
Cookie: hub sets an httpOnly refresh_token cookie. Postman stores it automatically if "Save cookies" is on.

2 · Scenario ① — Create an agent, VM spawns end-to-end
2a · POST /api/v1/u/agents — trigger everything
URL	http://localhost:8000/api/v1/u/agents
Method	POST
Headers	Authorization: Bearer {{JWT}} · Content-Type: application/json
Auth	JWT
Body	see below

{
  "name": "BTC momentum",
  "symbol": "BTCUSDT",
  "llm_provider": "anthropic",
  "llm_model": "claude-sonnet-4-5",
  "strategy_pool": ["ema_crossover", "rsi_reversion"],
  "risk_params": {
    "amount_usdt": 500,
    "leverage": 5,
    "tp_pct": 1.5,
    "sl_pct": 0.8,
    "poll_seconds": 1.0,
    "supervisor_interval": 60
  }
}
Under the hood (no action needed, but so you know what to wait for):

WakeProxyMiddleware sees /api/v1/u/*, decodes JWT → user_id
Registry says VM is stopped → calls vm_service.wake(user_id)
Morph start boots from MORPH_GOLDEN_SNAPSHOT_ID
configure_wake_on_http + launch_user_server runs docker run artic-user-server:v0 inside the VM
Hub polls the VM's /health up to VM_WAKE_TIMEOUT_SECONDS (default 10s)
Secrets push to user-server, status → running
Hub forwards the original POST to user-server /agents with X-Hub-Secret injected automatically
User-server persists the Agent row then docker run artic-agent:v0
Response with agent row bubbles back
Two possible responses:

200 with full agent body → success, VM + agent both running
202 {"error":{"code":"VM_WAKING"}} + Retry-After: 3 → VM is still booting; wait 3s and retry the same POST. Idempotent — won't double-create.
Response shape:


{
  "id": "uuid-agent",
  "name": "BTC momentum",
  "symbol": "BTCUSDT",
  "llm_provider": "anthropic",
  "llm_model": "claude-sonnet-4-5",
  "strategy_pool": ["ema_crossover", "rsi_reversion"],
  "risk_params": {...},
  "status": "stopped",
  "container_id": null,
  "port": null,
  "created_at": "2026-04-20T12:10:00Z",
  "updated_at": "2026-04-20T12:10:00Z"
}
Save {{AGENT_ID}} = id.

2b · POST /api/v1/u/agents/{id}/start
URL	http://localhost:8000/api/v1/u/agents/{{AGENT_ID}}/start
Method	POST
Headers	Authorization: Bearer {{JWT}}
Body	empty
Returns agent row with status: "alive", container_id, port.

3 · Scenario ② — Monitor VM details
3a · GET /auth/me — who am I
URL	http://localhost:8000/auth/me
Method	GET
Headers	Authorization: Bearer {{JWT}}
Response currently: {id, wallet_address, wallet_chain, init_username}.
Does not yet include VM status — 5-min patch: add vm_status, endpoint, last_active_at fields to MeResponse pulled from user_vms table.

3b · GET /api/v1/u/agents — list agents (triggers wake if stopped)
URL	http://localhost:8000/api/v1/u/agents
Method	GET
Headers	Authorization: Bearer {{JWT}}
Returns AgentOut[]. Because it goes through the wake-proxy, hitting this endpoint on a stopped VM cold-wakes it.

3c · GET /api/v1/u/agents/{id} — per-agent detail
Same path pattern, returns the same AgentOut shape (status, container_id, port).

3d · VM-level state — NOT EXPOSED YET
There is no endpoint today that returns {status: "running"|"waking"|"stopped", last_active_at, snapshot_id, provider_vm_id} directly. Two short-term paths:

Add GET /api/v1/vm (20-min hub edit): new router reading user_vms row for the JWT's user_id.
Extend /auth/me response with vm_status, last_active_at (5-min edit, simpler).
Until then: the presence of a 200 response on /api/v1/u/* means VM is running; a 202 VM_WAKING means waking; a hub log entry is the only place stopped/error shows.

4 · Scenario ③ — Stop + cold sleep
4a · POST /api/v1/u/agents/{id}/stop — stop the agent
URL	http://localhost:8000/api/v1/u/agents/{{AGENT_ID}}/stop
Method	POST
Headers	Authorization: Bearer {{JWT}}
Returns the agent row with status: "stopped", container_id: null. The docker stop happens inside the VM. VM itself stays running.

4b · DELETE /api/v1/u/agents/{id} — delete permanently
Same path, DELETE. Removes both the running container + the DB row. Returns 204.

4c · POST /api/v1/u/agents/stop-all — kill switch
URL	http://localhost:8000/api/v1/u/agents/stop-all
Method	POST
Headers	Authorization: Bearer {{JWT}}
Loops every alive agent in the VM and stops them. Agent-level only — VM stays running.

4d · Cold sleep (VM snapshot + stop) — NOT WIRED
Automatic drain cron doesn't exist yet. Two options to trigger it:

Option A — add manual endpoint POST /api/v1/vm/sleep (10 min hub patch):


@router.post("/api/v1/vm/sleep")
async def sleep_vm(user: User = Depends(get_current_user)):
    ok = await vm_service.drain(user.id)
    return {"drained": ok}
Then Postman:

URL	http://localhost:8000/api/v1/vm/sleep
Method	POST
Headers	Authorization: Bearer {{JWT}}
Option B — add a drain cron in lifespan:


# hub/server.py next to register_market_jobs
_scheduler.add_job(
    drain_idle_vms, "interval", seconds=300, id="drain_idle",
    args=[vm_service, idle_minutes=5],
)
Picks up every running VM whose last_active_at < now - 5min AND alive_agents == 0 and calls vm_service.drain(user_id). No Postman action — just wait.

After either: the VM is stopped on Morph, the snapshot is saved back to user_vms.snapshot_id. Next /api/v1/u/* request cold-wakes from that snapshot — loop closed.

Quick reference table
Step	URL	Method	Auth	Notes
Nonce	/auth/nonce	POST	none	{address, chain}
Verify	/auth/verify	POST	none	Full signed body from helper; returns JWT
Me	/auth/me	GET	Bearer JWT	Currently no VM fields
Sessions list	/auth/session	GET	Bearer JWT	
Session revoke	/auth/session	DELETE	Bearer JWT + session headers	Logout
List agents	/api/v1/u/agents	GET	Bearer JWT	Wakes VM; no session sig needed for reads
Create agent	/api/v1/u/agents	POST	Bearer JWT	Triggers full wake + user-server spawn + agent docker run
Get agent	/api/v1/u/agents/{id}	GET	Bearer JWT	
Start agent	/api/v1/u/agents/{id}/start	POST	Bearer JWT	
Stop agent	/api/v1/u/agents/{id}/stop	POST	Bearer JWT	
Delete agent	/api/v1/u/agents/{id}	DELETE	Bearer JWT	204
Kill switch	/api/v1/u/agents/stop-all	POST	Bearer JWT	
VM status	—	—	—	NOT wired — add to /auth/me or new /api/v1/vm
Cold sleep	/api/v1/vm/sleep	POST	Bearer JWT	NOT wired — 10 min hub patch
Refresh	/auth/refresh	POST	httpOnly cookie	Rotates refresh + issues new JWT
Headers you never set yourself (hub injects on proxied calls): X-Hub-Secret, X-Real-IP, X-User-Id.

Session-key headers (X-Session-Id, X-Session-Nonce, X-Session-Sig): documented in docs/alpha/api-contracts.md but not enforced on /api/v1/u/* yet — only /auth/session DELETE uses them. For now, JWT alone is enough for mutations.

Two hub patches unlock the last mile — the dev-token bypass (to skip signing), VM status on /auth/me, and the manual sleep endpoint are ~45 min total.
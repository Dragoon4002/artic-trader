# Artic — Hackathon Implementation Plan

Goal: maximize hackathon scoring. No video, no landing page, no infra/hosting work. Code + product only.

## Snapshot of current state (verified)

- InterwovenKit v2.6.0 installed but **not load-bearing** for auth — hub uses custom secp256k1 (ADR-36) wallet in localStorage. Need to wire InterwovenKit as primary signer.
- Web client points to Initia testnet `initiation-2` (rpc.testnet.initia.xyz) ✓
- `.init` username already resolved at `hub/auth/initia_names.py` and stored on `User.init_username` ✓ — but dashboard still shows wallet address everywhere
- Contracts (DecisionLogger, TradeLogger) deployed on **HashKey Chain**, NOT Initia. RPC env `HSK_RPC_URL`. Must redeploy on Initia rollup (`initiation-2`).
- `app/onchain_logger.py` + `onchain_trade_logger.py` gracefully no-op when env missing — needs always-on for demo on Initia.
- WebSocket `/ws/u/agents/*/logs` stubbed (returns 1011) — server + client both unimplemented.
- Trade history table has no tx-hash column / explorer links.
- No `.initia/submission.json`.
- Spawner does not pass chain RPC/private-key env to agent containers.
- `pnl_bot.py` lives only on VM, not in repo — ignore.

## Phase 1 — Initia chain & on-chain logging (CRITICAL)

- [ ] 1.1 Deploy `DecisionLogger.sol` + `TradeLogger.sol` to Initia `initiation-2` testnet using `contracts/deploy.py` + `deploy_trade_logger.py`. Update deployed.json files w/ new address, tx hash, block, chain ID, RPC URL.
- [ ] 1.2 Rename `HSK_RPC_URL` / `HSK_PRIVATE_KEY` → `INITIA_RPC_URL` / `INITIA_PRIVATE_KEY` (or aliases) across `app/onchain_logger.py:30-48`, `onchain_trade_logger.py:15-33`, env templates, docker-compose.dev.yml, user-server config, spawner env builder.
- [ ] 1.3 Add `INITIA_RPC_URL`, `INITIA_PRIVATE_KEY`, `INITIA_CHAIN_ID` to `user-server/user_server/agents/spawner.py:81-97` `build_env()` so agent containers inherit chain config.
- [ ] 1.4 Persist `decision_tx_hash` / `trade_tx_hash` on LogEntry/Trade rows when on-chain log lands.
- [ ] 1.5 Schema migration: add `decision_tx_hash`, `trade_tx_hash`, `chain_id` columns to Trade and LogEntry models in user-server.

## Phase 2 — Initia username (.init) as primary identity (user explicit ask)

Backend already stores `User.init_username`. Frontend ignores it.

- [ ] 2.1 Verify `init_username` returned in `/auth/verify`, `/auth/me` payloads. Add if missing.
- [ ] 2.2 Display `init_username || shortAddress(address)` everywhere wallet rendered:
  - `clients/web/components/dashboard/header.tsx`
  - `clients/web/app/app/settings/page.tsx`
  - `clients/web/app/(auth)/connect/connect-client.tsx`
  - grep `address.slice` / `0x` rendering across web client
- [ ] 2.3 Pass `OWNER_INIT_NAME` into agent container env via spawner. Agent uses for log attribution. Falls back to address if null.
- [ ] 2.4 Add `init_username` to `/agents/:id` response. Dashboard detail shows "owned by alice.init".
- [ ] 2.5 Username refresh button on settings (force re-resolution).

## Phase 3 — InterwovenKit as load-bearing signer

Currently InterwovenKit imported but `useHubAuth` uses custom secp256k1. Judges check this.

- [ ] 3.1 Refactor `clients/web/hooks/use-hub-auth.ts:49-72` to use `useInterwovenKit().address` as canonical wallet — remove localStorage privkey storage.
- [ ] 3.2 Replace ADR-36 `secp256k1.sign()` at `:131-132` with InterwovenKit's signing API. Verify hub auth path or add new tx-based nonce verification.
- [ ] 3.3 Wire `useInterwovenKit().autoSign` toggle on settings — framed as "agent autonomy" / session-key auto-sign.
- [ ] 3.4 Settings: show .init username, connected chain `initiation-2`, autoSign state.

## Phase 4 — Trades/decisions visible on-chain in dashboard

- [ ] 4.1 Add `tx_hash` column to trade history table (`clients/web/app/app/agents/[id]/page.tsx:227-242`) with explorer link `scan.testnet.initia.xyz/...`.
- [ ] 4.2 Third tab "On-chain Decisions" — DecisionLogged events from indexer w/ strategy, confidence, action, reasoning hash, tx link.
- [ ] 4.3 Header badge: "X decisions · Y trades logged on-chain". Add `/agents/:id/onchain-summary` if missing.

## Phase 5 — WebSocket log streaming

- [ ] 5.1 Implement `/ws/u/agents/{id}/logs` in user-server: tail LogEntry inserts, forward over WS.
- [ ] 5.2 Replace `hub/proxy/ws.py:24-30` stub with reverse-proxy to user-server WS (wake VM first).
- [ ] 5.3 Client: open WS in agent detail, fall back to polling on failure.

## Phase 6 — Reliable demo trades (replace pnl_bot.py glue)

- [ ] 6.1 Add `DemoMode` strategy to `app/strategies/` that fires every 30-60s on BTC w/ small momentum + side bias.
- [ ] 6.2 `demo_mode: bool` flag on agent create form (default off, on for demo).
- [ ] 6.3 Remove pnl_bot.py refs from `scripts/build_golden_snapshot.py`.

## Phase 7 — Submission file + README polish

- [ ] 7.1 Create `.initia/submission.json` per Initia spec: name, track (AI), description, repo, contract addrs, chain ID, team.
- [ ] 7.2 Rewrite root `README.md` for judges: one-liner, demo placeholder, Initia integration section (InterwovenKit + .init + auto-sign + chain ID + contracts), quickstart, module map. ≤200 lines.

## Out of scope (per user)

- Demo video
- Landing page (`clients/web/app/landing/`)
- Hosted demo URL / deployment
- Market positioning, pitch

## Execution order

Phase 1 → 2 → 3 → 4 → 5 → 6 → 7. Phase 1+2 unblock the rest (chain config + identity). Phase 3 may surface InterwovenKit API quirks — fallback to existing ADR-36 if blocked (InterwovenKit already imported satisfies the requirement; depth is bonus).

## Resolved (per inertia-details.md + user)

- **Own appchain REQUIRED.** `initiation-2` deploy alone disqualifies. Must run `weave init` → launch own EVM rollup → unique chain ID like `artic-1`. EVM track (Solidity contracts).
- Privkey provided: `beabde5c66458425f1b9f8350584e794c2efe7729c12cadc7a75287ea28dd530` (32-byte secp256k1, EVM-compatible).
- Explorer base: `https://scan.testnet.initia.xyz` (L1) — for L2 rollup, scan supports rollup chain ID.
- InterwovenKit: use `signMessage` per user.
- Submission JSON schema documented inline (project_name, repo_url, commit_sha, rollup_chain_id, deployed_address, vm, native_feature, core_logic_path, native_feature_frontend_path, demo_video_url).
- Native feature pick: `auto-signing` (also wire `.init` usernames as bonus identity surfacing).

## Phase 0 — Launch own EVM rollup (BLOCKED on user — interactive `weave init`)

User must run `weave init` per inertia-details.md Step 7. Provide me:
- `rollup_chain_id` (e.g. `artic-1`)
- rollup RPC URL (typically `http://localhost:26657` for local; may need exposed URL for hosted demo)
- gas-station mnemonic from `~/.weave/config.json` (or confirm the privkey above is funded as L2 dev key)

I cannot drive interactive prompts. Everything else proceeds in parallel; Phase 1 deploy unblocks once Phase 0 lands.

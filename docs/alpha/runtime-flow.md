# Runtime Flow — Alpha

Every lifecycle path the system actually walks. Ordered by how often it runs.

## 1. Cold wake (first client request after scale-to-zero)

```
client → hub GET /api/v1/u/agents          [JWT]

hub:
  user_id = jwt.sub
  vm = SELECT * FROM user_vms WHERE user_id = ?
  IF vm.status != 'running':
    UPDATE vm SET status='waking'
    vm_provider.resume(vm.provider_vm_id)     # Firecracker/Fly resume
    poll user_server /health (200ms, max 10s)
    POST user_server /hub/secrets/refresh     # decrypt + push user's LLM keys
    UPDATE vm SET status='running', last_active_at=now()
  proxy request → user_server /agents
  return response
```

If resume > 10s: hub returns `202 { code: "VM_WAKING" }` with `Retry-After`. Client shows shimmer and retries.

## 2. Tick loop (hot path, every `poll_seconds` per agent)

```
agent:
  price = Pyth Hermes GET /latest_price_feeds?ids={id}
  price_history.append(price)

  IF position open:
    check TP/SL → if hit: close locally → POST user-server /trades
    every supervisor_interval:
       POST user-server /llm/supervise → KEEP / CLOSE / ADJUST
  ELSE:
    IF strategy dispatch cadence reached:
       POST user-server /llm/plan → StrategyPlan

  candles = GET user-server /agents/{id}/candles (user-server reads from local hub cache mirror)
  signal, detail = strategies[name](plan, price_history, candles)   # RestrictedPython if user strat

  action = decide(signal, threshold, position.side)
  IF action == OPEN_LONG/SHORT:
    PaperExecutor.open(side, size, leverage, price)
    POST user-server /trades { agent_id, side, entry_price, … }
    user-server → chain signer → TradeLogger.logTrade(...) → tx_hash
    user-server writes indexer_tx locally
  IF action == CLOSE:
    close, compute pnl, POST user-server /trades (update)
    same on-chain path

  POST user-server /agents/{id}/status   (every tick)
  every 10 ticks: POST user-server /logs (batch)

  sleep(poll_seconds)
```

## 3. Agent create + start

```
client → hub POST /api/v1/u/agents {symbol, llm_provider, llm_model, strategy_pool, risk_params}
  hub proxy → user-server POST /agents
    user-server:
      INSERT agents row (status=stopped)
      return agent

client → hub POST /api/v1/u/agents/{id}/start
  hub proxy → user-server POST /agents/{id}/start
    user-server:
      allocate VM-internal port
      resolve strategies (builtin code + installed code blobs)
      docker run artic-app {
        HUB_AGENT_ID, SYMBOL, INTERNAL_SECRET, USER_SERVER_URL, STRATEGY_POOL, …
      }
      poll agent /health
      POST agent /start {StartRequest}
      UPDATE agents SET status=alive, container_id, port
      return agent
```

## 4. Trade → chain log → indexer

```
agent detects trade action
  → POST user-server /trades {payload}
  user-server:
    INSERT trades
    chain_signer.sign_and_send(TradeLogger.logTrade, payload_hash, session_id)
    on receipt:
      INSERT indexer_tx {tx_hash, agent_id, kind:'trades', amount_usdt, tags:{strategy_id, llm_provider, llm_model, symbol, side, pnl_bps}, block_number}
      UPDATE trades SET tx_hash
```

Supervisor events same shape, `kind='supervise'`, no `amount_usdt`.

## 5. Credit debit cron (hub, every minute)

```
hub cron @ */1 * * * *:
  FOR each user u WITH alive_agents > 0:
    delta = -(alive_agents / 60)
    UPDATE credits SET balance_ah = balance_ah + delta WHERE user_id = u
    INSERT credit_ledger {user_id, delta, reason:'tick_debit'}

    IF balance_ah <= 0:
      POST user_server /hub/halt
      mark agents as halted in hub cache
      push notification to client (WS)
```

`alive_agents` source of truth = hub's proxied status lookups + periodic heartbeat from user-server. If heartbeat stale > 90s, hub treats as `alive=0` (conservative — prevents runaway debit on orphan).

## 6. Scale-to-zero drain

```
hub cron @ */5 * * * *:
  FOR each vm WHERE status='running' AND last_active_at < now() - 5min:
    IF alive_agents(user_id) == 0:
      UPDATE user_vms SET status='draining'
      POST user_server /hub/drain
        user-server:
          stop all agents (idempotent — already stopped)
          POST hub /internal/v1/indexer/flush {rows since last_flush_at}
          fsync local DB
          return 200
      vm_provider.snapshot_and_stop(vm.provider_vm_id)
      UPDATE user_vms SET status='stopped'
```

Woken by next client request (Flow 1).

## 7. Platform wallet funder (testnet)

```
hub cron @ 0 */5 * * *:
  platform_bal = chain.balance(PLATFORM_WALLET)
  FOR each vm WHERE status IN ('running','waking'):
    bal = chain.balance(vm.wallet_address)
    IF bal < FUND_FLOOR_WEI:
      chain.send(from=PLATFORM_WALLET, to=vm.wallet_address, value=FUND_TOPUP_WEI)
      log + OTel metric
  alert IF platform_bal < FUND_MIN_RESERVE
```

Vars `FUND_FLOOR_WEI`, `FUND_TOPUP_WEI`, `FUND_MIN_RESERVE`, `FUND_INTERVAL_SEC` all env-configurable.

## 8. Connect + VM provision

Replaces the old email/password signup. Idempotent: same wallet connecting a second time just re-authenticates and issues a fresh session key.

```
client: wallet = interwovenkit.connect()       # {address, chain, pubkey}
client: sess   = ephemeralKeypair()            # in-memory only

client → hub POST /auth/nonce {address, chain}
  hub:
    if chain not in AUTH_SUPPORTED_CHAINS: return 400
    nonce = random_urlsafe(32)
    INSERT auth_nonce {address, chain, nonce, expires_at=now()+300s}
    message = build_message(domain, chain, address, nonce,
                            session_pub, session_scope, session_expires_at)
    return {nonce, message, expires_at}

client: signature = wallet.signArbitrary(message)    # ADR-36 for Initia

client → hub POST /auth/verify {
  address, chain, nonce, signature, pubkey,
  session_pub, session_scope, session_expires_at
}
  hub:
    row = SELECT * FROM auth_nonce WHERE nonce=? AND address=? AND chain=?
    assert row AND row.used_at IS NULL AND row.expires_at > now()
    reconstructed = build_message(...)                # same inputs
    assert VERIFIERS[chain](address, reconstructed, signature, pubkey)
    UPDATE auth_nonce SET used_at=now() WHERE id=row.id
    init_name = resolve_init_name(address)            # best-effort; may be NULL
    user = UPSERT users (wallet_address, wallet_chain)
           SET init_username=init_name, init_username_resolved_at=now()
    IF user was inserted (new row):
      chain_wallet = generate_keypair()               # platform-custodied VM wallet
      vm_provider.create_machine(image='user-server:latest') → provider_vm_id
      vm_provider.stop(provider_vm_id)                # immediately stop (scale-to-zero)
      INSERT user_vms {user_id, provider_vm_id, wallet_address:<chain_wallet.addr>,
                       status='stopped'}
      queue funder job (immediate)
    INSERT auth_session_keys {user_id, session_pub, scope:session_scope,
                              expires_at:session_expires_at, last_nonce:0}
    return {
      access_token: jwt(user.id),
      session_id:   auth_session_keys.id,
      init_username: user.init_username
    }
    Set-Cookie: refresh_token=<rotating>; HttpOnly; Secure; SameSite=Lax
```

First successful `/auth/verify` also triggers Flow 1 (wake) on the next user-scoped request. Note: `users.wallet_address` (auth identity) and `user_vms.wallet_address` (on-chain signing) are **different** addresses.

## 8a. Session-key authorized action

Used for every state-changing request after connect. No wallet popup.

```
client builds request:
  body    = <json>
  body_hash = sha256(body)
  nonce   = monotonic_counter++    # client-side
  canon   = json({method, path, body_sha256:body_hash,
                  session_id, nonce}, sort_keys=True)
  sig     = base64(session_priv.sign(canon))

client → hub <METHOD> <path>
  Authorization: Bearer <jwt>
  X-Session-Id: <session_id>
  X-Session-Nonce: <nonce>
  X-Session-Sig:   <sig>
  body: <json>

hub (require_session_key dep):
  user  = get_current_user(jwt)
  sess  = SELECT * FROM auth_session_keys
          WHERE id=? AND user_id=user.id AND revoked_at IS NULL
            AND expires_at > now()
  assert sess
  assert int(X-Session-Nonce) > sess.last_nonce
  canon = json({method, path, body_sha256:sha256(raw_body),
                session_id, nonce:int(X-Session-Nonce)}, sort_keys=True)
  assert verify_sess_sig(sess.session_pub, canon, X-Session-Sig)
  UPDATE auth_session_keys SET last_nonce=? WHERE id=sess.id
  proceed
```

Expired or revoked session → 401 `AUTH_REQUIRED`; client prompts a fresh wallet connect.

## 9. Indexer pull sync (hub → user-server, 30min)

```
hub cron @ */30 * * * *:
  FOR each vm WHERE status='running':
    since_ts = max(created_at) FROM indexer_tx_mirror WHERE user_id = vm.user_id
    rows = GET user_server /hub/indexer/since?ts={since_ts}
    bulk INSERT indexer_tx_mirror
```

Plus a **pre-drain flush** (Flow 6) guarantees no data loss when VM sleeps.

## 10. Marketplace install

```
client → hub POST /api/v1/marketplace/{id}/install
  hub:
    LOAD marketplace_strategy.code_blob
  hub proxy → user-server POST /strategies {source:'marketplace', marketplace_id, code_blob, name}
    user-server:
      INSERT strategies
      code runs under RestrictedPython at tick time (not now)
    return strategy
```

## 11. Marketplace report

```
client → hub POST /api/v1/marketplace/{id}/report {reason}
  hub:
    INSERT marketplace_report (UNIQUE(strategy_id, reporter_id))
    UPDATE marketplace_strategy.reports++
    IF reports >= 3 AND most recent 3 reports within 7 days:
      UPDATE strategy SET status='under_review'
      notify admin
```

Delist is a manual admin action.

## 12. Kill switch

```
client → hub POST /api/v1/u/agents/stop-all
  hub proxy → user-server POST /agents/stop-all
    user-server stops all agents, waits for drain, returns count
```

Credit halt (Flow 5) uses the same user-server path (`/hub/halt`).

## Edge cases

| Scenario | Handling |
|----------|----------|
| VM wake fails 3× in a row | mark vm.status='error', alert, return `VM_UNAVAILABLE` to client |
| Chain tx stuck / reverted | user-server retries ≤3× with gas bump; on final failure logs WARN; indexer row written with `status=failed` (future schema) |
| Agent container crash | docker restart policy `on-failure:3`; user-server re-POSTs `/start` on detection |
| User-server crash | VM auto-restart; hub re-proxies on next client request (transient 503) |
| Pyth feed timeout | agent skips tick, logs warn, keeps position |
| Marketplace code violates sandbox | RestrictedPython raises → agent logs error, falls back to default momentum strategy |

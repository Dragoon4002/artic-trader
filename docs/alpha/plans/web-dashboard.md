# Plan — Web Dashboard

Only client interface for alpha. Next.js 15, bun, shadcn/ui, Tailwind v4 (already scaffolded at `/clients/web/`). Alpha replaces current marketing-only site with a real dashboard gated behind auth.

## Route map

| Path | Auth | Purpose |
|------|------|---------|
| `/` | public | landing (keep existing) |
| `/connect` | public | single "Connect Wallet" button via InterwovenKit; signs nonce + session-key auth; first-time connect also provisions VM |
| `/app` | user | redirect based on onboarding state |
| `/app/onboarding` | user | add first LLM key, create first agent |
| `/app/agents` | user | grid of user's agents with live status |
| `/app/agents/new` | user | create-agent wizard |
| `/app/agents/[id]` | user | detail: live status, trade table, log stream, controls |
| `/app/strategies` | user | list installed + authored + upload editor |
| `/app/marketplace` | user | browse, install, publish, report |
| `/app/marketplace/[id]` | user | strategy detail + code preview |
| `/app/credits` | user | balance, ledger, topup (alpha: admin-only) |
| `/app/indexer` | user | tx explorer (own + cross-user) |
| `/app/settings` | user | API keys, session list, logout, `.init` claim banner |
| `/docs/*` | public | keep existing MDX docs |

## Alpha feature set

### Authentication (wallet connect — InterwovenKit)
- `@initia/interwovenkit-react` wraps the app; single "Connect Wallet" button on `/connect`
- Flow:
  1. `wallet.connect()` → `{address, chain, pubkey}`
  2. Generate ephemeral session keypair in memory (never persisted)
  3. `POST /auth/nonce {address, chain}` → server builds canonical message binding nonce + session_pub + expires
  4. `wallet.signArbitrary(message)` → single popup; returns `signature`
  5. `POST /auth/verify {...}` → `{access_token, session_id, init_username}` + httpOnly refresh cookie
- Access token + session private key both held in memory; session private key is **never** persisted (lost on tab close → user reconnects)
- Auto-refresh on 401 with refresh cookie; on refresh failure → redirect `/connect`
- No password reset, no email — identity is the wallet
- Tab-sync: BroadcastChannel shares access_token across tabs; session private key is per-tab (acceptable: first tab holds the key, others get one at their own connect)

### Signed-request client
`signedFetch(method, path, body)` helper wraps `fetch` for state-changing calls:
```ts
const nonce = monotonicCounter++;                       // per session, in-memory
const body_sha256 = sha256hex(JSON.stringify(body));
const canon = JSON.stringify({ method, path, body_sha256, session_id, nonce },
                              /* sort keys */);
const sig = base64(sessionPriv.sign(canon));
return fetch(path, {
  method, body: JSON.stringify(body),
  headers: {
    Authorization: `Bearer ${jwt}`,
    "X-Session-Id":   session_id,
    "X-Session-Nonce": nonce.toString(),
    "X-Session-Sig":  sig,
    "Content-Type":   "application/json",
  },
});
```
Apply to: create/start/stop/delete/edit agent, kill-switch, LLM key write, strategy upload, marketplace publish/install/report, logout.

### Identity display (.init)
`shortenAddr(addr)` helper returns `init1xy…4k9p`. Everywhere a user is shown:
```ts
const display = user.init_username ?? shortenAddr(user.wallet_address);
```
Sites: top-nav user chip, leaderboard rows, marketplace publisher, agent detail owner, settings. `.init` resolution is best-effort — if name service is down at login, `init_username` is `null` and fallback applies. A passive banner on settings page links to the `.init` registration site when `init_username` is null.

### Onboarding
- Post-signup: guided 3-step flow
  1. Add LLM API key (provider select + key input; encrypted client-side optional, server-side mandatory)
  2. Choose strategy source (built-in / marketplace / authored)
  3. Create first agent (symbol + risk params + LLM + strategy pool)
- Skippable, but dashboard shows reminder cards until all three done

### Agents
- Grid view: card per agent
  - Status badge: stopped / starting / alive / stopping / error / halted (credits)
  - Live price (Pyth WS), position side, unrealised PnL, strategy, LLM model
  - Controls: start, stop, delete, view
  - "Group" toolbar: start-all, stop-all (kill switch)
- Detail view:
  - Live status (WS)
  - Trade history table (sortable by open_at, pnl, size)
  - Log stream (WS, tail-style, filter by level)
  - PnL chart (Recharts)
  - Config panel (read-only while alive; editable when stopped)
- Create wizard:
  - Symbol (dropdown of 27 Pyth feeds)
  - Amount USDT, leverage (1-10), TP %, SL %, poll seconds, supervisor interval
  - LLM provider + model
  - Strategy pool (multi-select from installed)
  - Paper/live toggle — alpha forces paper

### Strategies
- Installed list: name, source badge (builtin/marketplace/authored), delete
- Authored editor: Monaco editor, Python syntax, RestrictedPython lint hint, save → user-server
- Publish-to-marketplace button on authored strategies

### Marketplace
- Public feed: sort by installs / recent / reports
- Detail page: description, code preview, install count, report button
- Publish flow: metadata + code blob → hub
- Report: modal with reason textarea

### Credits
- Header widget: balance_ah with color state (green > 10, amber 1-10, red < 1, grey halted)
- Ledger table: delta, reason, agent, timestamp

### Indexer explorer
- Filters: user, agent, kind, min_amount, date range
- Row = tx_hash (copy), kind, amount, tags, block, created_at
- "My txs" and "All users" tabs

### Cold-wake UX
- Hub may return 202 `VM_WAKING` with `Retry-After`
- Client shows full-screen "Warming up…" shimmer for ≤10s
- Exponential retry 500ms → 1s → 2s → 4s; fail on 15s
- Banner persists for any request during wake; other tabs share via BroadcastChannel

### Notifications (in-app only for alpha)
- Credits threshold (25%, 10%, 0%)
- Agent halted
- Marketplace strategy delisted
- WebSocket via a single persistent `/ws/notifications`

## Tech choices

- Wallet: `@initia/interwovenkit-react` (locked — required Initia stack integration)
- Session key curve: secp256k1 or ed25519 (pick in `lib/session.ts`); library = `@noble/curves`
- State: server components + React Query for data fetching
- WebSocket: single `useWebSocket` hook with reconnect/backoff; subscription multiplexed by channel id
- Charts: Recharts (PnL line), lightweight
- Code editor: `@monaco-editor/react`
- Form: react-hook-form + zod schemas mirroring hub API
- Auth: httpOnly refresh cookie + session-key signature on mutations (no CSRF needed — signature binds method+path+body)
- API client: typed fetch wrapper in `lib/api.ts` + `signedFetch` in `lib/session.ts`

## File structure additions

```
clients/web/
├── app/
│   ├── (auth)/
│   │   └── connect/page.tsx        # single Connect Wallet button; nonce → sign → verify
│   ├── app/
│   │   ├── layout.tsx              # authed shell, credits widget, nav, .init chip
│   │   ├── page.tsx                # redirect
│   │   ├── onboarding/page.tsx
│   │   ├── agents/
│   │   │   ├── page.tsx
│   │   │   ├── new/page.tsx
│   │   │   └── [id]/page.tsx
│   │   ├── strategies/page.tsx
│   │   ├── marketplace/
│   │   │   ├── page.tsx
│   │   │   └── [id]/page.tsx
│   │   ├── credits/page.tsx
│   │   ├── indexer/page.tsx
│   │   └── settings/page.tsx       # .init banner when unregistered
├── components/
│   ├── providers/
│   │   └── interwovenkit.tsx       # InterwovenKit provider wrapper
│   ├── dashboard/
│   │   ├── agent-card.tsx
│   │   ├── log-stream.tsx
│   │   ├── pnl-chart.tsx
│   │   ├── credits-widget.tsx
│   │   ├── warming-up.tsx
│   │   ├── user-chip.tsx           # .init || shortenAddr
│   │   └── kill-switch.tsx
│   └── marketplace/
│       ├── strategy-card.tsx
│       ├── code-preview.tsx
│       └── report-dialog.tsx
├── lib/
│   ├── api.ts
│   ├── auth.ts                     # connect, verify, refresh
│   ├── session.ts                  # session keypair, signedFetch, monotonic nonce
│   ├── identity.ts                 # shortenAddr helper
│   ├── ws.ts
│   └── schemas.ts
```

## Out of scope (alpha)

- Mobile layout polish (basic responsive only)
- Dark/light toggle (dark-only alpha)
- i18n
- Paid topup UI
- Team/org features
- Notification preferences page
- 2FA

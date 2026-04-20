# credits/ — Phase 4 stub

See `docs/alpha/plans/hub.md` §Credits debit cron. Lands on a follow-up branch.

Target contents:
- `service.py` — grant, debit, halt
- `cron.py` — per-minute debit loop
- `router.py` — `/credits`, admin `/credits/grant`

Schema: `credits`, `credit_ledger` tables per `docs/alpha/data-model.md`.

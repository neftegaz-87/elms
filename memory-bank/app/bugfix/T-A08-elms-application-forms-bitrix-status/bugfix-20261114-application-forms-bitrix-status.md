# BUGFIX — application forms and Bitrix status

## Scope

Closed BF-001, BF-002, and BF-003 in the single APP BUGFIX session.

## Fixes

- BF-001: repaired public `/apply` and `/apply/legal` runtime rendering and asset registration.
- BF-002: restored the public form entry path used by `submit_application`.
- BF-003: reconciled the methodologist workspace shortcut with `/app/elms-learning`.

## Verification

- Evidence file: `browser-artifacts/browser-evidence.json`
- Evidence timestamp: `2026-11-14T02:23:51Z`
- Combined targeted regression: `35 passed`.
- Browser smoke and application probe passed; `/apply`, `/apply/legal`, and `/apply/status` returned HTTP 200 with typed route, submit, and status outcomes recorded.

All queue items are terminal and the queue verification status is `pass`.

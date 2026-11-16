# Context sync — T-A07-elms-b2b-org-keycloak-provisioning

EPIC_ID: T-A07-elms-b2b-org-keycloak-provisioning
ROLE: app
QA: memory-bank/app/qa/T-A07-elms-b2b-org-keycloak-provisioning/qa-20261113-b2b-access.yaml
ALLOW WRITE:
  - memory-bank/techContext.md
  - memory-bank/productContext.md
  - memory-bank/systemPatterns.md
  - memory-bank/projectbrief.md
  - memory-bank/app/context-sync/T-A07-elms-b2b-org-keycloak-provisioning/sync-20261113-b2b-org-keycloak-provisioning.md

**Дата:** 2026-11-13  
**Session ID:** `session-485cb245c505`  
**Статус:** done  
**Force:** no

## Evidence used

| Source | Evidence |
|--------|----------|
| QA pass | `qa-20261113-b2b-access.yaml`, `verdict: pass`, `checklist_sha256: d7c9b4376f381ceabe5b051466792a3ae5a065bb9e733466f366a8859da9f22c`; required `coverage_map`, `review`, `test_audit`, `browser` and `retro` present; `issues`, `blockers` and `fix_plan` empty |
| Verify gate | QA artifact records `verify-qa PASS`; live boundary accepted for this session |
| Full suite | `./bin/pytest -q --tb=line` — 205 passed, 9 skipped, 5 subtests passed |
| Targeted behavior | Access/SSO suite — 49 passed, 3 skipped; provider failure, permissions, idempotent re-invite and reconciliation covered |
| Runtime/browser | Keycloak discovery/login/authorization, `/app/elms-access`, organization/invite API, SMTP-captured `UPDATE_PASSWORD` and invited-user login passed; console/request/http errors empty |
| Sunset/SOT | No enabled Yandex provider or `kc_idp_hint` runtime dependency; remaining matches are reviewed migration aliases/data, tooling or negative assertions |
| Plan bounded scope | `memory-bank/app/plan/T-A07-elms-b2b-org-keycloak-provisioning/md/plan.md` — `Context consumed` and `Technology axiom (replace-not-wrap)` |
| Root canon | `memory-bank/techContext.md`, `memory-bank/productContext.md`, `memory-bank/systemPatterns.md`, and absent `memory-bank/projectbrief.md` |

## Root canon reconciliation

| Path | Action | Real diff |
|------|--------|-----------|
| `memory-bank/techContext.md` | updated | Added the as-built B2B access surface, Keycloak Admin provisioning contract, Organization/User Permission boundary, Keycloak-only runtime/Yandex migration boundary, T-A07 evidence and test results. |
| `memory-bank/productContext.md` | updated | Recorded T-A07 as a completed B2B organization, Company Admin, invite-to-password-to-login vertical slice; clarified T-B03 as legacy foundation and preserved T-A08/T-A09 non-goals. |
| `memory-bank/systemPatterns.md` | updated | Reconciled Central Identity to Keycloak-only runtime and added B2B Organization scope plus typed, fail-closed, idempotent invite provisioning patterns. |
| `memory-bank/projectbrief.md` | no-op | File is absent from the root canon inventory; no file was created. |

## Result

- `ELMS Organization` / membership / `ELMS Invite Log`, Company Admin scope and canonical access methods are now represented in root canon.
- Invite success is documented as requiring durable Frappe state, Keycloak provisioning and `UPDATE_PASSWORD`; provider failure is fail-closed, re-invite is idempotent, and passwords are not returned.
- Keycloak-only runtime and migration-only Yandex compatibility are recorded from accepted live/browser evidence.
- No product vision/phases/roadmap, plan/decompose/implement, production code or unrelated files were changed.

## QA retro

- missed defect: `tabUser` reconciliation race and the direct access route were found and fixed during QA.
- redundant gate: none.
- flaky test: none.
- next-cycle change: Keep typed live/browser artifacts current when changing SSO or Desk routing.


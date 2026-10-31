# Context sync: T-A01-elms-keycloak-login-ui

- `EPIC_ID`: `T-A01-elms-keycloak-login-ui`
- `ROLE`: `app`
- `QA`: `memory-bank/app/qa/T-A01-elms-keycloak-login-ui/qa-20261029-login-ui.yaml`
- `ALLOW WRITE`: `memory-bank/techContext.md`, `memory-bank/productContext.md`, `memory-bank/systemPatterns.md`, `memory-bank/projectbrief.md` (только доказанное изменение), `memory-bank/app/context-sync/T-A01-elms-keycloak-login-ui/sync-20261030-keycloak-login-ui.md`
- `SESSION_ID`: `session-7fce901b6921`

## Evidence basis

- QA verdict: `pass`; required `coverage_map`, `review`, `test_audit`, `browser` and `retro` sections are present.
- QA lanes: 65 backend tests passed, `bench build --app elms` passed, browser QA passed with live computed styles, and live smoke passed with typed HTTP evidence.
- Runtime evidence: `browser-artifacts/browser-evidence.json` confirms one Keycloak control, no direct Yandex control, CSS delivery, `44px`/`3px`/`rgb(13, 76, 211)` computed style; `docs/reports/sso-browser-api-trace.json` confirms `JRN-SSO-001`, `JRN-SSO-001A`, `JRN-SSO-001B` and no direct Frappe-to-Yandex call.
- Bounded plan context: `Context consumed` and the step contract identify the stock Frappe login surface, scoped CSS, Keycloak broker and live-smoke boundary. No separate `Technology axiom` section/key exists in the allowed plan files.

## Root canon diff

- `memory-bank/techContext.md` — updated the sync date; recorded the stock `/login` ownership, `web_include_css` asset boundary, computed-style evidence, T-A01 QA/build/browser/live results, broker journeys, and the explicit interactive-Yandex `not_run` boundary.
- `memory-bank/productContext.md` — added the delivered T-A01 login-UI wedge and its observed browser/live acceptance evidence.
- `memory-bank/systemPatterns.md` — added the stock-login ownership, Frappe CSS-cascade, computed-style acceptance, and Keycloak identity-boundary patterns grounded in the QA evidence.
- `memory-bank/projectbrief.md` — no-op: the allowed path does not exist and no proven change can be applied.

## QA retro

- missed defect: CSS stylesheet ordering in Frappe: `login.bundle.css` is included via `head_include` after `head.html`, overriding equal-specificity selectors from `web_include_css`.
- redundant gate: none.
- flaky test: none.
- next-cycle change: Always test computed styles in the actual browser via Playwright rather than relying solely on static CSS token text assertions.

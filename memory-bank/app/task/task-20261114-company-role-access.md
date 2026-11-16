---
execution: direct-ad-hoc
title: Company Admin role and access management
date: 2026-11-14
status: completed
---

## Intent

Make the access boundary explicit: the global `Settings` workspace and Frappe
Permission Manager remain platform-only, while `ELMS Company Admin` gets a
separate company-scoped page to invite staff, assign internal role profiles,
and disable accounts.

## Root cause / contract impact

The current B2B page is platform-only and the current invite API supports only
learner and company-admin profiles. There is no company-scoped role-management
surface. Add a server-owned organization context, allow only company profiles
for Company Admin, and keep global roles/DocPerm inaccessible.

## Files

- `elms/elms/access/api.py`
- `elms/elms/desk/workspaces.py`
- `elms/elms/hooks.py`
- `elms/elms/operations/page/elms_company_access/elms_company_access.json`
- `elms/elms/public/js/elms-company-access-page.js`
- `elms/elms/public/js/desk-company-access.js`
- `elms/elms/public/css/desk-company-access.css`
- `elms/elms/tests/test_company_access.py`
- `elms/elms/tests/test_workspaces.py`
- `elms/elms/tests/test_access_invite.py`
- `elms/elms/tests/test_access_ui.py`

## Continuation: company-scoped integrations

The company cabinet also owns external integration credentials. A Company
Admin may configure only the integrations of the organization they belong to;
the platform singleton remains the platform-wide fallback only for users and
flows without an organization context. When an organization is known, a
missing company integration fails closed and never silently uses the platform
secret.

### Additional files allowlist

- `elms/elms/elms_core/doctype/elms_organization_integration/__init__.py`
- `elms/elms/elms_core/doctype/elms_organization_integration/elms_organization_integration.json`
- `elms/elms/elms_core/doctype/elms_organization_integration/elms_organization_integration.py`
- `elms/elms/integrations/api.py`
- `elms/elms/integrations/resolver.py`
- `elms/elms/integrations/bitrix_config.py`
- `elms/elms/applications/bitrix_leads.py`
- `elms/elms/ai/omniroute.py`
- `elms/elms/tenant.py`
- `elms/elms/hooks.py`
- `elms/elms/desk/workspaces.py`
- `elms/elms/hooks.py`
- `elms/elms/operations/page/elms_company_integrations/elms_company_integrations.json`
- `elms/elms/public/js/elms-company-integrations-page.js`
- `elms/elms/public/js/desk-company-integrations.js`
- `elms/elms/public/css/desk-company-integrations.css`
- `elms/elms/tests/test_company_integrations.py`
- `elms/elms/tests/test_integration_resolution.py`
- `elms/elms/tests/test_bitrix_config.py`
- `elms/elms/tests/test_ai_assistant.py`
- `elms/elms/tests/test_workspaces.py`
- `elms/elms/hooks.py`
- `memory-bank/product/modules.md`
- `memory-bank/architecture/integrations.md`
- `memory-bank/app/task/task-20261114-company-role-access.md`

## Lanes

- backend: required — API authorization, profile changes, disable operation,
  and invite profile validation.
- frontend: required — Desk page and workspace link.
- wire: required — page registration, role gate, and whitelist methods.
- browser/live_smoke: skipped — no live browser/deployment request in this task.

## Selected skills

None; repository-local Frappe patterns and existing ELMS access/cabinet
surfaces are the applicable implementation contract.

## Loop-safety preflight

`activeContext.md` is at DONE and exposes no active implementation shard; the
allowlist above does not overlap the completed T-A09 work shard.

## Evidence

### Company-scoped integrations continuation

- Added `ELMS Organization Integration` with organization ownership, LLM,
  Bitrix24 and Custom API fields; API responses expose only configured/not
  configured flags and never return Password values.
- Added `/app/elms-company-integrations` and the `Интеграции компании` shortcut
  in `Моя компания`. Company Admin gets only their organization; ELMS Admin can
  select any organization. Global `ELMS Integration Settings` remains in the
  platform-only Settings workspace.
- Added tenant query and document permission enforcement for direct reads and
  writes, not only UI filtering. Company Admin cannot read or edit another
  organization's integration record.
- LLM resolution uses the current user's organization first and fails closed
  when that company's integration is missing. Bitrix24 uses the same rule for
  authenticated company workflows; public/unscoped forms retain the global
  platform transport. Board webhook `BITRIX_WEBHOOK_URL` remains forbidden.
- Targeted tests: `python3 -m pytest -q
  elms/elms/tests/test_company_integrations.py
  elms/elms/tests/test_integration_resolution.py
  elms/elms/tests/test_bitrix_config.py elms/elms/tests/test_ai_assistant.py
  elms/elms/tests/test_applications_submit.py` — 40 passed.
- Final app suite: `python3 -m pytest -q elms/elms/tests` — 260 passed, 10
  skipped, 5 subtests passed.
- JSON, `py_compile`, and `node --check` passed for the new DocType, page and
  assets. `bench migrate`, clear-cache and backend/frontend restart completed.
- Runtime readback confirms the new DocType and page exist; Company Admin API
  readback returns only `Демонстрационный контур НефтеГаз`, while the foreign
  Company Admin returns only `ELMS Test Company`. A temporary disabled foreign
  integration was denied by `doc.has_permission("read")` and removed after the
  check. A temporary enabled LLM config was created through the Company Admin
  API, returned with `api_key_configured=true` and without the secret, then
  removed.

- Red test: `python3 -m pytest -q elms/elms/tests/test_company_access.py` —
  4 expected failures before the API existed.
- Targeted green: `python3 -m pytest -q elms/elms/tests/test_company_access.py
  elms/elms/tests/test_access_invite.py elms/elms/tests/test_access_model.py
  elms/elms/tests/test_access_ui.py elms/elms/tests/test_workspaces.py` — 38
  passed, 3 skipped.
- Final app suite: `python3 -m pytest -q elms/elms/tests` — 248 passed, 10
  skipped, 5 subtests passed.
- Syntax/wire: `python3 -m py_compile ...` for touched Python modules and
  `node --check` for both new JavaScript assets — passed.
- Live browser/deploy was not run; it was not required by this task.

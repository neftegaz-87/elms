---
execution: direct-ad-hoc
task: elms-access-tabs
date: 2026-11-16
status: completed
---

# ELMS Access: вкладки и выбор организаций

## Intent and root cause

На Desk `/app/elms-access` три операции (создать организацию, назначить
Company Admin, пригласить сотрудника) показаны одной длинной страницей.
После создания компании поле «Организация» в приглашении и назначении
Company Admin остаётся свободным текстовым вводом — существующие компании
не подгружаются, оператор вынужден помнить точное имя.

## Contract impact

- UI: одна страница `/app/elms-access`, три вкладки с одним активным действием.
- Machine input: `organization` для invite и assign остаётся строкой имени
  `ELMS Organization`; источник списка — существующий whitelist
  `elms.access.api.get_company_access_context` (поле `organizations`).
- После успешного `create_organization` списки организаций на вкладках
  invite/assign обновляются без перезагрузки Desk.
- Серверные методы `create_organization`, `assign_company_admin`,
  `invite_org_user` не меняют контракт ответа; права по-прежнему
  проверяются на сервере.

## Files allowlist

- `elms/elms/public/js/desk-access.js`
- `elms/elms/public/css/desk-access.css`
- `elms/elms/hooks.py`
- `elms/elms/tests/test_access_ui.py`
- `memory-bank/app/task/task-20261116-elms-access-tabs.md`

## Verification lanes

- required backend/contract: `timeout -k 10s 300s bin/pytest elms/elms/tests/test_access_ui.py -q --tb=line`
- required frontend syntax: `timeout -k 10s 300s node --check elms/elms/public/js/desk-access.js`
- required browser (parent): открыть `/app/elms-access`, проверить tablist и
  select организаций после создания компании
- skipped live_smoke: нет нового HTTP API и внешней интеграции

## Selected skills

- `tdd`
- `frontend-patterns`

## Loop-safety preflight

- `activeContext` epic `T-A09-elms-company-admin-cabinet` в состоянии DONE;
  пересечения allowlist с активным loop shard нет → direct-ad-hoc OK.
- Не трогаем `activeContext`, roadmap, plan/decompose, implement artifacts.

## Evidence

- backend/contract: `timeout -k 10s 300s bin/pytest elms/elms/tests/test_access_ui.py -q --tb=line` → 9 passed
- frontend syntax: `timeout -k 10s 300s node --check elms/elms/public/js/desk-access.js` → PASS
- browser (live Desk): `/app/elms-access` показывает tablist из трёх вкладок; на
  «Пригласить сотрудника» и «Назначить Company Admin» поле Организация —
  `<select>` с существующими компаниями из `get_company_access_context`
  (ELMS Test Company и QA-*); после создания организации список обновляется
  и UI переключает на вкладку invite
- assets: `desk-access.js?v=2`, `desk-access.css?v=2`

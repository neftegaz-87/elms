---
execution: direct-ad-hoc
date: 2026-11-02
role: APP
mode: TASK
slug: bitrix-elms-identity-export
---

# Bitrix → Yandex 360 → Keycloak export

## Intent

Read the Bitrix user directory and prepare a bounded identity handoff for ELMS:
the requested named users must be present, Bitrix source email must remain
available for reconciliation, Yandex email must be an explicit editable field,
and the Keycloak import must carry ELMS-compatible roles without inventing
Bitrix/CRM roles as product roles.

## Contract impact

Read-only Bitrix REST calls plus generated local CSV/JSON handoff artifacts.
No Bitrix, Yandex, Keycloak, Frappe, Docker, or production state is changed.
The export is treated as sensitive and is written below ignored `runtime/`.

## Files allowlist

- `memory-bank/app/task/task-20261102-bitrix-elms-identity-export.md`
- `runtime/exports/elms-bitrix-identity-20261102/bitrix-users-source.csv`
- `runtime/exports/elms-bitrix-identity-20261102/yandex-users-import.csv`
- `runtime/exports/elms-bitrix-identity-20261102/keycloak-users-import.csv`
- `runtime/exports/elms-bitrix-identity-20261102/email-mapping.csv`
- `runtime/exports/elms-bitrix-identity-20261102/export-manifest.json`

## Required lanes

- Bitrix read-only API discovery and paginated user export.
- Local CSV schema, UTF-8/BOM, delimiter, required-user presence, duplicate and
  email-mapping validation.
- Keycloak role compatibility check against ELMS product roles and current realm
  import conventions.

## Skipped lanes

- Frontend/build/browser: no UI or client assets are changed.
- Live HTTP smoke: no ELMS or Keycloak application code is changed.
- Bitrix write lane: forbidden for this export; only read methods are allowed.
- Yandex/Keycloak upload: external mutation requires a separate explicit request
  after the generated files are reviewed.

## Selected skills

- None; no workflow skill was selected by the APP task shard.

## Loop-safety preflight

The active loop context is BACK QA for `T-B09-elms-caddy-edge-cutover`; its
allowlisted files are edge-routing and cutover artifacts and do not overlap the
files above. Direct APP TASK must not modify `activeContext`, roadmap, plan,
implement artifacts, cursor files, or loop indexes.

## Evidence

- Read-only access established via operator webhook with `user_basic` and `user_brief` scopes.
- Bitrix user directory scanned: 92 active users extracted and paginated (0, 50, 100).
- Target users verified:
  - Андрей Ерохин (ID 274, aeroalgo@gmail.com) -> Login `erokhin.a`, ELMS Admin / admin.
  - Евгений Соколов (ID 240, sokolovavs13@yandex.ru) -> Login `sokolov.e`, ELMS LMS User / student, employee.
  - Ирина Видякина (Ведякина) (ID 82, ividakina002@gmail.com) -> Login `vidyakina.i`, ELMS Operations / employee.
  - Дополнительно включены руководители: Прошкина Т.В. (ID 12, Директор) -> Login `proshkina.t`, ELMS Admin; Стеклова А.В. (ID 5, Ведущий специалист УМО) -> Login `steklova.a`, ELMS Operations.
- Generated export artifacts in `runtime/exports/elms-bitrix-identity-20261102/`:
  1. `yandex-users-import.csv`: 92 rows in official Yandex 360 format (semicolon delimited, UTF-8 BOM, quoted fields, temporary passwords, `password_change_required=true`).
  2. `email-mapping.csv`: Complete correlation table linking `bitrix_id`, original `bitrix_email`, full name, position, departments, proposed `yandex_login`, `yandex_email_template`, and assigned ELMS & Keycloak roles.
  3. `keycloak-users-import.json`: Keycloak realm-compatible partial import with user profile, attributes (`bitrix_user_id`, `bitrix_source_email`), and role mappings.
  4. `bitrix-users-source.csv`: Raw source snapshot of all 92 active users.
  5. `export-manifest.json`: Summary metadata and priority targets list.
- No secrets or webhook tokens were recorded in logs or committed files.

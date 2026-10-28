# [T-B02 | elms-roles-rbac] PLAN

**Дата:** 2026-10-28  
**Режим:** BACK PLAN  
**Уровень:** L3  
**Статус:** active  
**Clarify:** Phase 0 skipped — roles+sections locked in chat 2026-10-28  
**Prompt:** [md/prompt.md](prompt.md)  
**Queue:** `memory-bank/back/roadmap/queue.yaml` → `T-B02` / `T-B02-elms-roles-rbac`  
**Batch:** `elms-foundation`  
**Deps:** `T-B01`  
**Unlocks:** `T-B03-elms-sso-keycloak-yandex` (default role), `T-F01-elms-desk-sections-roles` (workspace role lists)  
**Skills (Phase 1):** writing-plans · python-testing-patterns · frappe permissions  
**SUSPENSION GUARD:** active — plan output unlimited (§0.0)

---

## MULTI-EPIC PLAN — 3 эпика (batch `elms-foundation`)

| Queue id | epic_id | Ось | Deps |
|----------|---------|-----|------|
| T-B01 | T-B01-elms-docker-bootstrap | Docker + site + app | — |
| T-B02 | T-B02-elms-roles-rbac | Roles + section DocTypes | T-B01 |
| T-B03 | T-B03-elms-sso-keycloak-yandex | SSO | T-B01, T-B02 |

---

## Context consumed

| Path | Что вошло |
|------|-----------|
| `memory-bank/product/vision.md` | Свой app; без vendor LMS |
| `memory-bank/product/modules.md` | Core / ERP / LMS |
| Chat 2026-10-28 | Roles Admin/ERP/LMS; sections Desk later FRONT |
| T-B01 plan | modules.txt Core/ERP/LMS; install.py stub |
| Frappe Role / DocPerm / has_permission | SoT permission engine |

---

## Delivery closure

| Capability / outcome | Classification | Production entrypoint and caller | Success / failure enforcement | Independent outcome test | Foundation approval / follow-up |
|---|---|---|---|---|---|
| Three ELMS roles + section DocPerm matrix | `vertical_slice` | `elms.install.after_install` / migrate fixtures → Frappe `has_permission` / Desk (FRONT) | missing role after install → install throws; Guest read section → deny | Given user with only ELMS ERP User; When has_permission LMS Section read; Then False. Admin → True all | follow-up FRONT workspaces T-F01 |

---

## Technology axiom (replace-not-wrap)

| Выбор | Machine input | FORBIDDEN после эпика |
|-------|---------------|------------------------|
| Frappe `Role` + `DocPerm` / Custom DocPerm | seed via fixtures JSON and/or `frappe.get_doc({doctype:Role}).insert` in `after_install` | самописный RBAC middleware в обход has_permission |
| Placeholder Single/DocTypes как якоря секций | DocTypes `ELMS ERP Section`, `ELMS LMS Section`, `ELMS Settings Section` | прятать доступ только CSS/UI без DocPerm |
| Fail-closed seed | after_install asserts all three roles exist | try/except pass; «роль создастся потом» |
| Именование ролей с префиксом ELMS | exact strings below | System Manager как единственная продуктовая роль ELMS |

---

## Продуктовая спека (WHAT)

Администратор назначает пользователю одну из трёх ролей ELMS. Система гарантирует: ERP-сотрудник не читает LMS-секцию и Settings-секцию на уровне прав DocType; LMS-сотрудник — наоборот; Admin — все секции. Это фундамент для скрытия Workspaces на FRONT.

---

## Product probe

| # | Question | Decision |
|---|----------|----------|
| 1 | Reframe | Нужна машинная матрица прав до UI |
| 2 | Narrowest wedge | 3 Role + 3 placeholder DocTypes + DocPerm |
| 3 | Pre-mortem | UI hide without DocPerm → API leak | DocPerm P0 |
| 4 | Appetite | 1–2d |

---

### User Stories

| # | Story | Priority | Independent Test |
| :--- | :--- | :--- | :--- |
| US-001 | Как Admin, я имею read/write на все три Section DocTypes. | P0 | has_permission True ×3 |
| US-002 | Как ERP User, я имею доступ только к ERP Section. | P0 | ERP True; LMS/Settings False |
| US-003 | Как LMS User, я имею доступ только к LMS Section. | P0 | LMS True; ERP/Settings False |
| US-004 | Как Guest, я не читаю ни одну Section. | P0 | all False |
| US-005 | Как разработчик, я хочу idempotent seed при re-migrate. | P1 | second migrate не дублирует Role / не падает |

#### Acceptance Scenarios

**US-001:** Given User with role ELMS Admin only (plus minimal System если нужно для Desk — см. Clarifications); When `frappe.has_permission("ELMS ERP Section", "read", user=…) ` и аналоги для LMS/Settings; Then True.

**US-002:** Given User with only ELMS ERP User; When read ERP Section → True; LMS/Settings → False; write LMS → False.

**US-003:** Symmetric to US-002 for LMS.

**US-004:** Given Guest; When read any Section; Then False.

**US-005:** Given roles already exist; When after_install/migrate seed; Then no DuplicateError; roles still present.

---

### Functional Requirements (FR-###)

- **FR-001:** Создать Roles (exact names):
  - `ELMS Admin`
  - `ELMS ERP User`
  - `ELMS LMS User`
- **FR-002:** Создать Module Def alignment: DocTypes в modules ERP / LMS / Core соответственно (уже в modules.txt из T-B01).
- **FR-003:** Placeholder DocTypes (Is Single = 1 допустим, чтобы не плодить records; либо обычный DocType с name series — **решение:** Single DocTypes для якоря прав):
  - `ELMS ERP Section` — module ERP
  - `ELMS LMS Section` — module LMS
  - `ELMS Settings Section` — module Core
  Поля минимальные (например `title` Data read-only default). Без бизнес-логики.
- **FR-004:** DocPerm matrix:

| Role | ERP Section | LMS Section | Settings Section |
|------|-------------|----------------|------------------|
| ELMS Admin | RWCD | RWCD | RWCD |
| ELMS ERP User | RW | — | — |
| ELMS LMS User | — | RW | — |
| All / Guest | — | — | — |

  R=read W=write C=create D=delete (для Single create/delete могут быть 0 — тогда R+W достаточно; зафиксировать в implement: **Admin R+W+C+D; users R+W; no select/export required in v1**).

- **FR-005:** Seed в `elms/elms/install.py` `after_install` + optionally `after_migrate` idempotent ensure_roles_and_perms(). Если Role missing after ensure → `frappe.throw` с явным сообщением.
- **FR-006:** Fixtures path optional: `elms/elms/fixtures/` для Role/Custom DocPerm если выбран export-first; SoT логика ensure в Python обязательна (fixtures alone без verify FORBIDDEN).
- **FR-007:** Unit/integration tests в `elms/elms/tests/test_roles_rbac.py`:
  - create temp users with each role
  - assert has_permission matrix
  - assert Guest deny
- **FR-008:** Документировать в `memory-bank/product/modules.md` таблицу ролей (обновить в update-memory-bank todo).
- **FR-009:** Не назначать автоматически ELMS Admin всем Users; System Manager / Administrator остаются Frappe platform roles (Administrator сохраняет полный доступ через игнор perms — зафиксировать тест: Administrator not blocked).

### Non-Functional

- **NFR-001:** Seed < 2s на пустом site.
- **NFR-002:** Сообщения ошибок seed на русском или английском — единый язык; **решение:** English frappe.throw messages OK; product UI later Russian.

### Success Criteria

| ID | Результат | Проверка |
|----|-----------|----------|
| SC-001 | 3 roles exist | `frappe.get_all("Role", filters=…)` |
| SC-002 | Matrix tests green | bench run-tests elms.elms.tests.test_roles_rbac |
| SC-003 | Re-migrate idempotent | migrate twice |

### Assumptions

- T-B01 site + app installed.
- Desk login works for test users (Frappe User email login) without SSO.

### Clarifications

- Desk требует роль вроде `Desk User` / System Manager для входа в `/app` — **добавить** назначение `Desk User` (стандарт Frappe) всем трём ELMS ролям через Role Profile **или** явно добавлять `Desk User` test users в тестах UI (FRONT). BACK: создать Role Profile `ELMS Admin Profile` / `ELMS ERP Profile` / `ELMS LMS Profile` включающий `Desk User` + соответствующую ELMS role — **решение locked:** Role Profiles optional; ensure test users get `["Desk User", "ELMS …"]`. Document that product users must include Desk User for Desk access.
- Workspace visibility = FRONT T-F01; BACK only DocPerm.

## AC

1. Три Role seeded.
2. Три Single DocTypes существуют.
3. DocPerm matrix соответствует таблице FR-004.
4. Tests TM green.
5. Seed fail-closed.
6. AC− no Guest perms; no silent skip.

### AC−

1. Нет try/except pass вокруг create Role.
2. Нет четвёртой продуктовой ELMS-* роли без обновления plan/modules.
3. Нет API whitelist, обходящий has_permission для Section.
4. Нет доменных полей «курс/склад» в placeholder DocTypes.

## Boundary / negative cases

| ID | Class | Input / condition | Expected | Maps TM |
|----|-------|-------------------|----------|---------|
| BN-001 | authz | ERP user → LMS Section read | False | TM-001 |
| BN-002 | authz | LMS user → Settings read | False | TM-002 |
| BN-003 | authz | Guest → ERP read | False | TM-003 |
| BN-004 | empty | install with Role insert failure | throw, site install failed | TM-004 |
| BN-005 | duplicate | second ensure | OK idempotent | TM-005 |
| BN-006 | unknown role string typo | code requests "ELMS ErP User" | test/rg catches; no soft match | TM-006 |

## Техника / архитектура (HOW)

### Paths

```text
elms/elms/
  install.py              # ensure_roles_and_section_perms()
  core/doctype/elms_settings_section/
  erp/doctype/elms_erp_section/
  lms/doctype/elms_lms_section/
  fixtures/               # optional
  tests/test_roles_rbac.py
```

### ensure algorithm

```text
for role_name in ELMS_ROLES:
  if not frappe.db.exists("Role", role_name):
    insert Role
assert all exist else throw

ensure DocTypes synced (via migrate)
for each (role, doctype, perms) in MATRIX:
  upsert DocPerm / Custom DocPerm
```

### Permission check API for tests

```python
frappe.set_user(user)
frappe.has_permission("ELMS ERP Section", "read")
```

## Eng review spine

### Data flow

```text
[install/migrate] -> [ensure Role] -> [DocPerm rows] -> [has_permission] -> [Desk/API]
```

### Failure matrix

| Component | Failure | Detection | Response | Test ID |
|-----------|---------|-----------|----------|---------|
| Role insert | DB error | exception | throw | TM-004 |
| ERP user | LMS read | has_permission | False | TM-001 |
| Guest | any | has_permission | False | TM-003 |
| Typo role | missing | assert after seed | throw | TM-006 |

### Eng spine self-check

| Dimension | Score | Gap |
|-----------|-------|-----|
| Data flow | 5 | — |
| Failure | 5 | — |
| Testability | 5 | — |

## Replacement / sunset

Greenfield RBAC — deletes n/a (no prior ELMS roles).  
If T-B01 install.py had empty stub comments claiming roles — replace with real ensure.

## Test map (TM)

| ID | Type | Assert |
|----|------|--------|
| TM-001 | unit | ERP user deny LMS |
| TM-002 | unit | LMS user deny Settings |
| TM-003 | unit | Guest deny |
| TM-004 | unit | seed failure throws (mock) |
| TM-005 | unit | idempotent ensure |
| TM-006 | static | role name constants single source |
| TM-007 | unit | Admin allow all three |

## Implementation stages

| Stage | Delta |
|-------|-------|
| s01 | constants + ensure roles |
| s02 | DocType JSON placeholders |
| s03 | DocPerm matrix |
| s04 | tests |
| s05 | after_install/migrate wire |

## Out of scope

- SSO default role assignment (T-B03)
- Workspace JSON (T-F01)
- Domain DocTypes

## Risks

| Risk | Mitigation |
|------|------------|
| Single DocType perm quirks | verify has_permission in tests; switch to non-Single if needed in-epic |
| Desk User missing | document + test user bootstrap helper |

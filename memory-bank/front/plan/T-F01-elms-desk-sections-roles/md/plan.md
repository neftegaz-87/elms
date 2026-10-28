# [T-F01 | elms-desk-sections-roles] PLAN

**Дата:** 2026-10-28  
**Режим:** FRONT PLAN  
**Уровень:** L3  
**Статус:** active  
**Clarify:** Phase 0 skipped — Desk workspaces + SSO labels locked chat 2026-10-28  
**Prompt:** [md/prompt.md](prompt.md)  
**Queue:** `memory-bank/front/roadmap/queue.yaml` → `T-F01` / `T-F01-elms-desk-sections-roles`  
**Batch:** `elms-desk-shell`  
**Deps:** BACK `T-B02-elms-roles-rbac`, `T-B03-elms-sso-keycloak-yandex`  
**Unlocks:** future domain UI epics  
**Skills (Phase 1):** writing-plans · playwright-best-practices (smoke) · frappe Desk workspaces  
**SUSPENSION GUARD:** active — plan output unlimited (§0.0)

---

## MULTI-EPIC PLAN — FRONT batch `elms-desk-shell`

| Queue id | epic_id | Ось | Deps |
|----------|---------|-----|------|
| T-F01 | T-F01-elms-desk-sections-roles | Workspaces + SSO login affordances | T-B02, T-B03 |

Единственный FRONT эпик foundation; дальнейший UI product — отдельные batches.

---

## Context consumed

| Path | Что вошло |
|------|-----------|
| `memory-bank/product/vision.md` | Desk/Website later; свой app |
| Chat 2026-10-28 | Workspaces ERP/LMS/Settings; SSO Keycloak+Yandex UI |
| BACK T-B02 | Roles + Section DocTypes |
| BACK T-B03 | Social Login Key enable + redirects |
| Frappe Workspace doctype | `roles` child / public flags |
| Frappe `/login` template | social login buttons from Social Login Key |

---

## Delivery closure

| Capability / outcome | Classification | Production entrypoint and caller | Success / failure enforcement | Independent outcome test | Foundation approval / follow-up |
|---|---|---|---|---|---|
| Role-filtered Desk workspaces | `vertical_slice` | Desk sidebar `/app` loads Workspace list filtered by User roles | ERP User seeing LMS workspace link = FAIL | Given ERP User login; When open Desk; Then sidebar has ERP, not LMS/Settings | domain UI later |
| SSO login affordances | `vertical_slice` | `/login` social buttons | enabled providers without readable label = FAIL (must set provider_name/icon) | Given enabled keys; When GET /login; Then texts Keycloak and Яндекс visible | — |

---

## Technology axiom (replace-not-wrap)

| Выбор | Machine input | FORBIDDEN после эпика |
|-------|---------------|------------------------|
| Frappe Workspace fixtures in app `elms` | `elms/elms/fixtures/workspace.json` or Module Onboarding + Workspace docs via ensure | Vue SPA sidebar dual SoT |
| Visibility via Workspace roles | child table roles = ELMS_* | hide-only CSS; client-only filter without Workspace.roles |
| Stock Frappe login page | Social Login Key `provider_name`, `icon` | rewrite `www/login.py` template fork without need; custom React login |
| RU labels for SSO | provider_name / title «Яндекс», «Keycloak» | English-only cryptic client_id as button text |

---

## Продуктовая спека (WHAT)

После логина сотрудник видит в левой навигации Desk только свои разделы: учебный контур (LMS), операционный ERP или оба + Settings для Admin. На странице входа понятно, что можно войти через корпоративный Keycloak или Яндекс. Заглушки разделов честно говорят, что домен ещё не реализован («Скоро»), но навигация и права уже рабочие.

---

## Product probe

| # | Question | Decision |
|---|----------|----------|
| 1 | Reframe | Нужна видимая карта ролей до домена |
| 2 | Narrowest wedge | 3 Workspaces + login labels |
| 3 | Pre-mortem | Workspace without roles → все видят всё | roles required |
| 4 | Appetite | 1–2d |

---

### User Stories

| # | Story | Priority | Independent Test |
| :--- | :--- | :--- | :--- |
| US-001 | Как ELMS Admin, я вижу Workspaces ERP, LMS и Settings. | P0 | sidebar contains three |
| US-002 | Как ELMS ERP User, я вижу только ERP. | P0 | LMS/Settings absent |
| US-003 | Как ELMS LMS User, я вижу только LMS. | P0 | ERP/Settings absent |
| US-004 | Как гость на `/login`, я вижу кнопки Keycloak и Яндекс когда SSO enabled. | P0 | button text/icon assert |
| US-005 | Как пользователь раздела, я открываю workspace и вижу link на Section DocType или page «Скоро». | P1 | click → form/list/page 200 |

#### Acceptance Scenarios — US-001

- **Given:** User roles include `Desk User` + `ELMS Admin`  
- **When:** open `/app`  
- **Then:** sidebar/workspace switcher shows ERP, LMS, Settings

#### Acceptance Scenarios — US-002

- **Given:** `Desk User` + `ELMS ERP User` only (no Admin/LMS)  
- **When:** `/app`  
- **Then:** ERP visible; LMS and Settings not listed

#### Acceptance Scenarios — US-003

- Symmetric for LMS User.

#### Acceptance Scenarios — US-004

- **Given:** Social Login Key keycloak+yandex enable_social_login=1  
- **When:** GET `/login`  
- **Then:** visible controls/labels containing Keycloak and Яндекс (case-insensitive OK for Keycloak)

#### Acceptance Scenarios — US-005

- **Given:** ERP User  
- **When:** open ERP workspace shortcut to ELMS ERP Section  
- **Then:** permitted page; LMS Section URL → PermissionError/403 Desk message (not empty 200 with data)

---

### Functional Requirements (FR-###)

- **FR-001:** Workspace documents (fixtures or `ensure_workspaces()` in install/migrate — FRONT owns JSON content; may live in app called from after_migrate shared with BACK):

| Workspace name | Title | Roles | Content |
|----------------|-------|-------|---------|
| `ERP` | ERP | ELMS Admin, ELMS ERP User | Link/card → ELMS ERP Section; short description «Операционный контур (скелет)» |
| `LMS` | LMS | ELMS Admin, ELMS LMS User | Link → ELMS LMS Section; «Учебный контур (скелет)» |
| `Settings` | Settings | ELMS Admin | Link → ELMS Settings Section; «Настройки ELMS» |

- **FR-002:** Workspace `public` = 0; not visible to Guest.
- **FR-003:** Icons: use standard Frappe icons (e.g. `organization`, `education`, `setting`) — no custom design system.
- **FR-004:** SSO Social Login Key display:
  - Keycloak: provider_name / label `Keycloak` (or «Войти через Keycloak» if field allows); icon URL or stock
  - Yandex: `Яндекс` / «Войти через Яндекс»
  - Ensure FRONT verify strings after BACK ensure — if BACK leaves English-only, FRONT patch ensure display fields in same app module `elms/elms/sso/display.py` or fixtures update **in this epic**.
- **FR-005:** Seed three demo Users (optional, documented) for smoke:
  - `admin.elms@example.com` → Admin+Desk
  - `erp.elms@example.com` → ERP+Desk
  - `lms.elms@example.com` → LMS+Desk  
  Passwords only in `.env.dev` / site script, not committed. Script `scripts/seed-desk-smoke-users.py` or bench console snippet in README.
- **FR-006:** Playwright smoke (preferred) under `elms/elms/tests/playwright/` or repo `e2e/`:
  - login password users
  - assert sidebar workspace names
  - login page SSO text (providers enabled — may mock Social Login Key in test site)
  If Playwright infra heavy for v1: **manual AC checklist** required in README + plan; mark SC accordingly. **Решение:** ship manual checklist P0; Playwright P1 if time — but plan must include checklist file `memory-bank/front/plan/T-F01-elms-desk-sections-roles/md/manual-ac.md`.
- **FR-007:** No custom CSS theme epic; stock Desk OK.
- **FR-008:** Russian UI strings for workspace titles/descriptions as in table (ERP/LMS/Settings titles may stay Latin module codes with Russian description).

### Non-Functional

- **NFR-001:** Sidebar load не хуже stock Desk.
- **NFR-002:** Strings без эмодзи и marketing clutter.

### Success Criteria

| ID | Результат | Проверка |
|----|-----------|----------|
| SC-001 | Admin sees 3 | manual/playwright |
| SC-002 | ERP only ERP | manual/playwright |
| SC-003 | LMS only LMS | manual/playwright |
| SC-004 | SSO labels | /login |
| SC-005 | manual-ac.md exists | file |

### Assumptions

- BACK roles + Section DocTypes installed.
- BACK SSO keys can be enabled on test site.
- Users have Desk User role.

### Clarifications

- Workspace ensure may share `elms.install` — FRONT plan owns UX content; coordinate single ensure function to avoid duplicate Workspace inserts (idempotent by name).
- Settings workspace ≠ Frappe System Settings only — points to ELMS Settings Section placeholder first.

## AC

1. Three workspaces with correct roles.
2. Role matrix visible in Desk sidebar.
3. SSO labels Keycloak + Яндекс on login when enabled.
4. Placeholder links work under perm.
5. manual-ac.md checklist complete.
6. AC− no SPA; no CSS-only hide.

### AC−

1. Нет Vue/React login app.
2. Нет Workspace без roles «для всех».
3. Нет показа LMS workspace ERP User.
4. Нет зависимости от ERPNext Desk pages.

## Boundary / negative cases

| ID | Class | Input / condition | Expected | Maps TM |
|----|-------|-------------------|----------|---------|
| BN-001 | authz | ERP user open LMS workspace URL direct | deny / not in list | TM-001 |
| BN-002 | authz | Guest /app | login redirect | TM-002 |
| BN-003 | empty | SSO disabled | no Yandex/Keycloak buttons | TM-003 |
| BN-004 | misconfig | workspace fixture missing roles | ensure test FAIL | TM-004 |
| BN-005 | duplicate | migrate twice | one workspace each name | TM-005 |

## Техника / архитектура (HOW)

### Navigation model

```text
User roles
  -> Frappe Desk boots
  -> filters Workspace by roles child
  -> sidebar shows ERP | LMS | Settings subset
  -> link -> Single DocType form ELMS * Section
```

### Login model

```text
GET /login
  -> Frappe template lists enabled Social Login Key
  -> buttons show provider_name + icon
```

### Files

```text
elms/elms/
  desk/
    workspaces.py          # ensure_workspaces()
  fixtures/workspace.json  # optional export
  public/images/           # optional yandex/keycloak icons
scripts/seed-desk-smoke-users.py
memory-bank/front/plan/T-F01-elms-desk-sections-roles/md/manual-ac.md
```

### hooks

```python
after_migrate = [
  "elms.install.after_migrate",  # includes workspaces ensure
]
```

Coordinate with BACK ensure order: roles → doctypes → social keys → workspaces.

## Eng review spine

### Data flow

```text
[fixtures/ensure] -> [Workspace + roles] -> [Desk sidebar]
[Social Login Key display fields] -> [/login buttons]
```

### Failure matrix

| Component | Failure | Detection | Response | Test ID |
|-----------|---------|-----------|----------|---------|
| Workspace roles | missing | ERP sees LMS | FAIL AC | TM-001 |
| Guest | /app | redirect login | OK | TM-002 |
| SSO off | buttons | absent | OK | TM-003 |
| ensure | dup | idempotent | OK | TM-005 |

### Eng spine self-check

| Dimension | Score | Gap |
|-----------|-------|-----|
| Data flow | 5 | — |
| Failure | 4 | — |
| Testability | 4 | playwright P1 |

## Replacement / sunset

| Устаревает | Замена |
|------------|--------|
| Empty Desk with only stock workspaces | ELMS ERP/LMS/Settings |
| Unlabeled social client_id buttons | RU/clear provider_name |

deletes: n/a (greenfield workspaces).

## Test map (TM)

| ID | Type | Assert |
|----|------|--------|
| TM-001 | manual/e2e | ERP user no LMS |
| TM-002 | manual | Guest redirect |
| TM-003 | manual | SSO off no buttons |
| TM-004 | unit | workspace has roles |
| TM-005 | unit | idempotent ensure |
| TM-006 | manual | Admin three sections |
| TM-007 | manual | SSO labels |

## Implementation stages

| Stage | Delta |
|-------|-------|
| s01 | ensure_workspaces + role links |
| s02 | shortcuts to Section DocTypes |
| s03 | SSO display names/icons |
| s04 | smoke users script |
| s05 | manual-ac.md (+ optional playwright) |

## Out of scope

- Domain forms, kanban, reports
- Design tokens / dark theme sync
- Mobile responsive redesign
- Custom App launcher branding beyond workspace

## Risks

| Risk | Mitigation |
|------|------------|
| Frappe version Workspace schema fields differ | match v15 Workspace JSON from etalon wiki/crm samples |
| Sidebar caching | clear-cache after migrate in docs |
| SSO buttons need enable | document dependency on T-B03 conf |

## Manual AC outline (to be written as manual-ac.md in IMPLEMENT)

1. Login admin.elms → see ERP, LMS, Settings.  
2. Login erp.elms → see only ERP; open section OK; hit LMS URL deny.  
3. Login lms.elms → only LMS.  
4. Logout → /login shows Keycloak and Яндекс when env set.  
5. Disable provider → button disappears after cache clear.

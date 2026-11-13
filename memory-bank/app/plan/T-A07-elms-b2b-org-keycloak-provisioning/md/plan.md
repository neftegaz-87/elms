# [T-A07 | elms-b2b-org-keycloak-provisioning] PLAN

**Дата:** 2026-11-13  
**Режим:** APP PLAN → APP DECOMPOSE → APP IMPLEMENT → APP QA  
**Уровень:** L2  
**Статус:** planned  
**Clarify:** [memory-bank/app/clarify/clarify-20261113-elms-b2b-roles-keycloak-provisioning.md](../../../clarify/clarify-20261113-elms-b2b-roles-keycloak-provisioning.md)  
**Prompt:** [md/prompt.md](prompt.md) — outcome SoT  
**Queue:** `memory-bank/app/roadmap/queue.yaml` → `T-A07` / `T-A07-elms-b2b-org-keycloak-provisioning`  
**Batch:** `elms-b2b-access`  
**Deps:** `T-B02-elms-roles-rbac`, `T-B03-elms-sso-keycloak-yandex`, `T-A01-elms-keycloak-login-ui`  
**Follow-up in cut:** `T-A08-elms-application-forms-bitrix-status`, `T-A09-elms-company-admin-cabinet`  
**SUSPENSION GUARD:** active — plan output unlimited (§0.0)

---

## Решение

Один mixed vertical slice закрывает **доступ B2B и идентичность**:

1. DocType **`ELMS Organization`** + членство пользователя в организации + **User Permission** (изоляции).
2. Роль **`ELMS Company Admin`** (+ Role Profile): приглашает только пользователей своей org; `ELMS Admin` создаёт org и первого Company Admin.
3. **Invite/provision:** создание/обновление User в Frappe **и** пользователя в Keycloak (Admin API) + email execute-actions «UPDATE_PASSWORD»; пароль не показывается в Desk.
4. **Yandex sunset:** удаление IdP `yandex` из realm seed/runtime-контракта; миграция федеративных Yandex-пользователей на локальный credential Keycloak с обязательной сменой пароля; smoke/тесты fail-closed без Yandex happy-path.

`ELMS Subscription` (квота мест) **не** проверяется при invite (решение владельца). Заявки Bitrix и кабинет прогресса — **не** этот эпик.

---

## Context consumed

| Path | Что вошло |
|------|-----------|
| `memory-bank/app/clarify/clarify-20261113-elms-b2b-roles-keycloak-provisioning.md` | Q1–Q11: B2B invite chain, email set-password, Organization без квоты, Yandex purge+migrate, заявки/кабинет out |
| `memory-bank/architecture/integrations.md` | Keycloak-only identity; ELMS operational hub |
| `memory-bank/product/modules.md` | Роли Admin/Operations/Learner/Instructor/Methodologist; User Permission vs User Group |
| `memory-bank/systemPatterns.md` | Central Identity; Closed integrations; Yandex legacy → purge |
| `memory-bank/techContext.md` | Keycloak compose, Social Login Key Keycloak-only, JIT |
| `elms/elms/install.py` | `ensure_roles`, Role Profiles, groups; нет Company Admin |
| `elms/elms/sso/*` | ensure Social Login Key; reconcile KC→Frappe; нет Frappe→KC provision |
| `docker/keycloak/realm-elms.json` | IdP alias `yandex` — sunset inventory |
| `scripts/live_smoke.sh` / SSO tests | Yandex broker routes → переписать под Keycloak-only |

## Clarifications

- Phase 0 done; Grill Round 1–3; CRITICAL нет.
- Invite без Subscription quota.
- Company Admin не видит чужие org.
- Yandex: C = purge + миграция существующих.

## Product outcome (WHAT)

Проблема: нельзя штатно выдать доступ компании и сотруднику так, чтобы человек сразу вошёл; Yandex лишний; org-границы нет. Успех: Admin завёл org и пригласил людей → письмо → пароль в Keycloak → вход в ELMS; Yandex пути нет.

### Product decision / WHAT

| Field | Decision | Impact |
|-------|----------|--------|
| **Reframe** | Provision+RBAC+IdP sunset, не «ещё одна роль в таблице» | Wire: Desk invite → KC → login |
| **Demand / status quo** | JIT только при первом SSO; Yandex broker; org — строка на Batch | Нужен обратный provision и DocType Organization |
| **Narrowest wedge** | Organization + Company Admin + invite sync + Yandex purge/migrate | Формы/кабинет — follow-up |
| **Explicit non-goals** | Bitrix-заявки; кабинет прогресса; квота Subscription на invite; IdP заказчика | Queue T-A08/T-A09 |
| **Success signal** | Invitee входит Keycloak-only; Company Admin не читает чужую org | Mixed QA + live smoke |
| **Decision** | `proceed` | DECOMPOSE после PLAN |

## Delivery closure

| Capability | Classification | Production entrypoint | Success / failure | Independent test | Follow-up |
|---|---|---|---|---|---|
| Organization + membership + UP | `vertical_slice` | Desk Form `ELMS Organization` + assign member | Missing org / cross-org → PermissionError | Create org, assign, assert UP | n/a |
| Company Admin invite | `vertical_slice` | Desk action / whitelist `invite_org_user` | KC fail → весь invite FAIL (нет «успех только Frappe») | Invite → KC user exists → email action queued/mocked | n/a |
| Keycloak-only login | `vertical_slice` | `/login` → Keycloak username/password | Yandex IdP absent; broker URL not required | live_smoke + realm assert no yandex | n/a |
| Yandex user migrate | `vertical_slice` | migration/ensure job | Federated-only user gets local cred + UPDATE_PASSWORD | Fixture federated → after migrate can auth local | n/a |

## Technology axiom (replace-not-wrap)

| Выбор | Machine input | FORBIDDEN после эпика |
|-------|---------------|------------------------|
| Keycloak Admin API typed client (Pydantic settings: base URL, realm, client_id/secret) | JSON responses + validated env | «создали User в Frappe, KC потом вручную» как success |
| Enum/Literal роли `ELMS Company Admin` | Role name + Role Profile | параллельный raw string «кадровик» без роли |
| Realm seed без IdP yandex | `realm-elms.json` | dual path broker Yandex + document «можно Yandex» |
| Invite result model (status, keycloak_user_id, email) | structured whitelist out | regex parse Keycloak HTML errors as OK |

Sunset inventory: `realm-elms.json` IdP `yandex` + mappers; tests/smoke ожидающие Yandex broker happy-path; copy «Login with Yandex»; env Yandex client secrets как обязательные для login (оставить только если ещё нужны иным контуром — **не** для SSO).

## User stories

| ID | Story | P | Independent test |
|----|-------|---|---|
| US-001 | Как ELMS Admin, я создаю Organization (название, ИНН/ОГРН) и назначаю Company Admin. | P0 | DocType + role assign test |
| US-002 | Как Company Admin, я приглашаю сотрудника своей org по email. | P0 | invite whitelist + KC mock/live |
| US-003 | Как приглашённый, я получаю письмо, задаю пароль в Keycloak и вхожу в ELMS. | P0 | wire journey login |
| US-004 | Как Company Admin, я не вижу и не приглашаю в чужую org. | P0 | PermissionError cross-org |
| US-005 | Как пользователь, я не вижу входа через Yandex. | P0 | realm + login UI/smoke |
| US-006 | Как оператор миграции, уже связанные через Yandex получают локальный credential и must-change password. | P0 | migrate behavior test |

### Acceptance — US-001

- **Given:** Admin в Desk.  
- **When:** создаёт Organization и назначает user роль Company Admin + membership.  
- **Then:** User Permission на эту Organization; Role Profile Company Admin применён.

### Acceptance — US-002

- **Given:** Company Admin в org A.  
- **When:** invite email нового сотрудника.  
- **Then:** Frappe User (enabled) + Keycloak user (same email) + execute-actions UPDATE_PASSWORD; ответ API success только если KC OK.

### Acceptance — US-003

- **Given:** invite выполнен.  
- **When:** пользователь проходит set-password и `/login` → Keycloak.  
- **Then:** сессия Frappe; роли Learner или назначенные; org scope на месте.

### Acceptance — US-004

- **Given:** Company Admin org A.  
- **When:** читает/invite org B или user без membership.  
- **Then:** PermissionError; KC user для B не создаётся.

### Acceptance — US-005

- **Given:** realm после ensure/migrate.  
- **When:** открыт login / authorization.  
- **Then:** нет enabled IdP yandex; тесты на broker yandex не требуют success.

### Acceptance — US-006

- **Given:** user с federated Yandex link.  
- **When:** migration job.  
- **Then:** локальный credential required actions; повторный вход через Yandex IdP невозможен (IdP disabled/removed).

## Acceptance criteria

- **AC-001:** Admin creates an Organization and assigns a Company Admin with a matching User Permission scope.
- **AC-002:** Invite success is reported only after both durable Frappe state and Keycloak provisioning succeed.
- **AC-003:** Re-invite is idempotent, sends `UPDATE_PASSWORD`, and never returns a password.
- **AC-004:** The realm seed and runtime migration are Keycloak-only: no enabled Yandex provider or broker hint remains.
- **AC-005:** The real Desk journey reaches the Organization and invite API with role-aware success and denial states.
- **AC-006:** The invite-to-password-to-login wire journey reaches Keycloak password setup and Keycloak-only ELMS login without a Yandex control.

## Functional requirements

### FR-001 — ELMS Organization

- DocType: name, inn, ogrn (валидация формата), optional kpp, status Active/Inactive.
- Child/link membership: User ↔ Organization (один primary org для Company Admin в P0; много org — explicit non-goal unless needed).
- На membership: создать/обновить User Permission `allow=ELMS Organization` / `for_value=org`.

### FR-002 — Role ELMS Company Admin

- Добавить в `ELMS_ROLES`, Role Profile `ELMS Company Admin Profile` (`Desk User` + роль).
- DocPerm: read/write ограниченные поверхности invite + read своей org; Settings deny; чужие Enrollment/Progress — только через follow-up T-A09 (в T-A07 минимум: не читать users вне org).
- `ELMS Admin` — полный RWCD Organization и может назначить любого Company Admin.

### FR-003 — Invite provision (ELMS → Keycloak)

- Whitelist (имена уточняются в DECOMPOSE): например `elms.access.invite_user(email, first_name, last_name, organization, roles[])`.
- Preconditions: caller Admin **или** Company Admin с membership на organization; email обязателен и уникален.
- Steps (atomic success): validate → create/update Frappe User + roles + membership + UP → Keycloak Admin API create/update user → send execute-actions-email `UPDATE_PASSWORD` → return structured result.
- Failure: любая ошибка KC после создания Frappe User → **rollback или compensating disable + throw** (не silent «создан локально»). Предпочтительно: KC first или transaction with explicit compensating delete/disable documented in DECOMPOSE.
- Re-invite существующего: идемпотентно по email; повторный execute-actions допустим.
- Пароль **никогда** не возвращается в API/UI.

### FR-004 — Keycloak Admin client

- Typed settings (env): `KEYCLOAK_ADMIN_*` или service-account client в realm (confidential), base URL internal для server-side, realm `elms`.
- Секреты не в git; absence → invite fail-closed.
- Не использовать пользовательский password Admin в коде тестов без fixtures.

### FR-005 — Yandex sunset

- Удалить IdP `yandex` и связанные mappers из `realm-elms.json` (и ensure/docs).
- Убрать обязательность Yandex secrets для SSO login path.
- Migration: найти users с IdP link yandex → ensure local password required actions; document operator runbook.
- `live_smoke` / SSO traces: Keycloak auth без Yandex broker requirement; Yandex endpoint checks → removed or assert absent.
- Login UI: без копирайта Yandex; остаётся Keycloak control (T-A01 surface).

### FR-006 — Login / JIT совместимость

- Сохранить Social Login Key Keycloak и callback.
- JIT: если user уже provisioned в Frappe с email, связать по email/`sub` без дубля.
- Default role на первый вход не должен снимать Company Admin / явные роли invite.

## Non-functional

| ID | Requirement |
|----|-------------|
| NFR-001 | Invite p95 server path < 5s без учёта email provider latency (mock email в unit). |
| NFR-002 | Все ошибки KC/сети — typed, без утечки client_secret. |
| NFR-003 | Audit: кто кого пригласил, org, timestamp (Activity или Invite Log DocType). |
| NFR-004 | 152-ФЗ: email/ФИО — минимально необходимые поля; пароли не логировать. |

## API / contract sketch

| Method | In | Out | Errors |
|--------|----|-----|--------|
| `elms.access.create_organization` | name, inn, ogrn?, kpp? | org name | ValidationError, PermissionError |
| `elms.access.assign_company_admin` | user, organization | ok | PermissionError, DoesNotExist |
| `elms.access.invite_org_user` | email, names, organization, role_profile? | {user, keycloak_id, invited:true} | PermissionError, ValidationError, KeycloakProvisionError |
| `elms.access.migrate_yandex_users` | dry_run? | {migrated:n, errors:[]} | PermissionError (Admin only) |

UI journeys:

1. Admin: Workspace Settings/Operations → Organization → New → Assign Company Admin.  
2. Company Admin: список людей org → Invite → success toast «письмо отправлено».  
3. User: email link → KC password → `/login` → Desk/LMS.  
4. Operator: run migrate → verify no yandex IdP.

## Explicit non-goals

- Формы заявок физ/юр и Bitrix status (T-A08).  
- Кабинет прогресса компании (T-A09).  
- Enforce Subscription quota на invite.  
- Bitrix как источник создания User (может быть позже).  
- Magic-link без Keycloak.

## Ownership matrix

| Surface | Owner in epic |
|---------|----------------|
| DocTypes Organization, membership, invite log | APP (backend elms) |
| Roles/DocPerm/UP | APP |
| Keycloak realm seed + Admin client | APP (docker/keycloak + elms.sso/access) |
| Desk UI invite/org | APP (Desk Form / JS) |
| Login CSS/JS | только правки copy/assert no Yandex; без fork template |
| Tests backend + browser login smoke | APP parent lanes |

## QA charter (APP)

| Lane | Required | Notes |
|------|----------|-------|
| backend | yes | roles, org UP, invite idempotency, KC client mock, migrate |
| frontend_build / Desk assets | yes if JS added | desk invite form |
| browser | yes | login Keycloak-only; no Yandex control |
| live_smoke | yes | Keycloak auth; Yandex broker not required |
| wire_journey | yes | invite → (mock mail) → password → session |
| leftover_sot | yes | grep yandex IdP enabled paths; dual provision |
| behavior_smoke | yes | FR wire |

## Risks

| Risk | Mitigation |
|------|------------|
| Orphan Frappe User without KC | compensating transaction + tests |
| Email delivery fails | status «KC created, email failed» explicit; re-send action |
| Existing Yandex users locked out | migrate + UPDATE_PASSWORD before IdP delete order in runbook |
| Company Admin over-permission | DocPerm + UP tests |

## DECOMPOSE hints

Suggested sNN (не final): s01 Organization+role+UP; s02 Keycloak admin client+invite; s03 Yandex sunset+migrate+smoke; s04 Desk UI+wire.

## Next

`APP DECOMPOSE T-A07-elms-b2b-org-keycloak-provisioning`

# [T-A09 | elms-company-admin-cabinet] PLAN

**Дата:** 2026-11-13  
**Режим:** APP PLAN → APP DECOMPOSE → APP IMPLEMENT → APP QA  
**Уровень:** L2  
**Статус:** planned  
**Clarify:** [memory-bank/app/clarify/clarify-20261113-elms-b2b-roles-keycloak-provisioning.md](../../../clarify/clarify-20261113-elms-b2b-roles-keycloak-provisioning.md)  
**Prompt:** [md/prompt.md](prompt.md)  
**Queue:** `memory-bank/app/roadmap/queue.yaml` → `T-A09` / `T-A09-elms-company-admin-cabinet`  
**Batch:** `elms-b2b-access`  
**Deps:** `T-A07-elms-b2b-org-keycloak-provisioning`, `T-A05-elms-learner-progress-and-quiz-player` (progress APIs as-built)  
**SUSPENSION GUARD:** active — plan output unlimited

---

## Решение

Кабинет **`ELMS Company Admin`**: одна Desk/LMS поверхность «Моя организация», где видны **только** пользователи membership своей `ELMS Organization`:

- ФИО / email / статус учётки;
- зачисления (`ELMS Enrollment`) и статусы;
- **% прогресса** по курсам из существующих `ELMS Course Progress` (и program summary если доступно as-built);
- **простой отчёт**: табличный export (CSV или xlsx) тех же колонок.

Не строится полноценный BI (воронки, heatmaps, сравнение потоков) — explicit non-goal (Q9=A).

Изоляция **только server-side** (roles + User Permission / membership filter); UI filter не security boundary.

---

## Context consumed

| Path | Что вошло |
|------|-----------|
| Clarify Q5/Q9 | Cabinet = list + enrollment + % + simple report |
| T-A07 | Organization, Company Admin, UP |
| T-A05 / lms api | learner progress contracts to reuse, not duplicate model |
| `product/modules.md` | Enrollment, Course Progress |

## Product outcome (WHAT)

Заказчик хочет сам видеть, учатся ли его люди. Успех: Company Admin открыл кабинет → только своя org → прогресс и выгрузка.

### Product decision

| Field | Decision | Impact |
|-------|----------|--------|
| **Reframe** | Org-scoped progress roster, не analytics suite | Reuse progress APIs |
| **Wedge** | List + % + CSV/xlsx | No BI |
| **Non-goals** | Forms Bitrix; Yandex; deep activity telemetry UI | |
| **Decision** | `proceed` | |

## Delivery closure

| Capability | Class | Entrypoint | Enforce | Test |
|---|---|---|---|---|
| Org roster | vertical_slice | cabinet page / whitelist `get_org_roster` | cross-org → PermissionError | two-org fixture |
| Progress columns | vertical_slice | same payload includes enrollment + % | missing progress → 0/empty explicit | progress join test |
| Simple report export | vertical_slice | `export_org_progress` → file | same ACL as roster | export rows match roster |
| Desk UI | vertical_slice | `/app/elms-learning` or Workspace card | empty org state | browser journey |

## Technology axiom

| Выбор | Machine input | FORBIDDEN |
|-------|---------------|-----------|
| Whitelist JSON roster DTO (pydantic/dict typed) | organization + filters | client-passed list of arbitrary user names without server filter |
| Reuse Course Progress fields | existing DocTypes | parallel «CompanyProgress» denormalized SoT |
| Export generated server-side | same query as roster | browser-only CSV from unchecked DOM |

## User stories

| ID | Story | P | Test |
|----|-------|---|------|
| US-001 | Как Company Admin, вижу список сотрудников своей org. | P0 | roster ACL |
| US-002 | Вижу статус зачисления и % по курсам. | P0 | progress fields |
| US-003 | Выгружаю простой отчёт. | P0 | export |
| US-004 | Не вижу другую org. | P0 | PermissionError |
| US-005 | Пустая org — понятный empty state. | P1 | UI |

### Acceptance

- US-001/004: Given Admin A in org1, users in org1/org2; When roster; Then only org1; direct API org2 → error.
- US-002: Given enrollment + course progress 40%; When roster row; Then shows Active/Completed/… and 40%.
- US-003: When export; Then file contains same users/rows; no org2.

## Functional requirements

### FR-001 — Roster API

- Input: organization (default = caller primary org); optional status filter.
- Output rows: user, email, roles (learner), enrollments[{course, status, progress_pct, last_activity?}].
- Authz: Company Admin membership **or** ELMS Admin (Admin may select org).

### FR-002 — Progress source

- `progress_pct` from `ELMS Course Progress` for active enrollments; definition = as-built field (percent complete).
- No inventing second formula; if no row → `null`/`0` with documented semantics.

### FR-003 — Export

- CSV (P0) or xlsx (P1); charset UTF-8; filename with org + date.
- Same authz as roster; audit log who exported.

### FR-004 — UI

- Card/page «Кабинет компании» visible to Company Admin (+ Admin).
- Table + Export button + empty state.
- Design: existing ELMS Desk/LMS tokens (neftegaz), no marketing landing.

## NFR

- Roster p95 reasonable for ≤500 members/org (paginate if needed — DECOMPOSE).
- Export capped (e.g. 5000 rows) with clear error if exceeded.

## Explicit non-goals

- Funnel analytics, lesson-level heatmaps, cross-org benchmarks.  
- Editing enrollments from cabinet (read-only P0).  
- Bitrix sync of progress.

## Ownership

| Surface | Owner |
|---------|-------|
| whitelist + export | APP backend |
| Desk cabinet UI | APP frontend |
| ACL tests | APP |

## QA charter

| Lane | Req |
|------|-----|
| backend | yes |
| browser | yes — cabinet + export download |
| wire_journey | yes — invitee from T-A07 appears in roster with progress |
| leftover_sot | yes — no unfiltered User list API |

## Risks

| Risk | Mitigation |
|------|------------|
| Progress API gaps | Depend T-A05; contract tests |
| UP misconfig leaks | fail-closed tests two-org |

## Next

`APP DECOMPOSE T-A09-elms-company-admin-cabinet` after T-A07 (hard dep).

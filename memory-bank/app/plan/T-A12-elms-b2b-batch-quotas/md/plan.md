# [T-A12 | elms-b2b-batch-quotas] PLAN

**Дата:** 2026-11-16  
**Режим:** APP PLAN → …  
**Уровень:** L3  
**Статус:** planned  
**Clarify:** [memory-bank/app/clarify/clarify-20261116-elms-admission-b2c-b2b-custom-fields.md](../../../clarify/clarify-20261116-elms-admission-b2c-b2b-custom-fields.md)  
**Prompt:** [md/prompt.md](prompt.md)  
**Queue:** `T-A12`  
**Batch:** `elms-admission-surfaces`  
**Deps:** `T-A11`, `T-A07`, `T-A09`  
**SUSPENSION GUARD:** active

---

## Решение

B2B зачисление из **уже распарсенного** import (T-A11):

1. Company Admin подтверждает import (или subset строк).
2. Для каждой строки: resolve/create Learner (+ synthetic creds already from T-A11), map program/course/batch, create **Active** `ELMS Enrollment`.
3. На каждое зачисление списывается **1 место** org-wide `ELMS Subscription` (Q6=A).
4. Org flags: `can_use_owner_catalog`, `can_publish_own` (Q2b=B) — enforce при маппинге курса.
5. Если квоты не хватает — **fail-closed** на confirm (частичный commit только если явно спроектирован transaction per-row with stop — default: atomic batch или stop-at-limit with explicit report; DECOMPOSE выбирает, но silent over-quota FORBIDDEN).

Platform admin **не** подтверждает от лица чужой org (Q4=C).

---

## Clarifications
- Q7=A Active сразу.
- Depends hard on T-A11.

## Product outcome
Компания одним подтверждением зачисляет список из бланка, не превышая квоту.

## Delivery closure

| Capability | Class | Entrypoint | Enforce | Test |
|---|---|---|---|---|
| Confirm import → enroll | vertical_slice | confirm_admission_import | requires parsed status | API+browser |
| Quota decrement | vertical_slice | subscription seats | over-quota DENY | unit |
| Catalog flags | vertical_slice | course resolve | cannot enroll owner course if flag off | API |
| Org isolation | enforce | confirm | other org import DENY | leftover_sot |

## Technology axiom
| Pydantic confirm payload | JSON | |
| Subscription seats int | DocType | soft ignore quota FORBIDDEN |
| Enrollment via enroll_learner | server | desk bulk without quota check FORBIDDEN |

## User stories / AC
| AC-001 | Given parsed import + seats≥N; When confirm N rows; Then N Active enrollments; seats_used += N. |
| AC-002 | Given seats < N; When confirm; Then typed error; no over-quota enrollments. |
| AC-003 | Given flag can_use_owner_catalog=false; When row targets owner course; Then row error. |
| AC-004 | Given other org import id; When confirm as Company Admin; Then 403. |

## FR
- Map программа/вид подготовки → Course/Program/Batch (rules in DECOMPOSE; fail if ambiguous).
- Write Learner Profile snapshot from row into unified profile (Q15=A).
- Audit: who confirmed, which import, seat delta.

## Non-goals
AI parse; B2C pay; custom fields; admin acting-as; 1С; Bitrix.

## QA charter
backend · browser · live_smoke · wire_journey · leftover_sot (quota enforce)



## Context consumed

| Path | Что |
|------|-----|
| Clarify Q2b/Q6/Q7/Q13 | flags, org seats, Active enroll, depends AI |
| T-A11 plan | parsed import SoT |
| T-A09 cabinet | company admin surface |
| `ELMS Subscription` as-built | seats_used/total_seats |

## Functional requirements

### FR-001 — Confirm import
- Input: import_id, optional row_ids subset, actor Company Admin of owning org.
- Preconditions: import status=`parsed` (or equivalent), all selected rows valid.
- Effects: create/link Users, upsert Learner Profile from row, create Active Enrollment per row, decrement seats.

### FR-002 — Quota
- Single subscription (or active subscription set) per org — DECOMPOSE pins selection rule (latest active / explicit subscription_id on import).
- seats_used increments atomically with enrollment create.
- Over-quota → typed `QuotaExceeded`; no partial silent success unless DECOMPOSE chooses stop-and-report with explicit `enrolled[]`+`rejected[]` in one response (must be documented in AC).

### FR-003 — Course resolve
- Map program title / training kind → Course and Batch.
- Ambiguous match → row error, no enroll.
- Enforce `can_use_owner_catalog` / `can_publish_own`.

### FR-004 — UI
- Company cabinet: open import → preview (from T-A11) → Confirm → result report.
- Show remaining seats before confirm.

## NFR

| ID | Requirement |
|----|-------------|
| NFR-001 | Transactional integrity around seat counter. |
| NFR-002 | Audit log confirm actor, import, counts. |
| NFR-003 | PII in profile same controls as B2C. |

## Ownership

| Surface | Owner |
|---------|-------|
| Confirm API + UI | APP |
| Subscription enforce | APP |
| Cabinet entry | APP (extends T-A09) |

## Risks

| Risk | Mitigation |
|------|------------|
| Ambiguous program names in blank | fail row; require catalog codes in follow-up |
| Partial batch confusion | explicit report contract |

## Explicit non-goals
AI parse; payment; custom fields; admin acting-as; Bitrix; 1С.

## Next
`APP DECOMPOSE T-A12-elms-b2b-batch-quotas`

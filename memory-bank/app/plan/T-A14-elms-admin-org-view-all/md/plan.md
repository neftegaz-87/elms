# [T-A14 | elms-admin-org-view-all] PLAN

**Дата:** 2026-11-16  
**Уровень:** L2  
**Статус:** planned  
**Clarify:** [memory-bank/app/clarify/clarify-20261116-elms-admission-b2c-b2b-custom-fields.md](../../../clarify/clarify-20261116-elms-admission-b2c-b2b-custom-fields.md)  
**Batch:** `elms-admission-surfaces`  
**Deps:** `T-A07`, `T-A09`  
**SUSPENSION GUARD:** active

---

## Решение (Q4=C)

- ELMS Admin / Operations получает UI **выбора организации** и read-модель кабинета/roster выбранной org.
- Действия submit admission / confirm B2B import / acting-as mutate **DENY** (остаются у Company Admin своей org).
- Audit: какой админ смотрел какую org.

## Product outcome
Поддержка платформы видит все компании, не притворяясь их кадровиком.

## AC
| AC-001 | Admin lists all orgs and opens roster of org X. |
| AC-002 | Admin confirm_admission_import for org X → 403. |
| AC-003 | Company Admin still cannot see other orgs. |

## Non-goals
Impersonation session; submit от лица компании.

## QA charter
backend · browser · leftover_sot (DENY mutate)



## Context consumed

| Path | Что |
|------|-----|
| Clarify Q4=C | view-all, no acting-as |
| T-A09 cabinet | roster APIs |
| T-A07 Organization | org list |

## Clarifications
- Read context only; mutate admission/import DENY.

## Functional requirements

### FR-001 — Org directory
- ELMS Admin/Operations: list all `ELMS Organization`.
- Switcher sets view context `organization` for subsequent read APIs.

### FR-002 — Read reuse
- Reuse T-A09 `get_org_roster` / export with admin override when actor has platform role + selected org.
- Company Admin path unchanged (own org only).

### FR-003 — DENY mutate-as
- `confirm_admission_import`, B2C ops-as-company, invite-as-company from platform switcher context → 403 unless actor is member Company Admin of that org.
- UI copy: «режим просмотра».

### FR-004 — Audit
- Record view-org events (actor, org, timestamp).

## NFR
| NFR-001 | No session User swap (not impersonation). |
| NFR-002 | Audit retention per 152-FZ ops policy. |

## Ownership
APP Settings/LMS admin UI + API guards.

## Risks
| Accidental write path | explicit capability check leftover_sot |

## Explicit non-goals
Acting-as submit; synthetic full Company Admin impersonation; 1С.

## Next
`APP DECOMPOSE T-A14-elms-admin-org-view-all`

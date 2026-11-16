# [T-A13 | elms-custom-fields-course-program-batch] PLAN

**Дата:** 2026-11-16  
**Уровень:** L2  
**Статус:** planned  
**Clarify:** [memory-bank/app/clarify/clarify-20261116-elms-admission-b2c-b2b-custom-fields.md](../../../clarify/clarify-20261116-elms-admission-b2c-b2b-custom-fields.md)  
**Batch:** `elms-admission-surfaces`  
**Deps:** `T-A02`  
**SUSPENSION GUARD:** active

---

## Решение

MVP конструктора полей (Q14=B):

- Сущности: `ELMS Course`, `ELMS Program`, `ELMS Batch`.
- Org-scoped schema (Company Admin / Methodologist в своей org; platform Admin для owner catalog).
- Field types MVP: text, number, date, select, checkbox (file/rich — follow-up unless trivial).
- Values validate-on-write (Pydantic/JSON schema).
- Optional inheritance Program→Course→Batch override (Recommended from earlier Q12/B intent) — include thin override merge.

Target full graph (categories, chapters, lessons) documented as follow-up epic in queue note / defer-list — **not** silent scope creep inside this epic.

## Product outcome
При создании/редактировании курса, программы и потока школа заполняет свои поля (комиссия, удостоверение, часы…).

## Delivery closure
| Define schema UI/API | vertical_slice | |
| Edit values on Course/Program/Batch forms | vertical_slice | |
| Reject unknown/invalid values | enforce | |
| No dual free-text parallel store | leftover_sot | |

## Technology axiom
JSON schema / typed CustomFieldDefinition → values JSON validated. FORBIDDEN: untyped long_text dump as only store.

## AC
| AC-001 | Admin defines select field on Course; value saved and shown. |
| AC-002 | Invalid type → ValidationError. |
| AC-003 | Other org cannot read/write schema of foreign org. |
| AC-004 | Chapter/Lesson custom schema endpoints absent or explicitly 404/not in MVP UI. |

## Non-goals
Category/Chapter/Lesson fields; admission form builder (uses Learner Profile, not this schema).

## QA charter
backend · browser Desk forms · leftover_sot



## Context consumed

| Path | Что |
|------|-----|
| Clarify Q12/Q14 | full graph target; MVP C/P/Batch |
| T-A02/T-A04 as-built | Course/Program/Batch DocTypes |
| modules.md §Поступление | canon |

## Clarifications
- Follow-up epic for Category/Chapter/Lesson must appear in queue or defer-list with owner (defer-list already in clarify).

## Functional requirements

### FR-001 — Field definition
- DocType or JSON schema store: name, label, type, required, options (select), applies_to∈{Course,Program,Batch}, organization.
- CRUD by Methodologist/Company Admin (own org) and ELMS Admin (owner org).

### FR-002 — Values
- Stored on target document (child table or JSON field) validated on validate().
- Inheritance: Program defaults → Course → Batch override (empty means inherit).

### FR-003 — UI
- Desk form section «Доп. поля» on Course/Program/Batch.
- Schema manager page/workspace action.

## NFR
| NFR-001 | Org isolation on schema and values. |
| NFR-002 | Migration-safe schema version. |

## Ownership
APP LMS DocTypes + Desk UI.

## Risks
| Unbounded schema growth | type allowlist MVP |
| Performance JSON | index not required MVP |

## Explicit non-goals
Admission forms fields (Learner Profile); Category/Chapter/Lesson; Bitrix.

## Next
`APP DECOMPOSE T-A13-elms-custom-fields-course-program-batch`

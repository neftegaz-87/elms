# [T-A11 | elms-ai-admission-parse] PLAN

**Дата:** 2026-11-16  
**Режим:** APP PLAN → APP DECOMPOSE → APP IMPLEMENT → APP QA  
**Уровень:** L3  
**Статус:** planned  
**Clarify:** [memory-bank/app/clarify/clarify-20261116-elms-admission-b2c-b2b-custom-fields.md](../../../clarify/clarify-20261116-elms-admission-b2c-b2b-custom-fields.md)  
**Prompt:** [md/prompt.md](prompt.md)  
**Queue:** `memory-bank/app/roadmap/queue.yaml` → `T-A11`  
**Batch:** `elms-admission-surfaces`  
**Deps:** `T-A07`, `T-A06`  
**SUSPENSION GUARD:** active

---

## Решение

Отдельный ship-ready эпик **разбора бланка заявки** (blocker для B2B enroll):

1. Company Admin (своей org) загружает XLSX по канону fixtures бланка 2026.
2. ELMS вызывает контур разбора (neftegaz-ai-layer / OmniRoute grounded parse) → structured rows.
3. Каждая строка валидируется Pydantic DTO (ФИО, ДР, СНИЛС, образование, телефон, программа/вид подготовки, … + шапка org/ИНН).
4. Если email отсутствует → генерируются **синтетические credentials** (login/email+temp secret) для будущего входа; секреты доступны Admin/Company Admin для раздачи; не публикуются в UI слушателю автоматически.
5. Результат: `ELMS Admission Import` (или аналог) со статусами draft/parsed/failed + row children. **Enrollment не создаётся** в этом эпике.

---

## Context consumed

| Path | Что |
|------|-----|
| Clarify Q10–Q13,Q17 | XLSX бланк; AI epic before B2B; synthetic creds |
| fixtures-20261116-admission | SoT колонок |
| T-A06 OmniRoute | AI transport patterns |

## Clarifications
- Q13=C: этот эпик **до** T-A12.
- Ship-ready без enroll: preview+export rows + credential vault for admins.

## Product outcome (WHAT)
Загруженный бланк превращается в проверяемый список людей и программ с учётками, которые админ может раздать.

## Delivery closure

| Capability | Class | Entrypoint | Enforce | Test |
|---|---|---|---|---|
| Upload blank | vertical_slice | whitelist upload | wrong mime/empty → error | API |
| AI parse → DTO | vertical_slice | parse job | invalid schema → fail-closed row errors | contract+fixture sample |
| Synthetic creds | vertical_slice | provision identity | no plaintext in learner UI | unit |
| No enroll | enforce | import API | enroll endpoints not called | leftover_sot |

## Technology axiom

| Выбор | Machine input | FORBIDDEN |
|-------|---------------|-----------|
| Pydantic AdmissionRow | JSON from parser | regex-only Excel scrape as validated |
| Typed import status enum | DocType field | prose status line |
| Fixtures blank as column SoT | xlsx | ad-hoc column aliases without schema version |

## User stories

| ID | Story | P |
|----|-------|---|
| US-001 | Загружаю бланк и вижу preview строк. | P0 |
| US-002 | Вижу ошибки по строкам (СНИЛС/даты). | P0 |
| US-003 | Для строк без email получаю synthetic login для раздачи. | P0 |
| US-004 | Повторная загрузка того же файла идемпотентна или явная новая ревизия. | P1 |

### Acceptance criteria

| ID | Criterion |
|----|-----------|
| AC-001 | Given blank-zayavka fixture; When parse; Then ≥ header fields mapped; sample Сметанин row extracts FIO+SNILS. |
| AC-002 | Given row without email; When parse OK; Then synthetic identity created and listed for admin. |
| AC-003 | Given corrupt file; When parse; Then import status failed with explicit error; no partial silent success presented as OK. |
| AC-004 | Given parsed import; When inspect; Then zero Enrollment documents created by this epic APIs. |

## Functional requirements

### FR-001 — Blank schema v1
- Header: org name, INN, program title, training kind.
- Columns: №, FIO, profession, birth date, SNILS, education, phone, contractor, program, training kind.
- Schema version field on import.

### FR-002 — AI parse pipeline
- Input file hash; provider call; structured JSON; validate; persist rows.
- Human preview before handoff to T-A12.

### FR-003 — Synthetic credentials
- Deterministic uniqueness (e.g. based on SNILS hash + org).
- Store secret one-time reveal for Company Admin/ELMS Admin.
- Keycloak provision may be deferred to T-A12 or thin invite hook — DECOMPOSE decides; minimum: Frappe User ready or invite token recorded.

## NFR
- PII encryption at rest for secrets; audit who revealed creds.
- Parse timeout bounded; fail-closed.

## Explicit non-goals
- Creating Enrollment / decrement quota (T-A12).
- Deterministic-only parser without AI (rejected by Q13=C).
- 1С.

## Ownership
APP (upload UI + parse service + import DocTypes). AI transport reuse T-A06 patterns.

## QA charter
backend yes · browser yes (upload+preview) · live_smoke optional AI · wire_journey yes · leftover_sot yes (no enroll)

## Risks
| Risk | Mitigation |
|------|------------|
| AI hallucinated columns | schema validate fail-closed + fixture golden |
| Cred leak | one-time reveal + audit |

## Next
`APP DECOMPOSE T-A11-elms-ai-admission-parse`

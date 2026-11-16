# [T-A10 | elms-b2c-admission-payment] PLAN

**Дата:** 2026-11-16  
**Режим:** APP PLAN → APP DECOMPOSE → APP IMPLEMENT → APP QA  
**Уровень:** L3  
**Статус:** decomposed  
**Clarify:** [memory-bank/app/clarify/clarify-20261116-elms-admission-b2c-b2b-custom-fields.md](../../../clarify/clarify-20261116-elms-admission-b2c-b2b-custom-fields.md)  
**Prompt:** [md/prompt.md](prompt.md)  
**Queue:** `memory-bank/app/roadmap/queue.yaml` → `T-A10` / `T-A10-elms-b2c-admission-payment`  
**Batch:** `elms-admission-surfaces`  
**Deps:** `T-A02`, `T-A07`  
**SUSPENSION GUARD:** active — plan output unlimited

---

## Решение

Вертикальный срез **B2C поступления**:

1. После регистрации слушатель выбирает опубликованный курс/поток.
2. Заполняет **Learner Profile** (паспортные данные, образование, профессия) и загружает обязательные сканы: паспорт, СНИЛС, документ об образовании.
3. Система создаёт платёж через **abstract Payment Provider port** и ждёт webhook `paid` / `failed`.
4. Только после `paid` создаётся `ELMS Enrollment` (Active).

Конкретный эквайринг и 1С **вне** эпика (адаптер follow-up). Bitrix status SoT **не** используется как master этого контура (deferred).

---

## Context consumed

| Path | Что вошло |
|------|-----------|
| Clarify Q3b/Q8/Q9/Q15 | pay webhook; payment port; docs before pay; unified profile |
| `product/modules.md` §Поступление | канон каналов |
| T-A02 learning core | Enrollment / Batch / Course |
| T-A07 org/Keycloak | User/Learner identity |

## Clarifications

- Цепочка: анкета+сканы → оплата → зачисление.
- Payment Provider = port (create payment + verify webhook signature + status enum).
- Согласие ПДн: checkbox+версия текста в том же submit profile (минимум 152-ФЗ).
- 1С / конкретный вендор — out.

## Product outcome (WHAT)

Физлицо само записывается на курс: документы собраны, оплата подтверждена webhook'ом, доступ в player появляется без ручного «проставить оплачено» в чате.

### Product decision

| Field | Decision | Impact |
|-------|----------|--------|
| **Reframe** | B2C = profile+files+pay gate перед Enrollment | Payment port + profile DocType |
| **Narrowest wedge** | One course enroll after paid | Multi-course cart out |
| **Non-goals** | 1С; Bitrix master; B2B blank | другие эпики batch |
| **Decision** | `proceed` | |

## Delivery closure

| Capability | Class | Entrypoint | Enforce | Test |
|---|---|---|---|---|
| Learner Profile upsert | vertical_slice | whitelist save_profile + file attach | missing required field/file → 4xx | API + browser |
| Start payment | vertical_slice | create_payment(course,batch) | unpaid → no Enrollment | unit+API |
| Webhook paid | vertical_slice | payment webhook endpoint | invalid signature → reject; paid→enroll once | contract tests |
| Deny enroll without pay | enforce | enroll path for B2C | DENY Active without paid payment ref | leftover_sot |

## Technology axiom

| Выбор | Machine input | FORBIDDEN |
|-------|---------------|-----------|
| Pydantic LearnerProfile DTO | JSON | regex extract prose passport |
| PaymentStatus Literal/Enum | webhook JSON validated | free-text «оплачено» в UI как SoT |
| Enrollment only via server after paid | payment_id link | desk checkbox «считать оплаченным» без payment record (кроме отдельного ops epic — не здесь) |

## User stories

| ID | Story | P | Test |
|----|-------|---|------|
| US-001 | Как слушатель, заполняю анкету и загружаю сканы до оплаты. | P0 | validation |
| US-002 | Как слушатель, получаю ссылку/сессию оплаты и после webhook вижу зачисление. | P0 | webhook→enroll |
| US-003 | Как слушатель, при failed/cancel не получаю Active enrollment. | P0 | negative |
| US-004 | Как система, повторный webhook idempotent (одно зачисление). | P0 | idempotency |
| US-005 | Как Admin/Ops, вижу статус платежа и профиль, но не подменяю paid локальным enum без payment event. | P0 | DENY |

### Acceptance criteria

| ID | Criterion |
|----|-----------|
| AC-001 | Given registered Learner + published batch; When profile incomplete; Then payment create rejected with typed error. |
| AC-002 | Given complete profile+files+consent; When create_payment; Then Payment record `pending` and provider session returned. |
| AC-003 | Given valid signed webhook `paid`; When handled; Then Enrollment Active exists exactly once for (user,batch). |
| AC-004 | Given webhook `failed` or unsigned; When handled; Then no Active Enrollment; error logged. |
| AC-005 | Given B2C path; When attempt enroll_learner without paid payment; Then DENY. |
| AC-006 | Given authenticated Learner; When save_profile without required fields or required scans or PD consent; Then typed ValidationError and no complete profile; When all required present; Then one ELMS Admission Profile per User persists with private files. |

## Functional requirements

### FR-001 — Learner Profile
- Fields: FIO parts, birth date, passport series/number, SNILS, education level, profession/position, phone, email (from User), consent version+timestamp.
- Files: passport_scan, snils_scan, education_doc_scan (Frappe File / private).
- One profile per User; upsert API.

### FR-002 — Payment port
- Interface: `create_payment(amount, currency, meta)`, `parse_webhook(headers, body) -> PaymentEvent`.
- Stub/fake adapter allowed in tests; production adapter config fail-closed if missing when payments enabled.
- Store provider_payment_id, status, raw event id for idempotency.

### FR-003 — Enroll after paid
- Map course/batch from payment meta.
- Call existing enroll path with quota rules **not** required for open B2C (subscription optional); if batch tied to subscription later — separate rule.
- Progress zero on create.

### FR-004 — UI journey
- Learner web/Desk steps: select course → profile form → upload → pay CTA → waiting → success with link to learning.
- Empty/error states explicit.

## NFR

| ID | Requirement |
|----|-------------|
| NFR-001 | Private file access only owner/Admin/Operations. |
| NFR-002 | Webhook signature verification mandatory. |
| NFR-003 | PII masked in logs. |
| NFR-004 | Idempotent webhook by event id. |

## Explicit non-goals
- 1С invoices; concrete YooKassa/Tinkoff adapter as sole hard dep (port+fake OK).
- B2B XLSX; AI parse; custom course fields.
- Bitrix lead create as gate for enroll.

## Ownership

| Surface | Owner |
|---------|-------|
| Profile DocType + API + UI | APP |
| Payment port + webhook | APP |
| Enrollment wire | APP |

## QA charter

| Lane | Req |
|------|-----|
| backend | yes |
| frontend_build | yes |
| browser | yes — full journey to paid mock |
| live_smoke | yes — API health; payment webhook with test secret |
| wire_journey | yes |
| leftover_sot | yes — no enroll without payment |

## Risks

| Risk | Mitigation |
|------|------------|
| Adapter unknown | port + fake; config flag |
| Double enroll | unique (user,batch) + idempotent event |
| PII leaks | private files + masked logs |

## Next
`APP DECOMPOSE T-A10-elms-b2c-admission-payment`

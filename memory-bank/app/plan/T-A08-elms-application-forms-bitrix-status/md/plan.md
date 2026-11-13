# [T-A08 | elms-application-forms-bitrix-status] PLAN

**Дата:** 2026-11-13  
**Режим:** APP PLAN → APP DECOMPOSE → APP IMPLEMENT → APP QA  
**Уровень:** L2  
**Статус:** planned  
**Clarify:** [memory-bank/app/clarify/clarify-20261113-elms-b2b-roles-keycloak-provisioning.md](../../../clarify/clarify-20261113-elms-b2b-roles-keycloak-provisioning.md)  
**Prompt:** [md/prompt.md](prompt.md)  
**Queue:** `memory-bank/app/roadmap/queue.yaml` → `T-A08` / `T-A08-elms-application-forms-bitrix-status`  
**Batch:** `elms-b2b-access`  
**Deps:** `T-A07-elms-b2b-org-keycloak-provisioning`, `T-B04-bitrix-rest-client`  
**SUSPENSION GUARD:** active — plan output unlimited

---

## Решение

Публичные **формы заявлений в ELMS** (Website/Desk web):

| Тип | Кто | Цель |
|-----|-----|------|
| B2C физлицо | гражданин | заявление на прохождение **конкретного курса** |
| B2B юрлицо | представитель компании | заявление на **сотрудничество** по определённым курсам |

При submit ELMS через существующий Bitrix REST (`BITRIX_REST_WEBHOOK_URL` / `scripts/bitrix`) **создаёт лид или сделку** и сохраняет `bitrix_id` + тип в локальной записи-ссылке.

**SoT статуса заявки = Bitrix** (решение Q11=B). ELMS:

- не даёт оператору перебить статус локально «в обход Bitrix»;
- показывает статус, **прочитанный** из Bitrix (on-demand и/или inbound webhook/хук обновления зеркала);
- при недоступности Bitrix — явная ошибка на submit и на refresh статуса (fail-closed).

Авто-invite в Keycloak из статуса Bitrix **не обязателен** в P0: после CRM-одобрения оператор использует T-A07 invite (wire «статус Approved → подсказка/задача» допустима как P1).

---

## Context consumed

| Path | Что вошло |
|------|-----------|
| Clarify Q7/Q10/Q11 | Формы в ELMS; Bitrix status SoT |
| `architecture/integrations.md` | Bitrix REST; ELMS forms + sync |
| `scripts/bitrix/rest_client.py` | Единственный transport; fail-closed credentials |
| T-A07 plan | Organization/invite после CRM — handoff, не dual provision |

## Clarifications

- Status SoT = Bitrix; ELMS mirror read-only для status field.
- Две формы: individual→course; legal→cooperation on courses.
- Quota Subscription не связана с формой в этом эпике.

## Product outcome (WHAT)

Клиент оставляет заявление на сайте школы; менеджер ведёт воронку в Bitrix; на сайте/в ELMS виден тот же статус. Успех: submit → сущность в Bitrix; смена статуса в Bitrix видна при просмотре в ELMS.

### Product decision

| Field | Decision | Impact |
|-------|----------|--------|
| **Reframe** | ELMS = UX формы + link; Bitrix = status engine | Inbound/outbound sync contract |
| **Narrowest wedge** | 2 формы + create lead/deal + status read-back | Auto-provision из статуса — P1/out |
| **Non-goals** | ELMS-owned status machine; Минтруд; Keycloak invite auto | T-A07 manual/ops invite |
| **Decision** | `proceed` | |

## Delivery closure

| Capability | Class | Entrypoint | Enforce | Test |
|---|---|---|---|---|
| Individual application form | vertical_slice | public web form → whitelist submit | Bitrix create fail → form error | API + browser submit |
| Legal entity application form | vertical_slice | public web form → submit | same | API + browser |
| Status read-back | vertical_slice | Desk/web «моя заявка» / admin list refresh | Local status edit DENY; show Bitrix status | Mock Bitrix status change → ELMS shows new |
| Bitrix transport | vertical_slice | rest_client only | missing webhook → exit/throw | isolation tests reuse T-B04 |

## Technology axiom

| Выбор | Machine input | FORBIDDEN |
|-------|---------------|-----------|
| Pydantic submit payload (type: individual\|legal, course ids, contacts, INN…) | JSON form POST | free-text «статус одобрено» regex |
| Bitrix entity id + status code as SoT | REST get | локальный Select status как master |
| Typed mirror DocType `ELMS Application Link` (или аналог) | bitrix_id, kind, last_status_snapshot, last_synced_at | второй CRM в Frappe с независимым workflow status |

## User stories

| ID | Story | P | Test |
|----|-------|---|------|
| US-001 | Как физлицо, отправляю форму на курс и вижу подтверждение с номером/ссылкой. | P0 | submit creates Bitrix + link |
| US-002 | Как юрлицо, отправляю форму сотрудничества по выбранным курсам. | P0 | legal payload + Bitrix |
| US-003 | Как заявитель/оператор, вижу **текущий статус из Bitrix**. | P0 | status refresh |
| US-004 | Как система, при падении Bitrix не показываю ложный success. | P0 | fail-closed |
| US-005 | Как Admin, не могу выставить «Approved» только в ELMS в обход Bitrix. | P0 | DENY local master status |

### Acceptance highlights

- US-001: Given published course id; When submit valid PII+consent; Then Bitrix lead/deal created; ELMS stores bitrix_id; user sees success with tracking ref.
- US-003: Given Bitrix status changed to STAGE_X; When ELMS refresh; Then UI shows STAGE_X label from mapping; stale local snapshot updated.
- US-005: Given Application Link; When PATCH local status; Then ValidationError/Permission denied.

## Functional requirements

### FR-001 — Forms

- Individual: FIO, email, phone, course (Link/Select published courses), consent PDn checkbox.
- Legal: company name, INN, contact FIO/email/phone, multi-select courses, comment, consent.
- Server-side validation; CSRF/website form security per Frappe patterns.
- Honeypot/rate-limit — минимум NFR (DECOMPOSE).

### FR-002 — Bitrix create

- Map form → Bitrix method (crm.lead.add / crm.deal.add — зафиксировать в DECOMPOSE по as-built порталу).
- Fields mapping table in plan implement notes; missing required Bitrix field → fail-closed.
- Persist `bitrix_id`, `bitrix_entity` (lead|deal), `application_kind`.

### FR-003 — Status SoT

- `get_application_status(name)` → Bitrix get + map to display label.
- Optional webhook inbound from Bitrix (если портал умеет) обновляет **snapshot only**.
- UI badge = snapshot with `synced_at`; button «Обновить статус».
- FORBIDDEN: ELMS Workflow State как master.

### FR-004 — Ops handoff

- Desk list Application Links for Admin/Operations (read).
- P1 optional: when Bitrix status ∈ {approved…}, show action «Пригласить в ELMS» → deep link T-A07 invite (не auto).

## NFR

- Submit timeout explicit; Bitrix error text sanitized.
- PII only fields needed; logs mask phone/email partially.
- Idempotent submit key (email+course+day) — optional anti-dup (DECOMPOSE).

## Explicit non-goals

- Auto Keycloak user on Bitrix approve (unless P1 thin deep-link).  
- Subscription quota.  
- Company cabinet (T-A09).  
- Замена Bitrix CRM.

## Ownership

| Surface | Owner |
|---------|-------|
| Web forms + whitelist | APP |
| Application Link DocType | APP |
| Bitrix REST calls | APP via `scripts/bitrix` / elms wrapper |
| Status mapping config | APP (DocType/JSON settings — single source) |

## QA charter

| Lane | Req |
|------|-----|
| backend | yes — validation, Bitrix mock, DENY local status |
| browser | yes — both forms submit + status display |
| live_smoke | optional if Bitrix sandbox; else mock + documented not_run live Bitrix |
| wire_journey | yes — form → bitrix_id → status read |
| leftover_sot | yes — no master status in ELMS |

## Risks

| Risk | Mitigation |
|------|------------|
| Неверный Bitrix entity/stage map | Inventory portal fields in DECOMPOSE; fixture contract |
| Dual edit confusion | UI copy «статус из Bitrix»; no local edit |
| PII to Bitrix | consent + field minimize |

## Next

`APP DECOMPOSE T-A08-elms-application-forms-bitrix-status` (после T-A07 или параллельно только UI stubs — **deps T-A07** для org handoff P1; формы могут стартовать после T-B04 already done; queue deps keep T-A07 for cut cohesion).

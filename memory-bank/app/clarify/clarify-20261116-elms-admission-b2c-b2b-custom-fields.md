# clarify — elms-admission-b2c-b2b-custom-fields

**plan_id:** T-A10 (proposed)  
**slug:** elms-admission-b2c-b2b-custom-fields  
**role:** app  
**date:** 2026-11-16  
**feature_description:** Формы подачи документов и зачисления для физлиц и юрлиц; batch-загрузка обучающихся компанией; согласия ПДн; счета 1С для физиков; квоты B2B; company switcher для owner/admin; конструктор кастомных полей курса/программы/потока.  
**status:** done

---

## Контекст и цель

- Вход чата: два сценария поступления (self B2C vs company batch B2B); согласия ПДн; 1С счета для физлиц; квоты для юрлиц; админы платформы ходят по всем компаниям и подают от их лица; нужен конструктор полей курса/программы/потока (сейчас жёсткая схема).
- As-built канон: открытая платформа + партнёры (`modules.md` / `vision.md`); `ELMS Enrollment` + `ELMS Subscription` квоты; T-A09 cabinet DONE; T-A08 application forms Bitrix — соседний контур заявок.
- Цель Phase 0: снять ambiguity до APP PLAN Phase 1 (возможно multi-epic).
- Round 1: независимый frontier — wedge, тип B2B-актора, gate физлица, модель company switcher.

---

## Grill pass (Phase 0 — mandatory)

| Поле | Значение |
|------|----------|
| **Reframe** | Нужен операционный контур **поступления на обучение** (заявка/документы → зачисление) для двух каналов — самозапись физлица и пакетная загрузка от компании по квотам — плюс админский обход компаний и гибкие метаданные курса/программы/потока. |
| **Premises** | (1) Multi-epic по поверхностям — `accepted`. (2) B2C: анкета+сканы → payment port → enroll — `accepted`. (3) Партнёр flags + org-wide квота — `accepted`. (4) B2B = XLSX бланк — `accepted`. (5) AI-parse эпик до B2B — `accepted` (Q13=C). (6) Form-builder MVP Course+Program+Batch — `accepted` (Q14=B). (7) Единый Learner Profile — `accepted` (Q15=A). (8) Bitrix deferred — `accepted` (Q16). (9) Admin view-all; 1С out — `accepted`. (10) Нет email → синтетические креды; админы раздают later — `accepted` (Q17). |
| **Weakest link** | Смешать в один эпик формы+квоты+1С+custom fields+impersonation → размытый done; или наоборот выкинуть квоты/1С и получить «формы без бизнес-модели». |
| **Anti-scope (черновик)** | Полный ERP/финансы внутри ELMS; корпоративный SSO заказчика; ФИС ФРДО/Минтруд автоподача; миграция Прометея; Bitrix как SoT статуса заявки (если не выбран явно). |
| **Verdict** | `resolved` (frontier closed) |
| **Design tree (sketch)** | Wedge/приоритет → Тип B2B-актора → Gate физлица (docs/pay) → Admin org-switch → (зависит) Batch/квоты → 1С → ПДн → Form builder scope |

---

## Product probe (черновик до ответов)

- **Demand reality:** нельзя нормально принимать физиков с документами/согласием/оплатой и юрлиц пачкой по квотам; курс/программа без кастомных полей школы.
- **Status quo:** enrollment/subscription foundation есть; кабинет компании (T-A09); жёсткие поля DocType курса/программы/потока; полноценных admission-форм + 1С + org-impersonation нет.
- **Desperate specificity:** при создании курса/программы нельзя задать школьные поля (удостоверения, комиссии, часы); нет пакетной загрузки «кто на какой курс».
- **Narrowest wedge (гипотеза):** один канал поступления end-to-end (скорее B2C форма+зачисление **или** B2B batch+квота) + минимальный admin switch; form builder и 1С — follow-up, если пользователь не выберет combined.
- **Observation:** T-A08 уже про application forms + Bitrix — риск дубля/конфликта SoT статуса.
- **Future-fit:** школы с разными наборами полей; квоты по договорам; 1С как внешний биллинг.

---

## Таксономия сканирования

| Категория | Status | Notes |
|-----------|--------|-------|
| scope | Clear | Поверхности: B2C · AI-parse · B2B+квоты · form-builder(C/P/B) · admin view-all; 1С out; Bitrix defer |
| data | Clear | Learner Profile unified; нет email → synthetic credentials (Q17) |
| UX-API | Clear | B2C multi-step; B2B upload→AI→enroll (после AI-эпика) |
| NFR | Partial | ПДн/сканы; payment webhook — в PLAN |
| integrations | Partial | Payment port; AI-layer; Bitrix deferred; 1С out |
| edge | Partial | В PLAN |
| constraints | Clear | Fail-closed; бланк = SoT колонок; AI-эпик блокирует B2B |
| terminology | Clear | Заявка B2B = XLSX бланк; Bitrix не SoT до reconcile |
| design_skills | Clear | product_ui |

---

## Design skills pack

```yaml
surface: product_ui
dialect: none
image_pack: []
groups: [D0]
pin_v1: false
resolved_paths:
  - .agents/skills/frontend-design/SKILL.md
status: draft
note: "Desk + learner/company portal forms; не marketing landing."
```

---

## Frontier rounds

### Round 1 — 2026-11-16 — partial

| Q | Status | Answer |
|---|--------|--------|
| Q1 | settled | Multi-epic **по поверхностям** (не один mega-epic). Cut поверхностей → Round 2 Q5. |
| Q2 | **re-ask** | Prose принят как intent; формальная модель org/capabilities не закрыта → Q2b |
| Q3 | **re-ask** | Цепочка reg→курс→оплата→зачисление + 1С later; механизм оплаты MVP без 1С не закрыт → Q3b |
| Q4 | settled | **C** — admin видит все org; подача/batch от лица компании нет |

### Round 2 — 2026-11-16 — answered

| Q | Status | Answer |
|---|--------|--------|
| Q2b | settled | **B** — флаги `can_use_owner_catalog` + `can_publish_own`; квота всегда |
| Q3b | settled | ≈**D** — вебхук от платежки → paid → enroll (провайдер → Round 3) |
| Q5 | settled | **A без 1С**: (1) B2C admission+pay (2) B2B batch+квоты (3) конструктор полей (4) admin view-all |
| Q6 | settled | **A** — одна квота мест на org |
| Q7 | settled | **A** — сразу Active enrollments |

### Round 3 — 2026-11-16 — answered (частично formal)

| Q | Status | Answer |
|---|--------|--------|
| Q8 | settled | **D** — abstract Payment Provider port |
| Q9 | settled (prose) | До оплаты: паспортные данные, образование, профессия + фото паспорта, СНИЛС, документ об образовании → оплата → зачисление |
| Q10 | settled | **A** XLSX; канон-шаблон = бланк заявки; fixtures сохранены; AI-layer для разбора — open → Q13 |
| Q11 | settled | Колонки = содержимое бланка (ФИО, должность, ДР, СНИЛС, образование, телефон, контрагент, программа, вид подготовки + шапка org/ИНН/программа) |
| Q12 | settled (prose) | Кастом на весь учебный граф: Курсы, Категории, Программы, Состав программ, Разделы, Уроки/материалы, Потоки/группы; MVP типы → Q14 |

### Fixtures (SoT бланка)

- `memory-bank/app/clarify/fixtures-20261116-admission/blank-zayavka-2026.xlsx`
- `memory-bank/app/clarify/fixtures-20261116-admission/sample-rpo-smetanin.xlsx`
- Header row: № · ФИО · Профессия/должность/разряд · Дата рождения · СНИЛС · Образование · Телефон · Контрагент · Программа · Вид подготовки
- Шапка: предприятие+ИНН, наименование программы, вид подготовки; блок согласия ПДн и гарантии оплаты в бланке

### Round 4 — 2026-11-16 — answered

| Q | Status | Answer |
|---|--------|--------|
| Q13 | settled | **C** — отдельный эпик AI admission parse **до** B2B enroll |
| Q14 | settled | **B** — MVP: Course+Program+Batch; категории/разделы/уроки follow-up |
| Q15 | settled | **A** — единый Learner Profile |
| Q16 | deferred | Bitrix «висит в воздухе» — не SoT решения в этом PLAN; reconcile later |

### Round 5 — 2026-11-16 — answered

| Q | Status | Answer |
|---|--------|--------|
| Q17 | settled | Если email нет → **синтетические данные для входа** в учебный контур; админы потом сами раздают креды людям |

---

## Q→A log

| ID | Answer | Notes |
|----|--------|-------|
| Q1 | multi-epic by surfaces | |
| Q2b | B | flags + квота |
| Q3b | payment webhook ≈D | |
| Q4 | C | view-all |
| Q5 | A без 1С | + AI-parse перед B2B |
| Q6 | A | org seats |
| Q7 | A | Active после parse+квота |
| Q8 | D | payment port |
| Q9 | анкета+сканы→pay→enroll | |
| Q10–Q11 | XLSX бланк | fixtures |
| Q12 | весь граф | MVP = Q14 |
| Q13 | C | AI-parse epic first |
| Q14 | B | Course+Program+Batch |
| Q15 | A | unified Learner Profile |
| Q16 | defer | Bitrix в воздухе |
| Q17 | synthetic creds | админы раздают креды later |

## CRITICAL open

- [x] Q17 — synthetic credentials без email

## Defer-list

| Item | Owner | Next |
|------|-------|------|
| Bitrix vs native SoT статуса заявки | APP / product | отдельный reconcile / CLARIFY revisit |
| 1С счета для физлиц | APP | вне текущего cut; backlog |
| AI-parse кривых/сканов сверх табличного бланка | APP | внутри/после эпика AI-parse |
| Custom fields на Category/Chapter/Lesson | APP | follow-up после form-builder MVP |
| Конкретный платёжный вендор | APP | адаптер после Payment port |

---

## Completion Report

- **status:** `done`
- **Grill:** done · verdict=needs_user_Q→resolved · rounds=5 · grill_Q=17 · mode=frontier
- **Ready for:** `APP PLAN` Phase 1 — **multi-epic** по поверхностям
- **Surfaces (order):**
  1. `T-A10` (proposed) B2C admission: Learner Profile + сканы → Payment port/webhook → Enrollment
  2. `T-A11` (proposed) AI admission parse: XLSX бланк → neftegaz-ai-layer → structured rows (+ synthetic creds)
  3. `T-A12` (proposed) B2B enroll + org quotas (depends on T-A11)
  4. `T-A13` (proposed) Custom fields MVP: Course + Program + Batch
  5. `T-A14` (proposed) Platform admin view-all organizations
- **Out of cut:** 1С; Bitrix SoT; full learning-graph custom fields beyond C/P/B
- **Fixtures:** `memory-bank/app/clarify/fixtures-20261116-admission/`
- **design_pack:** product_ui / D0

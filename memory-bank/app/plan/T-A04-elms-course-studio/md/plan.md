# [T-A04 | elms-course-studio] PLAN

**Дата:** 2026-11-09  
**Режим:** APP PLAN → APP DECOMPOSE → APP IMPLEMENT  
**Уровень:** L1  
**Статус:** planned  
**Related:** `memory-bank/product/modules.md`, `rules/elms-design.mdc`  
**SUSPENSION GUARD:** active — plan output unlimited (§0.0)

## Решение

Вместо разрозненных форм `ELMS Course Chapter` и `ELMS Course Lesson` добавляется единый Course Studio. Методист открывает курс на одном маршруте и видит вложенную структуру «курс → разделы → уроки», редактор выбранного элемента и свойства/правила прохождения. Сохранение отправляет один вложенный payload, а сервер сохраняет существующие DocType `ELMS Course`, `ELMS Course Chapter`, `ELMS Course Lesson` и `ELMS Quiz`, проверяя роли, принадлежность дочерних записей и ограничения удаления по прогрессу.

## Product outcome

Методист может создать или открыть курс, добавить и переставить разделы и уроки, связать quiz без ручного перехода в дочерние записи, сохранить черновик, открыть предпросмотр для слушателя и опубликовать курс. Слушательский player продолжает читать ту же сохранённую структуру.

## Context consumed

| Источник | Что учитывается |
|---|---|
| `memory-bank/product/modules.md` | Канонические LMS DocTypes, роли `ELMS Methodologist`, `ELMS Operations User`, `ELMS Admin` и learner-facing structure |
| `rules/elms-approach.mdc` | Frappe + custom `elms`, существующие LMS сущности как продуктовый канон |
| `rules/elms-design.mdc` | Светлый служебный UI, cobalt action, scoped CSS и клавиатурная доступность |
| `elms/elms/lms/api.py` | Текущий API структуры курса, прогресса, quiz и права на сервере |
| `elms/elms/public/js/desk-learning.js` | Текущая LMS management surface и переходы из неё |

## User stories

| ID | Story | Priority | Independent test |
|---|---|---:|---|
| US-001 | Как методист, я открываю один Course Studio вместо отдельных форм раздела и урока. | P0 | Route and UI contract test |
| US-002 | Как методист, я собираю курс в outline и сохраняю порядок разделов/уроков одним действием. | P0 | Nested save/reload test |
| US-003 | Как методист, я добавляю, переименовываю, переставляю и удаляю элементы outline. | P0 | API/UI contract assertions |
| US-004 | Как методист, я выбираю quiz для quiz-урока без ручного редактирования дочерней записи. | P1 | Editor payload and quiz-link test |
| US-005 | Как методист, я вижу learner preview и publish state курса. | P1 | Route controls and persisted state test |
| US-006 | Как слушатель, я продолжаю видеть тот же курс через сохранённую структуру. | P0 | Existing learner structure regression |

## Functional requirements

### FR-001 — Course-first authoring surface

Course Studio доступен по `/app/elms-course-studio[/<course>]` ролям, которые управляют каталогом. Экран содержит outline курса слева, редактор выбранного курса/раздела/урока по центру и свойства/правила прохождения справа. В интерфейсе не требуется открывать `ELMS Course Chapter` или `ELMS Course Lesson` отдельно.

### FR-002 — Nested persistence

`get_course_editor_data(course=None)` возвращает курс, вложенные главы и уроки в порядке `idx`, доступные quiz и текущий publish state. `save_course_draft(payload)` принимает метаданные курса, ordered chapters/lessons, optional quiz links и deletion lists; сервер создаёт/обновляет связи, нормализует порядок и возвращает payload с именами записей.

### FR-003 — Server-side safety

Оба метода требуют аутентифицированного пользователя с ролью `ELMS Admin`, `ELMS Operations User`, `ELMS Methodologist`, `System Manager` или `Administrator`. Сервер проверяет принадлежность каждой дочерней записи курсу, отклоняет неизвестные parents/children и не удаляет урок, по которому есть прогресс. Learner, Guest и unrelated authenticated users получают отказ.

### FR-004 — Authoring controls and continuity

Studio поддерживает add/reorder/remove, draft save, preview и publish state. Quiz link выбирается внутри урока. Learner player использует существующий `get_course_structure`; Studio не создаёт параллельную модель курса.

## Contract and acceptance criteria

| ID | Acceptance criterion | Evidence |
|---|---|---|
| AC-001 | Authenticated manager API returns nested data and validates ownership. | `test_course_studio.py` |
| AC-002 | Workspace and management course actions route to Studio. | `test_learning_ui.py`, `test_workspaces.py` |
| AC-003 | Multi-chapter course saves and reloads in correct order with relationships. | `test_course_studio.py` |
| AC-004 | Learner structure and preview read persisted chapter/lesson records. | `test_lms_core.py` |
| AC-005 | Backend, frontend syntax/contract and local wire checks pass. | shard `verify` and implement evidence |

## Explicit traceability

| Plan requirement | Decompose coverage |
|---|---|
| FR-001 | index `requirements_coverage.FR-001` → s01; shard `plan_contract.ui_contract` and route files |
| FR-002 | index `requirements_coverage.FR-002` → s01; shard `plan_contract.api`, `persistence` and API file |
| FR-003 | index `requirements_coverage.FR-003` → s01; shard `roles`, API tests and ownership checks |
| FR-004 | index `requirements_coverage.FR-004` → s01; shard UI contract and wire_complete |
| AC-001…AC-005 | index coverage → s01; shard checkpoints cp1…cp5 and `verify` commands |

## Stage and outcome

- Stage: `s01-course-studio-vertical-slice` — one mixed vertical slice from management entrypoint to persisted nested records and learner read path.
- Outcome: course-first authoring studio backed by existing LMS DocTypes, with no manual child-record linking in the primary authoring journey.
- Replacement cleanup: direct workspace authoring links for `ELMS Course Chapter` and `ELMS Course Lesson` are removed from the primary management path in favour of the Studio entrypoint.

## Scope

- Course-first route `/app/elms-course-studio[/<course>]`.
- Nested outline с add/reorder/remove и выбранным item editor.
- API `get_course_editor_data` и `save_course_draft` с серверной авторизацией и ownership validation.
- Workspace/management shortcuts направляют создание и открытие курса в Studio.
- Существующие quiz DocTypes остаются источником истины; полноценный bank authoring и AI/document import не входят в этот эпик.

## Delivery closure

| Capability | Production entrypoint | Success evidence |
|---|---|---|
| Course-first authoring | LMS Workspace/management → Course Studio | UI contract tests and route/assets checks |
| Nested persistence | `get_course_editor_data` / `save_course_draft` | ownership, ordering, deletion and reload tests |
| Learner continuity | existing `get_course_structure` / player | LMS core regression tests |
| Wire readiness | registered assets + live local endpoint | syntax, grep contract and local smoke checks |

## Requirements

| ID | Requirement | Step |
|---|---|---|
| FR-001 | One Course Studio surface replaces separate child-record authoring | s01 |
| FR-002 | Course metadata and ordered nested chapters/lessons save in one payload | s01 |
| FR-003 | Server validates roles, ownership and safe deletion of progressed lessons | s01 |
| FR-004 | Add, reorder, remove, draft save, preview, publish state and quiz selection | s01 |
| AC-001 | Authenticated manager API returns nested data and validates ownership | s01 |
| AC-002 | Workspace and management actions route to Studio | s01 |
| AC-003 | Multi-chapter course reloads with correct order and relationships | s01 |
| AC-004 | Learner structure remains backed by persisted records | s01 |
| AC-005 | Targeted backend/frontend/wire checks pass | s01 |

## Non-goals

- AI or document import.
- Full quiz/question authoring inside Studio.
- Real-time multi-author collaboration.

## Verification contract

- Backend: targeted Course Studio and LMS core tests.
- Frontend: targeted learning/workspace contract tests plus `node --check` for production assets.
- Wire: Python syntax, API/asset call-site search, route registration and local asset/API smoke checks.
- Browser acceptance is a later APP QA gate; this implementation slice keeps the local wire smoke named and evidence-backed.

## Plan

Один mixed vertical slice `s01-course-studio-vertical-slice.yaml` покрывает backend, frontend, wire integration, tests и локальную проверку. После реализации обязательны `verify-implement`, scope check и machine finish; commit/PR не выполняются без отдельного запроса.

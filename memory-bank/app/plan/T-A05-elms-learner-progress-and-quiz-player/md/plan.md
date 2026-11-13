# [T-A05 | elms-learner-progress-and-quiz-player] PLAN

**Дата:** 2026-11-12  
**Режим:** APP PLAN → APP DECOMPOSE → APP IMPLEMENT → APP QA  
**Уровень:** L2  
**Статус:** planned  
**Clarify:** [memory-bank/app/clarify/clarify-20261111-learner-progress-and-quiz-player.md](../../../clarify/clarify-20261111-learner-progress-and-quiz-player.md)  
**Prompt:** [md/prompt.md](prompt.md) — outcome SoT  
**Queue:** `memory-bank/app/roadmap/queue.yaml` → `T-A05` / `T-A05-elms-learner-progress-and-quiz-player`  
**Batch:** `elms-learner-progress`  
**Deps:** `T-A02-elms-learning-core-flows`  
**SUSPENSION GUARD:** active — plan output unlimited

## Решение

Замкнуть существующий LMS-контур в одном mixed vertical slice: слушатель получает опубликованный quiz с вариантами ответа, сохраняет незавершённую попытку, возвращается к ней и видит количество отвеченных вопросов; сотрудник с настроенным правом открывает карточку слушателя и видит текущий прогресс, программы, курсы, действия и историю по годам. Источниками остаются существующие `ELMS Enrollment`, `ELMS Program Enrollment`, `ELMS Course Progress`, `ELMS Lesson Progress`, `ELMS Quiz Attempt` и `ELMS User Activity`; отдельная параллельная модель прогресса не создаётся.

## Context consumed

| Источник | Что вошло в план |
|---|---|
| `memory-bank/app/clarify/clarify-20261111-learner-progress-and-quiz-player.md` | Решения владельца: доступ через роли/права, полный набор метрик, сохраняемый quiz draft, все существующие типы вопросов, безопасное раскрытие результатов, история программ/курсов/действий/годов |
| `memory-bank/product/modules.md` | Канонические роли `ELMS Learner`, `ELMS Instructor`, `ELMS Operations User`, `ELMS Admin`; LMS-сущности и правило learner self-only |
| `memory-bank/product/lms-best-practices.md` | Разделение Practice/Assessment, server-side grading, аудит активности и защита персональных данных |
| `rules/elms-approach.mdc` | Frappe + custom app `elms`; LMS — продуктовый домен; API через whitelist и Document API |
| `rules/elms-design.mdc` и `memory-bank/product/design.md` | Светлый scoped LMS UI, cobalt action, компактный Desk surface и учебная IA |
| `elms/elms/lms/api.py` | Текущие quiz payload/attempt, lesson/course progress, learning relationships и learner dashboard; найденный gap — нет persisted draft/resume и user-profile history |
| `elms/elms/public/js/desk-learning.js` | Текущий player рендерит quiz только после start, progress tab показывает только курс текущего пользователя, management surface не открывает progress profile |
| `elms/elms/tests/test_lms_core.py`, `elms/elms/tests/test_learning_ui.py` | Существующие security, quiz payload, server grading, progress calculation и UI contract checks для расширения без регрессии |

## Clarifications

- Session: 2026-11-12, владелец продукта; Phase 0 завершён в clarify-артефакте.
- Доступ к чужому прогрессу не привязывается к одной зашитой роли: capability определяется Frappe DocPerm/User Permission; слушатель всегда ограничен собственными данными.
- История пользователя — наблюдаемая сводка обучения: программы, курсы, зачисления, завершённые уроки, quiz start/submit и последний activity, сгруппированные по календарному году.
- Edge cases (пустой quiz, invalid options, expired/abandoned attempt, cross-user read) закрываются acceptance и QA; открытых CRITICAL нет.

## Product outcome (WHAT)

Проблема не в отсутствии отдельных полей, а в разрыве наблюдаемого учебного цикла: в курсе должен быть реальный путь «вопрос → вариант ответа → сохранение → результат → прогресс», а у уполномоченного сотрудника — единая карточка слушателя с историей обучения. Успехом считается, что пользователь может продолжить незавершённый тест, а доступный по правам сотрудник видит, что слушатель изучал и чего достиг в каждом году.

### Product decision / WHAT

| Поле | Решение / evidence | Влияние на план |
|---|---|---|
| **Reframe** | Learner progress inspector + resumable quiz player, а не отдельный dashboard-only виджет | Один эпик владеет back, front и wire journey |
| **Demand / status quo** | В текущем player есть server-side attempt и поля вариантов, но draft не возобновляется, counters не видны, а user history не открывается из management surface | Расширяем существующие контракты и проверяем runtime-связку quiz lesson → published quiz → questions |
| **Narrowest wedge** | Один экран карточки слушателя + один путь прохождения quiz в существующем `/app/elms-learning` | Массовые отчёты и организационная аналитика остаются вне scope |
| **Explicit non-goals** | Сертификаты, экзаменационный протокол, ФИС ФРДО, ручная проверка, новый LMS, полный bank editor | Не объявляем assessment/compliance полностью готовыми |
| **Success signal** | Слушатель возобновляет draft и завершает quiz; authorized viewer открывает user и видит history по годам без чужих данных | Проверяется backend + frontend + wire + live smoke |
| **Decision** | `proceed` | Phase 1 закрыт, можно переходить к DECOMPOSE |

## Delivery closure

| Capability / outcome | Classification | Production entrypoint and caller | Success / failure enforcement | Independent outcome test | Foundation approval / follow-up |
|---|---|---|---|---|---|
| Resumable quiz progress | `vertical_slice` | `/app/elms-learning` → quiz lesson → `save_quiz_progress` / `submit_quiz` | Ответы валидируются по frozen snapshot; learner payload не содержит `correct`; закрытая/чужая/просроченная попытка отклоняется | Backend test creates attempt, saves partial answers, resumes, submits and checks counters/status | `n/a` |
| Learner course/program history | `vertical_slice` | LMS management → selected learner → `get_learner_profile` | Server applies source DocPerm/User Permission and self-only rule; unauthorized target returns PermissionError | Backend test compares grouped years, course/program statuses and activity without cross-user leakage | `n/a` |
| Learner player and progress summary | `vertical_slice` | `/app/elms-learning` → My Courses / Progress / Player | Empty, missing quiz, draft, passed and failed states are visible and actionable | Frontend contract + wire journey asserts real API data and resume UI | `n/a` |

## User stories

| ID | Story | Priority | Independent test |
|---|---|---:|---|
| US-001 | Как слушатель, я открываю quiz-урок и вижу варианты ответа для каждого вопроса, не видя ключ правильного ответа. | P0 | API payload test + player contract test |
| US-002 | Как слушатель, я сохраняю частично заполненный quiz, возвращаюсь к нему и вижу `отвечено/всего` до отправки. | P0 | Attempt save/resume/submit behavior test |
| US-003 | Как слушатель, я вижу по своим курсам процент, уроки, время, последний вход, quiz counters, score и status. | P0 | Learner dashboard/progress response test |
| US-004 | Как сотрудник с настроенным правом, я нажимаю на слушателя и вижу его программы, курсы, действия и историю обучения по годам. | P0 | Role-aware learner profile wire journey |
| US-005 | Как сотрудник без права, я не могу получить профиль или прогресс чужого слушателя через прямой API вызов. | P0 | Fail-closed permission/isolation test |
| US-006 | Как методист, я публикую quiz с валидными вариантами и связываю его с quiz-уроком; learner получает тот же persisted quiz contract. | P1 | Published linkage/options validation regression |

### Acceptance scenarios — US-001

- **Given:** опубликованный `ELMS Quiz` связан с quiz-уроком активного зачисления и имеет вопросы с валидными options.
- **When:** слушатель открывает урок и запускает попытку.
- **Then:** player показывает текст вопроса и `id/text` вариантов для `Single Choice`, `Multiple Choice`, `True/False`; поля `correct` и explanation для Assessment отсутствуют.

### Acceptance scenarios — US-002

- **Given:** у слушателя есть активная попытка с 5 вопросами, из них выбраны ответы на 2.
- **When:** player вызывает сохранение и закрывается, затем слушатель снова открывает quiz.
- **Then:** сервер возвращает ту же активную попытку, `answered_questions=2`, `total_questions=5`, выбранные варианты восстановлены; новая параллельная попытка не создаётся.

### Acceptance scenarios — US-003

- **Given:** у слушателя есть enrollment, lesson progress и quiz attempts.
- **When:** он открывает личный прогресс.
- **Then:** видит процент курса, `completed/total lessons`, time spent, last activity, `answered/total questions`, score и статус каждой попытки; при Passed quiz-урок учитывается в course progress согласно существующему правилу.

### Acceptance scenarios — US-004

- **Given:** target user имеет enrollment в курсах и/или program enrollment за разные годы, а viewer имеет настроенное read permission.
- **When:** viewer выбирает пользователя из LMS management surface.
- **Then:** открывается профиль с summary и секциями «Текущие курсы», «Программы», «История по годам», «Активность»; в каждой записи видны человекочитаемые названия, статус, дата/год и progress.

### Acceptance scenarios — US-005

- **Given:** viewer не имеет права чтения LMS progress/history либо target не является текущим learner.
- **When:** viewer вызывает профиль напрямую или меняет `user` в запросе.
- **Then:** сервер отвечает typed `PermissionError`/403 и не возвращает частичный payload; learner не может читать чужие записи.

### Acceptance scenarios — US-006

- **Given:** quiz lesson указывает на опубликованный quiz, а вопрос содержит options JSON с уникальными `id`, `text` и серверным `correct`.
- **When:** методист публикует и learner запускает quiz.
- **Then:** валидные варианты попадают в player; invalid/missing options или missing published link дают понятное состояние ошибки, а не пустой тест.

## Functional requirements

### FR-001 — Quiz option contract and safe payload

- Сохранить существующие типы `Single Choice`, `Multiple Choice`, `True/False`.
- При чтении quiz сервер валидирует, что каждый вопрос имеет непустой массив вариантов с уникальным `id` и непустым `text`; некорректные данные отклоняются `ValidationError` с именем вопроса.
- Learner endpoints возвращают только `id`, `text`, type, question text, sequence, points и topic; `correct` и assessment explanation не передаются.
- Published quiz должен принадлежать course enrollment и быть связан с текущим quiz lesson; отсутствие связи возвращает `DoesNotExistError`/понятное empty state.

### FR-002 — Persisted and resumable quiz attempt

- `start_quiz(quiz, enrollment)` создаёт попытку только при отсутствии активной; при наличии активной возвращает её как `resumed=true` с frozen snapshot и сохранёнными ответами.
- Новый whitelist method `save_quiz_progress(attempt, answers)` сохраняет только выбранные option ids из snapshot, пересчитывает `answered_questions`, `total_questions`, `progress_percentage` и `last_saved_at`, но не закрывает и не оценивает попытку.
- `submit_quiz(attempt, answers=None)` использует финальный payload или сохранённый draft, выполняет server-side grading, фиксирует score/status/submitted_at и обновляет counters; правильные ключи не возвращаются learner.
- После `Passed` quiz-урок закрывается через существующий `_complete_quiz_lesson`; `Failed`, `Abandoned`, time limit и max attempts сохраняют текущую политику и дают typed error/state.

### FR-003 — Course and learner progress projection

- Расширить learner dashboard/current progress payload полями `last_activity_at`, quiz summary (`answered_questions`, `total_questions`, `score_percentage`, `attempt_status`) и человекочитаемыми course/lesson labels.
- Не менять базовое правило course progress: процент считается по обязательным урокам; quiz completion учитывается через завершение quiz-урока.
- Не создавать отдельный history DocType: history собирается из enrollment, program enrollment, course/lesson progress, quiz attempts и user activity.

### FR-004 — Role/permission-controlled learner profile

- Добавить server method `get_learner_profile(user=None)` с target по умолчанию = current session user.
- Для `user == session_user` разрешить self view по существующим learner permissions.
- Для другого target требовать настроенное read permission на соответствующие LMS source records и применять Frappe User Permission/organization isolation; UI role flags не являются механизмом безопасности.
- Output включает `user`, `summary`, `current_courses`, `programs`, `history_by_year`, `activity`; activity ограничивается учебными событиями и не раскрывает необязательные сетевые поля в UI.
- Каждый history item содержит год, дату, program/course/lesson/quiz label, event type, status и progress snapshot; источники с отсутствующими связями не ломают весь профиль.

### FR-005 — Player, profile and state UX

- В player: question cards, radio/checkbox controls, answered counter, save state, resume banner, submit action, loading/disabled/error states.
- Practice result: score, passed/failed, answered count и разрешённое explanation; Assessment result: score/status/topic summary без correct key.
- В management: кликабельный learner result из существующего relationship/admin search и отдельный profile surface с курсами, программами, history by year и activity.
- Пустые состояния: нет зачислений, нет истории, нет quiz, quiz без вопросов, нет права, истёкшая попытка; каждый state имеет понятное действие/сообщение.
- Scoped CSS использует токены ELMS/neftegaz-ai-layer, остаётся на русском и поддерживает клавиатурную навигацию для вариантов и таблиц.

### FR-006 — Audit and privacy

- Save, resume, submit, pass/fail и denied profile read фиксируются в `ELMS User Activity` с reference на attempt/profile target без answer key.
- Сервер проверяет ownership, enrollment status, quiz/course relation, active attempt, deadline и option ids.
- Любой direct API вызов без разрешения получает typed 403/validation response; UI не маскирует denial пустым успешным результатом.

## Contract & API specifications

### `POST /api/method/elms.lms.api.save_quiz_progress`

Input:

```json
{
  "attempt": "ATTEMPT-2026-001",
  "answers": "{\"Q-1\":[\"A\"],\"Q-2\":[\"B\",\"C\"]}"
}
```

Success:

```json
{
  "message": {
    "attempt": "ATTEMPT-2026-001",
    "status": "In Progress",
    "answered_questions": 2,
    "total_questions": 5,
    "progress_percentage": 40.0,
    "answers": {"Q-1": ["A"], "Q-2": ["B", "C"]},
    "last_saved_at": "2026-11-12 14:30:00"
  }
}
```

Errors: `PermissionError` for another user, `ValidationError` for invalid question/option ids or closed attempt, `DoesNotExistError` for missing attempt, `ValidationError` for expired deadline.

### `POST /api/method/elms.lms.api.get_learner_profile`

Input: `{ "user": "learner@example.ru" }`; omitted `user` means current session user.

Success shape:

```json
{
  "message": {
    "user": {"name": "learner@example.ru", "full_name": "Иван Слушатель"},
    "summary": {"courses": 2, "completed_courses": 1, "programs": 1, "last_activity_at": "2026-11-12 14:30:00"},
    "current_courses": [],
    "programs": [],
    "history_by_year": [{"year": 2026, "programs": [], "courses": [], "events": []}],
    "activity": []
  }
}
```

Errors: `PermissionError`/403 if target is not self and source read permissions fail; `DoesNotExistError` for an explicit nonexistent user; no partial success payload on denial.

### Existing contract extensions

- `get_lesson_quiz` and `start_quiz` include sanitized options plus `attempt`, `answers`, `answered_questions`, `total_questions`, `progress_percentage`, `resumed`.
- `submit_quiz` accepts optional `answers`, returns counters and safe result; it never returns `correct` flags for Assessment.
- `get_learner_dashboard` includes the same quiz/course summary for self view, preserving existing keys for current UI.

## UI journey and wire completion

1. Authorized learner opens `/app/elms-learning` → **Мои курсы** → **Открыть обучение**.
2. Player loads structure and quiz-safe payload; if an active attempt exists, it shows **Продолжить тест** and restored answers.
3. Learner chooses options; UI calls save endpoint on explicit save and bounded change/heartbeat policy, displays `N из M`; submit calls server grading and refreshes course progress.
4. Authorized staff searches **Слушатели** in management, opens a learner result, and sees profile/history grouped by year. The target is passed to the real API, not held in mock state.
5. Wire failure checks cover expired attempt, bad option, missing quiz link, denied target, empty history and backend outage; each has visible state and no silent fallback.

## Ownership matrix (mixed vertical slice)

| Lane | Component / artifact | Responsibility |
|---|---|---|
| Backend / data | `elms/elms/lms/api.py`, quiz attempt/progress DocType manifests/controllers | Persist draft answers/counters, resume, safe payload, profile/history projection, permission checks, activity audit |
| Frontend / Desk | `elms/elms/public/js/desk-learning.js`, `desk-learning.css`, route/workspace surface | Quiz controls, save/resume/result states, progress counters, learner profile/history journey |
| Domain / RBAC | LMS DocPerm, User Permission and existing `permissions.py`/install seed | Make viewer capability configurable by roles/permissions; keep learner self-only and fail closed |
| Tests | `elms/elms/tests/test_lms_core.py`, `test_learning_ui.py`, targeted wire/live checks | Behavior, security, payload redaction, UI contracts and real endpoint journey |
| QA | `memory-bank/app/qa/T-A05-elms-learner-progress-and-quiz-player/` | Mixed lanes: backend, frontend_build, browser/wire_journey, live_smoke, leftover_sot |

## Scope

- Existing LMS player: answer options, all three current question types, server-side grading, persisted draft/resume and question counters.
- Existing LMS progress: course/lesson/quiz summaries for learner and role-controlled target profile.
- User history grouped by calendar year with programs, courses, statuses, progress and learning activity.
- Permission-aware management entrypoint from current learner search/relationships.
- Targeted DocType/API/UI tests, syntax/build checks and real local wire journey.

## Non-goals

- Certificates, exam commission protocols, FIS FRDO/EISOT export and manual instructor grading.
- New external LMS, RAG/assistant integration, mass organization analytics or cohort dashboards.
- Full quiz/question bank editor inside Course Studio; existing LMS DocType forms remain the authoring source.
- Replacing `ELMS Course Progress`/`ELMS Quiz Attempt` with a second event-sourced model.

## Verification contract / APP QA charter

| Lane | Required? | Contract |
|---|---:|---|
| `backend` | yes | Targeted Frappe/pytest behavior: option redaction/validation, save/resume/submit, counters, history grouping, permission isolation, activity audit |
| `frontend_build` | yes | `node --check` for changed JS, targeted `test_learning_ui.py`, no mock-only learner profile path |
| `browser` | yes | Parent-only Playwright/manual browser journey: learner opens quiz, selects options, saves/resumes/submits; viewer opens user profile/history; denial/empty states |
| `wire_journey` | yes | Real Frappe route/API calls with persisted records from published quiz lesson through profile; response envelope and error mapping |
| `live_smoke` | yes | `scripts/live_smoke.sh` or stack-profile equivalent against live local HTTP; no ASGI/mock substitute |
| `leftover_sot` | yes | Search for stale final-only quiz path, answer-key leakage, role hardcoding, mock profile data and duplicate progress models |
| `behavior_smoke` | yes | Full selected catalog checks from APP charter; every non-run item has reason and next action |

Required catalog responsibilities: schema/migration, authz/isolation, backend behavior, API contract, frontend asset/build, browser journey, live HTTP and regression for T-A02/T-A04 surfaces. No lane may be marked PASS only from pytest when browser/frontend/live are required.

## Plan review passes

- **Product:** done in Phase 0; wedge = learner detail + resumable quiz; history by year added to outcome; non-goals explicit.
- **Design:** done by existing ELMS design canon; decisions = player-first hierarchy, visible counters, table/profile history, keyboard-safe controls, explicit empty/error states.
- **DX:** done; contracts specify method/path, input/output, typed errors, safe payload and resume semantics.
- **Eng:** done; one APP epic owns persistence, API, UI, wire and mixed QA; no INTEG child; existing source DocTypes remain SoT.

## Decompose handoff

APP DECOMPOSE must turn this plan into a bounded mixed tree. Recommended seams are:

- `s01-quiz-attempt-progress-and-safe-api` — attempt schema/API, option validation, resume/save/submit and backend behavior/security tests.
- `s02-learner-profile-history-and-player-wire` — profile/history API, player/profile UI, route/workspace entrypoint, frontend/wire/live checks and regression.

The first mandatory production consumer (player/profile UI) stays in this same APP epic. DECOMPOSE owns exact file allowlists, shard contracts, test catalog selection and verify commands.

## Done criterion

The epic is done only when all of the following are true:

1. A published quiz lesson visibly offers valid answer options for all supported types without exposing answer keys.
2. A learner can save, leave, resume and submit one active attempt; answered/total counters and score/status are persisted and visible.
3. Course and learner progress show lessons, time, last activity, quiz counters, score/status, programs and history grouped by year.
4. A viewer with configured read permissions can open a selected learner; a viewer without permission and a learner targeting another user receive fail-closed denial.
5. Backend, frontend_build, browser, wire_journey, live_smoke, leftover_sot and behavior_smoke required lanes pass with evidence.
6. Existing T-A02 enrollment/progress, T-A04 Course Studio and learner self-only behavior remain regression-free.

### Next phase

`APP DECOMPOSE T-A05-elms-learner-progress-and-quiz-player`

# clarify — learner-progress-and-quiz-player

**plan_id:** T-A05-elms-learner-progress-and-quiz-player
**slug:** learner-progress-and-quiz-player
**role:** app
**date:** 2026-11-12
**feature_description:** Пользователь должен проходить опубликованный курс с вариантами ответа в quiz-уроках, видеть сохранённый прогресс и число отвеченных вопросов. Уполномоченный сотрудник должен открыть слушателя и увидеть его прогресс по курсам.
**status:** done

---

## Контекст и цель

- Вход: запрос владельца продукта от 2026-11-11; текущий LMS player, quiz API и Course Progress.
- Цель сессии CLARIFY: зафиксировать границы доступа, состав прогресса и поведение quiz перед APP PLAN Phase 1.
- Ограничения: один APP vertical slice; production code на Phase 0 не изменяется.

## Grill pass (Phase 0 — mandatory)

| Поле | Значение |
|------|----------|
| **Reframe** | Нужно не просто добавить поле «процент», а замкнуть учебный цикл: слушатель открывает курс, получает варианты ответа, сохраняет ответы/результат, а куратор видит доказуемый прогресс этого слушателя по каждому курсу. |
| **Premises** | 1) `ELMS Course Progress` и `ELMS Lesson Progress` остаются сводным источником прогресса — accepted, подтверждено `modules.md` и текущим API. 2) Варианты ответа выдаются без ключа правильного ответа — accepted, подтверждено `_quiz_public_questions`. 3) Прогресс должен быть виден через настраиваемые роли и права, а слушатель — только себе — accepted, решение владельца. 4) Число отвеченных вопросов и незавершённые ответы сохраняются — accepted, решение владельца. 5) Карточка пользователя показывает историю обучения по программам, курсам, действиям и годам — accepted, дополнительное решение владельца. |
| **Weakest link** | Неправильно настроенные DocPerm/User Permission могут открыть чужой прогресс, поэтому endpoint и DocType должны проверять доступ на сервере независимо от UI; история должна группироваться по году без потери текущего статуса. |
| **Anti-scope** | Сертификаты, протокол комиссии, ФИС ФРДО, задания с ручной проверкой, новый внешний LMS и полноценный redesign Course Studio не входят в эту итерацию. |
| **Verdict** | `needs_user_Q` → resolved — ответы владельца закрыли persona/access, набор метрик, user history и правила показа результата; evidence зафиксирован в Q→A. |
| **Design tree (sketch)** | 1) кто смотрит прогресс → 2) какие метрики видны → 3) сохраняется ли незавершённая попытка → 4) какие типы вопросов/результаты показываются → 5) какие empty/error состояния нужны → 6) mixed API/UI/QA contract. |

## Product probe (office-hours lite, optional)

| # | Вопрос | Контекст / Ответ |
|---|--------|------------------|
| 1 | **Demand reality** | Запрос владельца продукта от 2026-11-11: при открытии курса нет рабочих вариантов ответа и не видно, сколько вопросов пройдено; также нужен просмотр прогресса выбранного пользователя/ученика. |
| 2 | **Status quo** | В текущем коде есть server-side quiz attempt и lesson/course progress, но management surface группирует связи вокруг курса, а player не даёт отдельного user-progress journey; фактический runtime-gap требует закрытия end-to-end. |
| 3 | **Desperate specificity** | Нельзя пройти quiz как слушатель и нельзя одним действием открыть карточку слушателя с курсами, процентом, уроками и вопросами. |
| 4 | **Narrowest wedge** | Один learner detail journey + один quiz player journey: список курсов слушателя, детализация курса и безопасный выбор вариантов с сохранением/отправкой ответов. |
| 5 | **Observation & surprise** | Backend уже ожидает `Single Choice`, `Multiple Choice`, `True/False` и `options_json`; проблема может быть в связке опубликованный quiz → quiz-урок → вопрос/варианты, поэтому acceptance должен проверять реальный payload, а не только наличие полей. |
| 6 | **Future-fit** | Будущие экзаменационные протоколы и сертификаты могут расширить результат попытки, поэтому этот эпик фиксирует только совместимый progress/attempt contract и не объявляет аттестацию полностью готовой. |

- **Reframe:** учебный цикл должен быть наблюдаемым и возобновляемым для слушателя и проверяемым куратором.
- **Premises (3–5 falsifiable):** см. Grill pass; решения владельца закрыли access, persistence, disclosure и history.
- **Recommended wedge:** роль-зависимый learner detail с историей + quiz player с безопасными вариантами, server-side grading и question progress.

## Таксономия сканирования

| Категория | Status | Notes |
|-----------|--------|-------|
| scope | Clear | Role/permission-driven user profile, course/quiz progress и history по годам. |
| data | Clear | Course/Lesson/Quiz/Attempt + persisted in-progress answers/counters + history projection. |
| UX-API | Clear | Learner detail, quiz resume/save/submit, history grouping и empty/error states. |
| NFR | Clear | Server-side isolation, 152-ФЗ boundary и отсутствие answer key в learner payload. |
| integrations | Clear | Внешних интеграций для этого среза нет. |
| edge | Partial | Empty quiz, invalid options, abandoned attempt, cross-user access, repeat attempts. |
| constraints | Clear | Frappe whitelist + native LMS DocTypes + scoped ELMS UI. |
| terminology | Clear | Канон: `ELMS Learner`, `Course Progress`, `Lesson Progress`, `Quiz Attempt`. |
| design_skills (FRONT UI) | n/a | APP mixed slice; визуальный канон задан `rules/elms-design.mdc`. |

## Frontier rounds

### Round 1

- Q1 → A: доступ к карточке слушателя настраивается ролями и правами; слушатель видит только себя. `resolved`.
- Q2 → A: сохраняются процент курса, уроки, время, последний вход, отвеченные/все вопросы, балл и статус теста; незавершённые ответы сохраняются. `resolved`.
- Q3 → A: показываются варианты всех существующих типов; правильные ответы скрыты; Practice показывает объяснение, Assessment — только итог. `resolved`.

## Q→A log

### Q1

- **Question:** Кто может открыть карточку слушателя и видеть его прогресс по курсам?
- **Why it matters:** Это определяет серверную авторизацию, персональные данные и UI entrypoint.
- **Recommended:** доступ задаётся ролями и DocPerm/User Permission; `ELMS Learner` видит только собственные данные.
- **Options:** A — рекомендованный набор ролей | B — только Admin/Operations | C — любой авторизованный пользователь
- **Answer:** доступ должен настраиваться ролями и правами; слушатель видит только себя.
- **resolution:** resolved
- **round:** 1

### Q2

- **Question:** Что именно считать прогрессом теста и курса?
- **Why it matters:** От этого зависят поля API, расчёт процента и строка прогресса в карточке пользователя.
- **Recommended:** по курсу — `%`, завершённые/все уроки, время, последний вход; по quiz — отвеченные/все вопросы, попытка, балл и статус; незавершённые ответы сохраняются.
- **Options:** A — рекомендованный полный минимум | B — только процент уроков | C — процент уроков + только финальный балл теста
- **Answer:** полный минимум; незавершённые ответы сохраняются.
- **resolution:** resolved
- **round:** 1

### Q3

- **Question:** Какие правила показа вопросов и результата нужны в первой версии?
- **Why it matters:** Нельзя отдавать ключ правильных ответов и нужно определить поведение Practice/Assessment.
- **Recommended:** показать варианты для всех трёх существующих типов; learner получает только `id/text`; Practice после отправки показывает результат/объяснение, Assessment — только итоговый статус и балл без ключа.
- **Options:** A — рекомендованный безопасный режим | B — показывать правильные ответы после каждого вопроса | C — только Single Choice в первой версии
- **Answer:** рекомендованный безопасный режим.
- **resolution:** resolved
- **round:** 1

## Deferred / [НУЖНО УТОЧНИТЬ] items

| Item | Severity | Why deferred | Next |
|------|----------|--------------|------|
| — | — | Открытых CRITICAL нет | — |

## Completion Report

- **Grill:** done · verdict=needs_user_Q → resolved · rounds=1 · grill_Q=3 · mode=frontier
- **Asked:** 3/20
- **Resolved:** настраиваемый RBAC/DocPerm с изоляцией ученика, полный набор метрик и возобновляемый quiz, безопасное раскрытие результатов, история обучения по программам/курсам/действиям/годам, текущий LMS/Frappe контур, narrowest wedge, отсутствие внешних интеграций.
- **Deferred:** n/a — открытых CRITICAL нет.
- **Coverage:** scope=Clear · data=Clear · UX-API=Clear · NFR=Clear · integrations=Clear · edge=Partial (закрывается acceptance) · constraints=Clear · terminology=Clear · design_pack=n/a
- **Next action:** `APP PLAN learner-progress-and-quiz-player` Phase 1.

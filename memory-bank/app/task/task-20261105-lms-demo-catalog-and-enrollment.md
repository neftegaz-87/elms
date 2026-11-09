---
execution: direct-ad-hoc
status: complete
date: 2026-11-05
---

# LMS demo-каталог и самостоятельное обучение

## Intent

Заполнить ELMS демонстрационными курсами по российской нефтегазовой отрасли и
довести пользовательский путь до рабочего состояния: слушатель видит каталог
опубликованных потоков, записывается на доступный курс, открывает уроки,
фиксирует активное время и видит процент прохождения.

Продолжение задачи: довести учебный контур до реального контроля знаний по
паттернам Frappe Learning и требованиям ELMS — тренировочные тесты, итоговая
проверка, попытки, серверная оценка и связь результата с прогрессом.

## Contract impact

- Существующий серверный enrollment-flow сохраняет проверки пользователя,
  потока, дублей и квоты.
- Добавляется отдельный learner endpoint для каталога и self-enrollment;
  управленческие API и DocPerm не ослабляются.
- Demo seed идемпотентен, не создаёт пользователей/пароли и не изменяет
  существующие пользовательские зачисления; для уже существующих локальных
  demo-пользователей (`erokhin.a@nftgz.ru`, `elms.test.admin@elms.local`,
  `elms.test.one@elms.local`) он создаёт отсутствующие зачисления на демо-потоки.
- Seed запускается явно через bench execute, а не автоматически на каждом
  обновлении приложения.
- Правильные ответы и критерии оценки никогда не отправляются клиенту для
  итоговой проверки; срез вопросов хранится на сервере в попытке.

## Files allowlist

- `elms/elms/lms/api.py`
- `elms/elms/lms/demo.py`
- `elms/elms/public/js/desk-learning.js`
- `elms/elms/public/css/desk-learning.css`
- `elms/elms/tests/test_lms_core.py`
- `elms/elms/tests/test_learning_ui.py`
- `elms/elms/desk/workspaces.py`
- `elms/elms/tests/test_workspaces.py`
- `elms/elms/lms/doctype/elms_quiz/elms_quiz.json`
- `elms/elms/lms/doctype/elms_quiz/elms_quiz.py`
- `elms/elms/lms/doctype/elms_quiz_question/elms_quiz_question.json`
- `elms/elms/lms/doctype/elms_quiz_question/elms_quiz_question.py`
- `elms/elms/lms/doctype/elms_quiz_attempt/elms_quiz_attempt.json`
- `elms/elms/lms/doctype/elms_quiz_attempt/elms_quiz_attempt.py`
- `memory-bank/product/modules.md`
- `memory-bank/app/task/task-20261105-lms-demo-catalog-and-enrollment.md`

## Verification lanes

- backend: required — targeted LMS unit/contract tests
- frontend: required — learning UI contract tests and JavaScript syntax check
- wire: required — inspect API/JS contract; live browser not available unless
  local stack is running
- live_smoke: skipped — no request or named deployment target

## Selected skills

- none; repository-local APP task workflow and ELMS rules are sufficient

## Loop-safety preflight

`memory-bank/activeContext.md` points to a completed T-A02 shard and only its
queue index is loadable; none of the allowlisted production paths overlap with
that completed shard. Direct-ad-hoc task therefore does not advance loop state
or edit `activeContext`, roadmap, plan, decompose, or implement artifacts.

## Evidence

- `bin/pytest -q elms/elms/tests/test_lms_core.py elms/elms/tests/test_learning_ui.py` — **17 passed**.
- `python3 -m py_compile elms/elms/lms/api.py elms/elms/lms/demo.py` — passed.
- `node --check elms/elms/public/js/desk-learning.js` — passed.
- `docker compose ... exec backend bench --site elms.localhost execute elms.lms.demo.seed_demo_data` — seeded **3 courses, 3 batches, 12 lessons** and demo enrollments for existing demo users.
- Repeated seed command — same result; database counts remain **3 courses / 12 lessons**, confirming idempotency.
- Live bench execution of `elms.lms.api.get_course_catalog` returned three published active batches for `Administrator`.
- Live smoke/browser lane skipped: no browser acceptance was requested; local backend/catalog endpoint was checked through bench.

- `bin/pytest -q elms/elms/tests/test_lms_core.py elms/elms/tests/test_learning_ui.py elms/elms/tests/test_workspaces.py` — **26 passed**.
- `python3 -m py_compile ...` and `node --check elms/elms/public/js/desk-learning.js` — passed after assessment changes.
- `bench --site elms.localhost migrate` — created/updated quiz DocTypes and workspace links.
- Repeated `bench --site elms.localhost execute elms.lms.demo.seed_demo_data` — stable **3 courses, 3 batches, 12 lessons, 2 quizzes, 6 questions**.
- Public quiz payload strips the `correct` flag; assessment results return only failed topics.
- Live API smoke for `erokhin.a@nftgz.ru` and `elms.test.admin@elms.local` returned **3 learner courses, 3 managed courses, 3 catalog courses and 3 preview courses**.

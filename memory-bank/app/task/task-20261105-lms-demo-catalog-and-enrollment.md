---
execution: direct-ad-hoc
status: in-progress
date: 2026-11-05
---

# LMS demo-каталог и самостоятельное обучение

## Intent

Заполнить ELMS демонстрационными курсами по российской нефтегазовой отрасли и
довести пользовательский путь до рабочего состояния: слушатель видит каталог
опубликованных потоков, записывается на доступный курс, открывает уроки,
фиксирует активное время и видит процент прохождения.

## Contract impact

- Существующий серверный enrollment-flow сохраняет проверки пользователя,
  потока, дублей и квоты.
- Добавляется отдельный learner endpoint для каталога и self-enrollment;
  управленческие API и DocPerm не ослабляются.
- Demo seed идемпотентен и не создаёт пользователей/пароли и не изменяет
  существующие пользовательские зачисления.
- Seed запускается явно через bench execute, а не автоматически на каждом
  обновлении приложения.

## Files allowlist

- `elms/elms/lms/api.py`
- `elms/elms/lms/demo.py`
- `elms/elms/public/js/desk-learning.js`
- `elms/elms/public/css/desk-learning.css`
- `elms/elms/tests/test_lms_core.py`
- `elms/elms/tests/test_learning_ui.py`
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

Pending implementation and verification.

---
execution: direct-ad-hoc
status: complete
date: 2026-11-05
---

# Полноценный учебный контур ELMS: программы и контроль знаний

## Intent

Расширить работающий LMS-срез паттернами Frappe Learning: learning paths
(программы из нескольких курсов), порядок курсов, вопросник, попытки теста,
проходной балл и роли методиста/инструктора. Пользователь должен видеть
программу, записаться на неё, пройти открытый курс и сдать тест; сервер должен
сам проверять доступ, ответы и итоговый прогресс.

## Contract impact

- Всё остаётся в custom app `elms`; Frappe Education/Learning не устанавливается.
- Новые сущности имеют собственные DocType и серверные whitelist-методы.
- `ELMS LMS User` не получает право редактировать учебный каталог или ответы.
- `ELMS Methodologist` управляет курсами, программами, уроками и тестами;
  `ELMS Instructor` видит учебный процесс и проверяет результаты.
- Сертификаты ФИС ФРДО, протокол комиссии и assignments с файлами остаются
  следующим production-эпиком; этот срез не называет completion certificate
  юридическим документом.

## Files allowlist

- `elms/elms/install.py`
- `elms/elms/lms/api.py`
- `elms/elms/lms/demo.py`
- `elms/elms/lms/doctype/elms_enrollment/elms_enrollment.json`
- `elms/elms/lms/doctype/elms_course_lesson/elms_course_lesson.json`
- `elms/elms/lms/doctype/elms_course_lesson/elms_course_lesson.py`
- `elms/elms/lms/doctype/elms_course/elms_course.json`
- `elms/elms/lms/doctype/elms_course_chapter/elms_course_chapter.json`
- `elms/elms/lms/doctype/elms_program/**`
- `elms/elms/lms/doctype/elms_program_course/**`
- `elms/elms/lms/doctype/elms_program_enrollment/**`
- `elms/elms/lms/doctype/elms_quiz/**`
- `elms/elms/lms/doctype/elms_quiz_question/**`
- `elms/elms/lms/doctype/elms_quiz_attempt/**`
- `elms/elms/public/js/desk-learning.js`
- `elms/elms/public/css/desk-learning.css`
- `elms/elms/tests/test_lms_core.py`
- `elms/elms/tests/test_learning_ui.py`
- `elms/elms/tests/test_roles_rbac.py`
- `elms/elms/tests/test_workspaces.py`
- `memory-bank/product/modules.md`
- `memory-bank/app/task/task-20261105-lms-learning-paths-assessments.md`

## Verification lanes

- backend: required — targeted LMS tests, schema validation, migration/seed
- frontend: required — learning UI contract tests and JavaScript syntax check
- wire: required — local bench endpoint checks and seeded data checks
- live_smoke: skipped — no production deploy or named external target

## Selected references

- `docs/vendor/learning/add-a-program.md`
- `docs/vendor/learning/others/course-progress-calculation.md`
- `docs/vendor/learning/assignments.md`
- `docs/vendor/learning/roles.md`

## Loop-safety preflight

`memory-bank/activeContext.md` points to the completed T-A02 shard and no active
production step overlaps this allowlist. This is a direct-ad-hoc task: do not
edit `activeContext`, roadmap, plan/decompose or implement artifacts and do not
run loop finish commands.

## Evidence

- `bin/pytest -q elms/elms/tests/test_lms_core.py elms/elms/tests/test_learning_ui.py elms/elms/tests/test_workspaces.py elms/elms/tests/test_roles_rbac.py` — **39 passed**.
- `python3 -m py_compile ...` and `node --check elms/elms/public/js/desk-learning.js` — passed.
- `bench --site elms.localhost migrate` — created/updated Program, Program Course, Program Enrollment, Quiz, Quiz Question and Quiz Attempt DocTypes; workspace links applied.
- Repeated `bench --site elms.localhost execute elms.lms.demo.seed_demo_data` — stable **3 courses, 1 program, 3 batches, 12 lessons, 2 quizzes, 6 questions**.
- Live `elms.lms.api.get_program_catalog` returned **1 published program with 3 ordered courses**.
- Live role check returned `ELMS Admin`, `ELMS Operations User`, `ELMS LMS User`, `ELMS Instructor`, `ELMS Methodologist`.
- Learner-facing quiz payload omits answer keys; assessment responses expose only failed topics.
- Production deploy/live smoke skipped; local dev stack only.

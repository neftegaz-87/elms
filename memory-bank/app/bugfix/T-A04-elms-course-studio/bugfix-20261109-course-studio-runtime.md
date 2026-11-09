# APP BUGFIX — Course Studio runtime and LMS relationships

## Root cause

The reported validation message came from the native `ELMS Course Lesson` form, not from Course Studio. The live frontend access log shows `/app/elms-course-lesson/new-elms-course-lesson` at 16:46. The installed `Workspace LMS` still contained direct Chapter/Lesson links because the runtime workspace record had not been synchronized with the canonical `elms.desk.workspaces` definition. A new child record had no parent course, so Frappe correctly rejected the save with the required Course Name value.

## Changes Implemented

- Synchronized the live LMS workspace and retained `after_migrate -> ensure_workspaces` as the source-of-truth sync path.
- Added a route guard that sends direct Chapter/Lesson authoring routes to Course Studio.
- Added human title/search fields to Course, Chapter, Lesson, Quiz, Batch, Program and Subscription DocTypes.
- Added `get_learning_relationships` with manager authorization and course-root grouping.
- Replaced the independent management-card dump with a relationship search and linked entity groups.
- Added a nested relationship outline: `Course → Chapter → Lesson`, with the chapter name repeated on every lesson row.
- Added program membership order/mandatory state and made the course view show every program containing the course; batches remain a separate course-level calendar context.
- Added an explicit `Создать поток` action in LMS management and a `Создать поток для курса` action on each course relationship card; the latter preselects the course in the Batch form.

## Acceptance

- Course creation is course-first and does not open a child form with an empty required course link.
- A single search for a stream or course groups the course with its program, batch, subscription, enrollments, chapters, lessons and quiz.
- A course with multiple program memberships shows each program separately, while lessons are rendered under their owning chapter.
- A manager can create a Batch from the management surface or directly from the selected course relationship.
- Course, Chapter, Lesson and Quiz links can be resolved using human-readable titles as well as IDs.
- Existing unrelated LMS learner/player flows remain outside this bugfix scope.

## Verification

- `./bin/pytest -q elms/elms/tests/test_course_studio.py elms/elms/tests/test_lms_core.py elms/elms/tests/test_learning_ui.py elms/elms/tests/test_workspaces.py` — 46 passed.
- `node --check` for Course Studio and learning assets — passed.
- Live `save_course_draft` smoke created and removed a temporary course successfully.
- Live relationship query for `Демо-поток 2026 · Стропальные работы` returned one course root and its batch, program, subscription, four enrollments, chapters, lessons and quiz.
- Authenticated browser check opened `/app/elms-learning`, searched the demo batch, and observed two chapter groups with four nested lesson rows; a temporary second program confirmed both programs render under the same course and was removed.
- Authenticated browser check created a temporary course in Course Studio, saved a full title plus chapter and lesson, reloaded the route, and confirmed all three values persisted; temporary records were removed.
- Live `frappe.desk.search.search_link` now returns course/lesson titles instead of only IDs.
- Typed receipt: `runtime-verification-20261109T181045Z.json`.

## Deferred environment limitation

The existing browser harness has no `.venv/bin/python` and no authenticated manager journey, so BF-003 is explicitly cancelled as an environment/test-harness follow-up rather than claimed as a product pass. The application contracts and live API smoke remain covered.

# T-A05 runtime evidence — 2026-11-12

## Migration and schema

Command:

```text
docker compose -f docker/compose.dev.yaml exec -T backend bench --site elms.localhost migrate
```

Result: `EXIT:0`. The command was repeated after the hook repair and completed with `after_migrate` hooks and search-index queueing.

Live MariaDB columns in `tabELMS Quiz Attempt`:

```text
answered_questions     int(11)          NOT NULL DEFAULT 0
total_questions        int(11)          NOT NULL DEFAULT 0
progress_percentage    decimal(21,9)    NOT NULL DEFAULT 0.000000000
last_saved_at          datetime(6)      NULL
```

## Backend and UI tests

```text
test_lms_core.py -k "quiz or attempt or option or learner_profile or history or activity"
9 passed, 10 deselected

test_learning_ui.py -k "learning or quiz or progress or profile"
18 passed

test_access_model.py -k "group or profile or permission"
4 passed, 3 skipped, 1 deselected
```

Syntax and whitespace checks for the touched implementation paths exited `0`.

## Authenticated live wire

Using the dev login session for `Administrator`:

```text
POST /api/method/elms.lms.api.get_learner_dashboard  -> 200
POST /api/method/elms.lms.api.get_learner_profile    -> 200
```

The dashboard response contains `authenticated: true`, `active_enrollments_count`, `courses`, `activities`, `last_activity_at`, and `last_login_at`. The profile response contains `summary`, `current_courses`, `programs`, `history_by_year`, and `activity`.

## Authenticated browser wire

Playwright opened `/app/elms-learning` with the same session:

- route status: `200`;
- learning API calls: all `200`;
- course and progress panes: present;
- `.elms-error-state`: absent;
- 375px viewport: no horizontal overflow after tab wrapping fix;
- screenshot: `/tmp/elms-learning-authenticated.png`.

The generic login-only harness still reports unrelated existing SSO/login assertions, and Socket.IO reports an unrelated Unauthorized/Not Found console error. Neither affected the learning API calls.

# T-A05 APP QA frozen checklist

## AC+

- AC+-001: schema migration completes and is idempotent;
- AC+-002: `answered_questions`, `total_questions`, `progress_percentage`, and `last_saved_at` exist in the live quiz-attempt table;
- AC+-003: targeted quiz/attempt/profile/UI tests pass;
- AC+-004: authenticated dashboard and learner-profile HTTP methods return 200;
- AC+-005: authenticated `/app/elms-learning` renders course/progress panes with learning API responses at 200;
- AC+-006: mobile learning tabs do not create horizontal overflow;
- AC+-007: permission denial and safe quiz payload behavior remain covered;

## AC-

- AC--001: no `answered_questions` SQL exception remains on the authenticated dashboard/profile path;

## §0.11

- BN-001: the live route uses the migrated schema rather than a status-only or UI-only fallback;
- BN-002: generic login/SSO findings are explicitly separated from the T-A05 learner-progress verdict;

## Prior blockers

- PB-001: prior runtime blocker was `Unknown column 'answered_questions' in 'SELECT'`;
- PB-002: migration hook previously failed on an empty mandatory `User Group.user_group_members` table.

---
execution: direct-ad-hoc
task: company-admin-platform-access
date: 2026-11-14
status: completed
---

# Company Admin: platform learning access

## Intent and root cause

`ELMS Company Admin` currently receives only the B2B workspace. The product
contract requires a company representative to use the learner-facing platform
and the organization cabinet, while remaining unable to create organizations,
assign other Company Admins, edit the global catalogue, or inspect foreign
organizations.

The existing LMS surface already separates learner APIs from management APIs,
but the Company Admin role was incorrectly treated as a learner-only role:
management navigation and the Course Studio were hidden. Company Admin is a
full LMS manager with B2B operations constrained to its own organization.

## Contract impact

- Platform owner: `ELMS Admin` keeps global LMS/Operations/Settings access.
- Company branch: `ELMS Company Admin` gets the full LMS surface, Course
  Studio, preview, cohorts, enrollment, progress and assessment management;
  B2B operations remain limited to its own organization and its employees.
- Individual: `ELMS Learner` keeps own learning access.
- Company Admin is not a composition of `ELMS Learner`; the two roles have
  separate responsibilities.

## Files allowlist

- `elms/elms/desk/workspaces.py`
- `elms/elms/install.py`
- `elms/elms/sso/roles.py`
- `elms/elms/permissions.py`
- `elms/elms/access/api.py`
- `elms/elms/public/js/desk-access.js`
- `elms/elms/lms/api.py`
- `elms/elms/lms/page/elms_learning/elms_learning.json`
- `elms/elms/lms/page/elms_course_studio/elms_course_studio.json`
- `elms/elms/lms/page/elms_course_preview/elms_course_preview.json`
- `elms/elms/operations/page/elms_access/elms_access.json`
- `elms/elms/operations/page/elms_cabinet/elms_cabinet.json`
- `elms/elms/tests/test_access_model.py`
- `elms/elms/tests/test_access_invite.py`
- `elms/elms/tests/test_lms_core.py`
- `elms/elms/tests/test_learning_ui.py`
- `elms/elms/tests/test_workspaces.py`
- `elms/elms/tests/test_workspaces_runtime.py`
- `elms/elms/tests/test_roles_rbac.py`
- `elms/elms/tests/test_sso_config.py`
- `elms/elms/tests/test_sso_ensure.py`
- `memory-bank/product/modules.md`
- `docker/keycloak/realm-elms.json`
- `docker/keycloak/entrypoint.sh`
- `docker/keycloak/seed-demo-users.sh`
- `docker/compose.dev.yaml`
- `docker/.env.dev.example`
- `docker/.env.dev` (local ignored runtime credential)
- `memory-bank/app/task/task-20261114-company-admin-platform-access.md`

## Verification lanes

- required backend: targeted access/LMS/workspace pytest suite
- required frontend contract: targeted learning UI tests and JavaScript syntax
- required runtime: `bench migrate`, authenticated workspace/page/role readback
- skipped: broad browser journey and live smoke; no new external integration or
  browser behavior beyond role-filtered navigation

## Selected skills

- `tdd`
- `python-testing-patterns`
- `verification-before-completion`

## Evidence

- `python3 -m pytest -q` on the targeted access/LMS/workspace/UI/RBAC/SSO
  modules: `136 passed, 10 skipped, 5 subtests passed`.
- `python3 -m py_compile` passed for the changed Python modules; `sh -n` and
  `python3 -m json.tool` passed for the Keycloak runtime files.
- `bench --site elms.localhost migrate` passed after the navigation and role
  changes.
- Runtime readback confirms `elms.test.admin@elms.local` is restored to
  `ELMS Admin Profile` / `ELMS Admin` and sees `LMS`, `Предпросмотр курсов`,
  `B2B Access`, `Settings`.
- Runtime readback confirms the new Company Admin sees `LMS`,
  `Предпросмотр курсов`, `Моя компания`; global `B2B Access` and its page are
  restricted to `ELMS Admin`.
- The new Keycloak account `elms.test.company.admin@elms.local` has group
  `/ELMS Company Admins`, realm role `employee`, and a successful password
  grant (`HTTP 200`). Its Frappe account has `ELMS Company Admin Profile`,
  `Desk User`, `ELMS Company Admin`, and membership in the demo organization.
- The LMS workspace runtime contains the Course Studio shortcut and links for
  courses, programs, batches, enrollments, quizzes, and progress.
- Removed an invalid Keycloak `scopeMappings` import field exposed while
  recreating the dev container; Keycloak now starts and seeds all four demo
  accounts.
- Course Studio and Course Preview Page roles include Company Admin; runtime
  Custom DocPerm grants Company Admin RWCD on the LMS surface.
- Company Admin may invite a learner or another Company Admin only through an
  organization membership it owns; creating organizations and assigning
  Company Admin through the central assignment action remain platform-admin
  operations.

The unrelated pre-existing cabinet test failure involving `page_size > 500`
was not changed.

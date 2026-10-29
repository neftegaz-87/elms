# Bugfix: Roles & RBAC Suite Alignment & Silent Fallback Purge
**Epic ID:** T-B02-elms-roles-rbac  
**Date:** 2026-10-28  
**Author:** BACK BUGFIX  
**Source:** memory-bank/back/qa/T-B02-elms-roles-rbac/qa-20261028-roles-rbac.yaml

---

## 1. QA Root Cause Analysis
During full test suite execution in BACK QA (`bin/pytest`), the suite failed:
- `AssertionError` at `bin/pytest` line 5 asserting obsolete `["Core", "Operations", "LMS"]` in `elms/elms/modules.txt`.
- AC− gap identified during verify-qa: silent fallback in `elms/elms/install.py:92,96` where `ensure_section_perms` used `return` and `continue` when db or DocType was missing.
- AC− gap identified during verify-qa: silent Custom DocPerm fallback in `elms/elms/install.py:99` where `ensure_section_perms` silently skipped permissions synchronization when `Custom DocPerm` DocType was missing.

**Root Causes:**
1. In epic `T-B02-elms-roles-rbac`, the modules list was aligned to `Core`, `Operations`, `LMS` (replacing obsolete `Operations`), but `bin/pytest` still asserted `["Core", "Operations", "LMS"]`. In addition, `bin/pytest` was not invoking the unit test suite `elms.tests.test_roles_rbac`.
2. `ensure_section_perms` returned silently when `frappe.db` was None or skipped missing section DocTypes using `continue`, violating fail-closed requirements (AC-6, AC--1).
3. `ensure_section_perms` checked `if frappe.db.exists("DocType", "Custom DocPerm"):` and silently skipped permission synchronization when Custom DocPerm was unavailable instead of failing closed with `frappe.throw`.

---

## 2. Changes Implemented (AC+)
- `bin/pytest`: Updated assertion to check for `["Core", "Operations", "LMS"]` in `elms/elms/modules.txt`.
- `bin/pytest`: Added execution of `PYTHONPATH=elms python3 -m unittest elms.tests.test_roles_rbac`.
- `elms/elms/install.py`: Replaced silent `return` and `continue` in `ensure_section_perms` with fail-closed `frappe.throw(...)` exceptions.
- `elms/elms/install.py`: Replaced silent `if frappe.db.exists("DocType", "Custom DocPerm"):` check with fail-closed check raising `frappe.throw("Required DocType 'Custom DocPerm' not found for ensure_section_perms.")`.
- `elms/elms/tests/test_roles_rbac.py`: Added unit tests `test_ensure_section_perms_fails_closed_when_db_absent`, `test_ensure_section_perms_fails_closed_when_doctype_missing`, and `test_ensure_section_perms_fails_closed_when_custom_docperm_missing`.
- `memory-bank/back/bugfix/T-B02-elms-roles-rbac/bugfix-queue.yaml`: Closed `BF-001`, `BF-002`, and `BF-003` with status `done`, verified suite execution, and set `verification.status: pass`.

---

## 3. Non-Goals / Fallback Purge (AC−)
- Purged silent fallbacks (`return` on missing db, `continue` on missing DocType, and silent bypass on missing `Custom DocPerm`) in `elms/elms/install.py`.
- No new fallback logic or test skips added.
- Fail-closed guarantees verified via explicit negative unit tests.

---

## 4. Integration Rule Counterparts (§0.11)
- Verified module taxonomy consistency across `modules.txt`, `modules.md`, and DocType fixtures.
- Preserved idempotent execution of `ensure_roles` and `ensure_section_perms` across install and migration hooks.
- No orphan references introduced.

---

## 5. Blockers Resolved
- BF-001: `suite_red:bin_pytest_modules_assertion_failure` — PASS
- BF-002: `ac_gap:silent_fallback_install_perms` — PASS
- BF-003: `ac_gap:silent_custom_docperm_fallback` — PASS

---

## 6. Verification
- Verification command:
  ```bash
  bin/pytest
  ```
  Result: 13 unit tests passed, 7 smoke checks passed (exit code 0).

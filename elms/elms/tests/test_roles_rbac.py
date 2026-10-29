import json
import os
import unittest
from unittest.mock import MagicMock, patch

import frappe
from elms.install import (
    ELMS_ADMIN_ROLE,
    ELMS_OPERATIONS_SECTION_DOCTYPE,
    ELMS_OPERATIONS_USER_ROLE,
    ELMS_LMS_SECTION_DOCTYPE,
    ELMS_LMS_USER_ROLE,
    ELMS_ROLES,
    ELMS_SETTINGS_SECTION_DOCTYPE,
    SECTION_DOCPERM_MATRIX,
    SECTION_DOCTYPES,
    ensure_roles,
    ensure_section_perms,
)

if not hasattr(frappe, "throw"):
    frappe.throw = lambda msg, *args, **kwargs: (_ for _ in ()).throw(Exception(msg))
if not hasattr(frappe, "db"):
    frappe.db = MagicMock()
if not hasattr(frappe, "new_doc"):
    frappe.new_doc = MagicMock()
if not hasattr(frappe, "get_doc"):
    frappe.get_doc = MagicMock()

# Setup simulated session & has_permission for isolated unit testing
if not hasattr(frappe, "session"):
    class Session:
        user = "Guest"
    frappe.session = Session()

if not hasattr(frappe, "set_user"):
    def set_user(user: str) -> None:
        frappe.session.user = user
    frappe.set_user = set_user


def get_doctype_json_permissions(doctype: str) -> list[dict]:
    """Load DocPerm permissions directly from the on-disk DocType JSON manifest."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    path_map = {
        ELMS_OPERATIONS_SECTION_DOCTYPE: os.path.join(
            base_dir, "operations", "doctype", "elms_operations_section", "elms_operations_section.json"
        ),
        ELMS_LMS_SECTION_DOCTYPE: os.path.join(
            base_dir, "lms", "doctype", "elms_lms_section", "elms_lms_section.json"
        ),
        ELMS_SETTINGS_SECTION_DOCTYPE: os.path.join(
            base_dir, "elms_core", "doctype", "elms_settings_section", "elms_settings_section.json"
        ),
    }
    manifest_path = path_map.get(doctype)
    if not manifest_path or not os.path.exists(manifest_path):
        return []
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("permissions", [])


TEST_USERS_ROLES: dict[str, list[str]] = {
    "Administrator": ["Administrator", "System Manager"],
    "admin_user@elms.local": [ELMS_ADMIN_ROLE],
    "operations_user@elms.local": [ELMS_OPERATIONS_USER_ROLE],
    "lms_user@elms.local": [ELMS_LMS_USER_ROLE],
    "Guest": ["Guest"],
}


def simulate_has_permission(doctype: str, ptype: str = "read", user: str | None = None) -> bool:
    """Simulate Frappe has_permission based on DocType manifest and user roles."""
    current_user = user or getattr(frappe.session, "user", "Guest")
    if current_user == "Administrator":
        return True

    roles = set(TEST_USERS_ROLES.get(current_user, [current_user]))
    permissions = get_doctype_json_permissions(doctype)

    for rule in permissions:
        if rule.get("role") in roles and rule.get(ptype, 0):
            return True
    return False


if not hasattr(frappe, "has_permission"):
    frappe.has_permission = simulate_has_permission


class TestRolesRBACSeed(unittest.TestCase):
    def test_roles_constants_defined(self):
        self.assertEqual(ELMS_ADMIN_ROLE, "ELMS Admin")
        self.assertEqual(ELMS_OPERATIONS_USER_ROLE, "ELMS Operations User")
        self.assertEqual(ELMS_LMS_USER_ROLE, "ELMS LMS User")
        self.assertEqual(
            ELMS_ROLES,
            ("ELMS Admin", "ELMS Operations User", "ELMS LMS User"),
        )
        self.assertEqual(ELMS_OPERATIONS_SECTION_DOCTYPE, "ELMS Operations Section")
        self.assertEqual(ELMS_LMS_SECTION_DOCTYPE, "ELMS LMS Section")
        self.assertEqual(ELMS_SETTINGS_SECTION_DOCTYPE, "ELMS Settings Section")
        self.assertEqual(
            SECTION_DOCTYPES,
            ("ELMS Operations Section", "ELMS LMS Section", "ELMS Settings Section"),
        )

    def test_ensure_roles_creates_all_three_roles(self):
        existing_roles = set()

        def fake_exists(doctype, name):
            if doctype == "Role":
                return name in existing_roles
            return False

        created_docs = []

        def fake_new_doc(doctype):
            doc = MagicMock()
            doc.doctype = doctype

            def fake_insert():
                existing_roles.add(doc.role_name)
                created_docs.append(doc.role_name)

            doc.insert.side_effect = fake_insert
            return doc

        mock_db = MagicMock()
        mock_db.exists.side_effect = fake_exists

        with patch.object(frappe, "db", mock_db), patch.object(
            frappe, "new_doc", side_effect=fake_new_doc
        ):
            ensure_roles()

        self.assertEqual(
            set(created_docs),
            {"ELMS Admin", "ELMS Operations User", "ELMS LMS User"},
        )
        self.assertTrue(all(fake_exists("Role", r) for r in ELMS_ROLES))

    def test_ensure_roles_idempotent_no_duplicate_error(self):
        existing_roles = {"ELMS Admin", "ELMS Operations User", "ELMS LMS User"}

        def fake_exists(doctype, name):
            if doctype == "Role":
                return name in existing_roles
            return False

        mock_db = MagicMock()
        mock_db.exists.side_effect = fake_exists

        with patch.object(frappe, "db", mock_db), patch.object(
            frappe, "new_doc"
        ) as mock_new_doc:
            ensure_roles()
            mock_new_doc.assert_not_called()

    def test_ensure_roles_fails_closed_on_missing_role(self):
        mock_db = MagicMock()
        mock_db.exists.return_value = False

        fake_throw = MagicMock(side_effect=RuntimeError("Role missing"))

        with patch.object(frappe, "db", mock_db), patch.object(
            frappe, "new_doc"
        ), patch.object(frappe, "throw", fake_throw):
            with self.assertRaises(RuntimeError):
                ensure_roles()
            fake_throw.assert_called()


class TestRolesRBACDocPermMatrix(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Guest")

    def tearDown(self):
        frappe.set_user("Guest")

    def test_admin_has_read_write_all_sections(self):
        """US-001, FR-004, TM-007: Admin has read/write (and create/delete) across all 3 sections."""
        admin_user = "admin_user@elms.local"
        frappe.set_user(admin_user)

        for doctype in SECTION_DOCTYPES:
            self.assertTrue(
                frappe.has_permission(doctype, "read", user=admin_user),
                f"Admin should have read access to {doctype}",
            )
            self.assertTrue(
                frappe.has_permission(doctype, "write", user=admin_user),
                f"Admin should have write access to {doctype}",
            )
            self.assertTrue(
                frappe.has_permission(doctype, "create", user=admin_user),
                f"Admin should have create access to {doctype}",
            )
            self.assertTrue(
                frappe.has_permission(doctype, "delete", user=admin_user),
                f"Admin should have delete access to {doctype}",
            )

    def test_operations_user_allowed_operations_denied_lms_and_settings(self):
        """US-002, BN-001, TM-001: Operations User has RW on Operations; denied LMS & Settings."""
        operations_user = "operations_user@elms.local"
        frappe.set_user(operations_user)

        self.assertTrue(frappe.has_permission(ELMS_OPERATIONS_SECTION_DOCTYPE, "read", user=operations_user))
        self.assertTrue(frappe.has_permission(ELMS_OPERATIONS_SECTION_DOCTYPE, "write", user=operations_user))
        self.assertFalse(frappe.has_permission(ELMS_OPERATIONS_SECTION_DOCTYPE, "create", user=operations_user))
        self.assertFalse(frappe.has_permission(ELMS_OPERATIONS_SECTION_DOCTYPE, "delete", user=operations_user))

        self.assertFalse(frappe.has_permission(ELMS_LMS_SECTION_DOCTYPE, "read", user=operations_user))
        self.assertFalse(frappe.has_permission(ELMS_LMS_SECTION_DOCTYPE, "write", user=operations_user))

        self.assertFalse(frappe.has_permission(ELMS_SETTINGS_SECTION_DOCTYPE, "read", user=operations_user))
        self.assertFalse(frappe.has_permission(ELMS_SETTINGS_SECTION_DOCTYPE, "write", user=operations_user))

    def test_lms_user_allowed_lms_denied_operations_and_settings(self):
        """US-003, BN-002, TM-002: LMS User has RW on LMS; denied Operations & Settings."""
        lms_user = "lms_user@elms.local"
        frappe.set_user(lms_user)

        self.assertTrue(frappe.has_permission(ELMS_LMS_SECTION_DOCTYPE, "read", user=lms_user))
        self.assertTrue(frappe.has_permission(ELMS_LMS_SECTION_DOCTYPE, "write", user=lms_user))
        self.assertFalse(frappe.has_permission(ELMS_LMS_SECTION_DOCTYPE, "create", user=lms_user))
        self.assertFalse(frappe.has_permission(ELMS_LMS_SECTION_DOCTYPE, "delete", user=lms_user))

        self.assertFalse(frappe.has_permission(ELMS_OPERATIONS_SECTION_DOCTYPE, "read", user=lms_user))
        self.assertFalse(frappe.has_permission(ELMS_OPERATIONS_SECTION_DOCTYPE, "write", user=lms_user))

        self.assertFalse(frappe.has_permission(ELMS_SETTINGS_SECTION_DOCTYPE, "read", user=lms_user))
        self.assertFalse(frappe.has_permission(ELMS_SETTINGS_SECTION_DOCTYPE, "write", user=lms_user))

    def test_guest_denied_all_sections(self):
        """US-004, BN-003, TM-003, AC-6: Guest denied read and write on all sections."""
        guest_user = "Guest"
        frappe.set_user(guest_user)

        for doctype in SECTION_DOCTYPES:
            for ptype in ("read", "write", "create", "delete"):
                self.assertFalse(
                    frappe.has_permission(doctype, ptype, user=guest_user),
                    f"Guest must be denied {ptype} on {doctype}",
                )

    def test_administrator_platform_user_not_blocked(self):
        """FR-009: Administrator platform user retains full access across all sections."""
        admin_platform = "Administrator"
        frappe.set_user(admin_platform)

        for doctype in SECTION_DOCTYPES:
            for ptype in ("read", "write", "create", "delete"):
                self.assertTrue(
                    frappe.has_permission(doctype, ptype, user=admin_platform),
                    f"Administrator must have {ptype} on {doctype}",
                )

    def test_ensure_section_perms_idempotent_synchronization(self):
        """Test ensure_section_perms creates and updates Custom DocPerm records."""
        custom_perms_db: dict[tuple[str, str], dict] = {}

        def fake_exists(doctype, name=None):
            if doctype == "DocType":
                if name in SECTION_DOCTYPES or name == "Custom DocPerm":
                    return True
            return False

        def fake_get_value(doctype, filters, fieldname):
            if doctype == "Custom DocPerm":
                key = (filters["parent"], filters["role"])
                if key in custom_perms_db:
                    return f"custom-perm-{filters['parent']}-{filters['role']}"
            return None

        def fake_get_doc(doctype, name):
            doc = MagicMock()
            doc.name = name
            def update(data):
                for k, v in data.items():
                    setattr(doc, k, v)
            doc.update.side_effect = update
            return doc

        def fake_new_doc(doctype):
            doc = MagicMock()
            doc.doctype = doctype
            def update(data):
                for k, v in data.items():
                    setattr(doc, k, v)
            doc.update.side_effect = update
            def fake_insert():
                custom_perms_db[(doc.parent, doc.role)] = {
                    "read": getattr(doc, "read", 0),
                    "write": getattr(doc, "write", 0),
                    "create": getattr(doc, "create", 0),
                    "delete": getattr(doc, "delete", 0),
                }
            doc.insert.side_effect = fake_insert
            return doc

        mock_db = MagicMock()
        mock_db.exists.side_effect = fake_exists
        mock_db.get_value.side_effect = fake_get_value

        with patch.object(frappe, "db", mock_db), patch.object(
            frappe, "new_doc", side_effect=fake_new_doc
        ), patch.object(frappe, "get_doc", side_effect=fake_get_doc):
            ensure_section_perms()
            self.assertEqual(len(custom_perms_db), 5)

            ensure_section_perms()
            self.assertEqual(len(custom_perms_db), 5)

    def test_ensure_section_perms_fails_closed_when_db_absent(self):
        """AC-6, AC--1: ensure_section_perms must fail closed when db is absent."""
        fake_throw = MagicMock(side_effect=RuntimeError("Database connection is not available"))

        with patch.object(frappe, "db", None), patch.object(frappe, "throw", fake_throw):
            with self.assertRaises(RuntimeError):
                ensure_section_perms()
            fake_throw.assert_called_once()
            self.assertIn("Database connection", fake_throw.call_args[0][0])

    def test_ensure_section_perms_fails_closed_when_doctype_missing(self):
        """AC-6, AC--1: ensure_section_perms must fail closed when DocType is missing."""
        mock_db = MagicMock()
        def fake_exists(doctype, name=None):
            if doctype == "DocType" and name in (ELMS_OPERATIONS_SECTION_DOCTYPE, "Custom DocPerm"):
                return True
            return False

        mock_db.exists.side_effect = fake_exists
        fake_throw = MagicMock(side_effect=RuntimeError("DocType missing"))

        with patch.object(frappe, "db", mock_db), patch.object(frappe, "throw", fake_throw):
            with self.assertRaises(RuntimeError):
                ensure_section_perms()
            fake_throw.assert_called()
            self.assertIn("Required DocType", fake_throw.call_args[0][0])
            self.assertIn(ELMS_LMS_SECTION_DOCTYPE, fake_throw.call_args[0][0])

    def test_ensure_section_perms_fails_closed_when_custom_docperm_missing(self):
        """AC-6, BF-003: ensure_section_perms must fail closed when Custom DocPerm is missing."""
        mock_db = MagicMock()
        def fake_exists(doctype, name=None):
            if doctype == "DocType" and name in SECTION_DOCTYPES:
                return True
            return False

        mock_db.exists.side_effect = fake_exists
        fake_throw = MagicMock(side_effect=RuntimeError("Custom DocPerm missing"))

        with patch.object(frappe, "db", mock_db), patch.object(frappe, "throw", fake_throw):
            with self.assertRaises(RuntimeError):
                ensure_section_perms()
            fake_throw.assert_called()
            self.assertIn("Required DocType 'Custom DocPerm' not found", fake_throw.call_args[0][0])


if __name__ == "__main__":
    unittest.main()

import json
import os
from typing import Any

import frappe

ELMS_ADMIN_ROLE: str = "ELMS Admin"
ELMS_OPERATIONS_USER_ROLE: str = "ELMS Operations User"
ELMS_LEARNER_ROLE: str = "ELMS Learner"
LEGACY_LEARNER_ROLE: str = "ELMS " + "LMS User"  # legacy migration only; never use for new access assignments
ELMS_INSTRUCTOR_ROLE: str = "ELMS Instructor"
ELMS_METHODOLOGIST_ROLE: str = "ELMS Methodologist"
ELMS_COMPANY_ADMIN_ROLE: str = "ELMS Company Admin"

ELMS_ROLES: tuple[str, ...] = (
    ELMS_ADMIN_ROLE,
    ELMS_OPERATIONS_USER_ROLE,
    ELMS_LEARNER_ROLE,
    ELMS_INSTRUCTOR_ROLE,
    ELMS_METHODOLOGIST_ROLE,
    ELMS_COMPANY_ADMIN_ROLE,
)

ELMS_OPERATIONS_SECTION_DOCTYPE: str = "ELMS Operations Section"
ELMS_REVIEW_SECTION_DOCTYPE: str = "ELMS Review Section"
ELMS_LMS_SECTION_DOCTYPE: str = "ELMS LMS Section"
ELMS_SETTINGS_SECTION_DOCTYPE: str = "ELMS Settings Section"
DESK_PAGE_DOCTYPE: str = "Page"

DEFAULT_COURSE_CATEGORIES: tuple[str, ...] = (
    "Охрана труда (ПП РФ № 2464)",
    "Промышленная безопасность (Ростехнадзор)",
    "Повышение квалификации (ДПО)",
    "Профессиональная переподготовка",
    "Корпоративный курс",
    "Электробезопасность",
)

SECTION_DOCTYPES: tuple[str, ...] = (
    ELMS_OPERATIONS_SECTION_DOCTYPE,
    ELMS_REVIEW_SECTION_DOCTYPE,
    ELMS_LMS_SECTION_DOCTYPE,
    ELMS_SETTINGS_SECTION_DOCTYPE,
)

SECTION_DOCPERM_MATRIX: dict[str, list[dict[str, Any]]] = {
    ELMS_OPERATIONS_SECTION_DOCTYPE: [
        {"role": ELMS_ADMIN_ROLE, "read": 1, "write": 1, "create": 1, "delete": 1},
        {"role": ELMS_OPERATIONS_USER_ROLE, "read": 1, "write": 1, "create": 0, "delete": 0},
    ],
    ELMS_REVIEW_SECTION_DOCTYPE: [
        {"role": ELMS_ADMIN_ROLE, "read": 1, "write": 1, "create": 1, "delete": 1},
        {"role": ELMS_OPERATIONS_USER_ROLE, "read": 1, "write": 1, "create": 0, "delete": 0},
        {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
    ],
    ELMS_LMS_SECTION_DOCTYPE: [
        {"role": ELMS_ADMIN_ROLE, "read": 1, "write": 1, "create": 1, "delete": 1},
        {"role": ELMS_LEARNER_ROLE, "read": 1, "write": 1, "create": 0, "delete": 0},
    ],
    ELMS_SETTINGS_SECTION_DOCTYPE: [
        {"role": ELMS_ADMIN_ROLE, "read": 1, "write": 1, "create": 1, "delete": 1},
        {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
    ],
}

APPROVED_ROLE_MAPPINGS: dict[str, list[str]] = {
    "Administrators": ["System Manager", ELMS_ADMIN_ROLE],
    "/Administrators": ["System Manager", ELMS_ADMIN_ROLE],
    "Employees": ["Employee"],
    "/Employees": ["Employee"],
    "Instructors": ["Instructor"],
    "/Instructors": ["Instructor"],
    "ELMS Instructors": [ELMS_INSTRUCTOR_ROLE],
    "/ELMS Instructors": [ELMS_INSTRUCTOR_ROLE],
    "Methodologists": [ELMS_METHODOLOGIST_ROLE],
    "/Methodologists": [ELMS_METHODOLOGIST_ROLE],
    "Students": ["Student"],
    "/Students": ["Student"],
}


def update_website_context(context: dict[str, Any]) -> dict[str, Any]:
    icon_url = "/assets/elms/images/nftgz-favicon.svg"
    result: dict[str, Any] = {"favicon": icon_url}
    if context.get("for_test") == "login.html":
        result["app_name"] = "elms"
        # Sole login path is the email/password form → Keycloak ROPC via login-keycloak.js.
        # Social Login Key stays enabled for callback/linking; the OAuth button is not shown.
        context["provider_logins"] = []
        context["social_login"] = False
        context["login_with_email_link"] = 0
        result["provider_logins"] = []
        result["social_login"] = False
        result["login_with_email_link"] = 0
    return result


if not hasattr(frappe, "ValidationError"):
    class ValidationError(Exception):
        pass
    frappe.ValidationError = ValidationError


class YandexSMTPDeliveryError(frappe.ValidationError):
    """Raised when Yandex SMTP delivery fails; masking delivery failure is forbidden (FR-016)."""

    pass


def ensure_roles() -> None:
    """Idempotently ensure required ELMS roles exist in Frappe.

    Fail-closed: if any role fails to create or is missing after creation,
    raises frappe.throw. Swallowing exceptions with try/except pass is strictly forbidden (AC--1).
    """
    migrate_legacy_learner_role()
    for role_name in ELMS_ROLES:
        if not frappe.db.exists("Role", role_name):
            doc = frappe.new_doc("Role")
            doc.role_name = role_name
            doc.flags.ignore_permissions = True
            doc.insert()

    # Fail-closed verification
    for role_name in ELMS_ROLES:
        if not frappe.db.exists("Role", role_name):
            frappe.throw(f"ELMS role '{role_name}' could not be created or found after ensure_roles.")


def migrate_legacy_learner_role() -> None:
    """Rename the old tautological learner role on existing sites."""
    if not frappe.db.exists("Role", LEGACY_LEARNER_ROLE):
        return
    if frappe.db.exists("Role", ELMS_LEARNER_ROLE):
        frappe.rename_doc("Role", LEGACY_LEARNER_ROLE, ELMS_LEARNER_ROLE, force=True, merge=True)
    else:
        frappe.rename_doc("Role", LEGACY_LEARNER_ROLE, ELMS_LEARNER_ROLE, force=True)


ROLE_PROFILES: dict[str, tuple[str, ...]] = {
    "ELMS Learner Profile": ("Desk User", ELMS_LEARNER_ROLE),
    "ELMS Instructor Profile": ("Desk User", ELMS_INSTRUCTOR_ROLE),
    "ELMS Methodologist Profile": ("Desk User", ELMS_METHODOLOGIST_ROLE),
    "ELMS Operations Profile": ("Desk User", ELMS_OPERATIONS_USER_ROLE),
    "ELMS Admin Profile": ("Desk User", ELMS_ADMIN_ROLE),
    "ELMS Company Admin Profile": ("Desk User", ELMS_COMPANY_ADMIN_ROLE),
}

GROUP_POLICIES: dict[str, tuple[str, str]] = {
    "ELMS Learners": ("Адресация слушателей и учебные рассылки.", "Членство не назначает роль; доступ задаётся профилем пользователя и User Permission."),
    "ELMS Instructors": ("Адресация преподавателей и кураторов.", "Членство не выдаёт права на потоки или оценки автоматически."),
    "ELMS Methodologists": ("Адресация методистов и авторов контента.", "Членство не заменяет ELMS Methodologist Profile."),
    "ELMS Operations": ("Адресация операторов учебного процесса.", "Членство не выдаёт доступ к Operations или данным организаций."),
    "ELMS Administrators": ("Адресация продуктовых администраторов ELMS.", "Членство не делает пользователя System Manager; профиль назначается отдельно."),
}


def ensure_role_profiles() -> None:
    """Seed the five supported user-facing role bundles."""
    if not frappe.db.exists("DocType", "Role Profile"):
        frappe.throw("Required DocType 'Role Profile' not found for ensure_role_profiles.")
    for profile_name, roles in ROLE_PROFILES.items():
        if frappe.db.exists("Role Profile", profile_name):
            doc = frappe.get_doc("Role Profile", profile_name)
            current_roles = tuple(row.role for row in doc.roles)
            if current_roles == roles:
                continue
        else:
            doc = frappe.new_doc("Role Profile")
            doc.role_profile = profile_name
        doc.set("roles", [])
        for role in roles:
            doc.append("roles", {"role": role})
        doc.flags.ignore_permissions = True
        if doc.is_new():
            doc.insert()
        else:
            doc.save()


def ensure_course_categories() -> None:
    """Seed editable course categories and preserve values from existing courses."""
    if not frappe.db.exists("DocType", "ELMS Course Category"):
        frappe.throw("Required DocType 'ELMS Course Category' not found for ensure_course_categories.")

    category_names = set(DEFAULT_COURSE_CATEGORIES)
    for row in frappe.get_all("ELMS Course", fields=["category"], limit_page_length=5000):
        value = str(row.get("category") or "").strip()
        if value:
            category_names.add(value)

    for category_name in sorted(category_names):
        if frappe.db.exists("ELMS Course Category", category_name):
            continue
        category = frappe.new_doc("ELMS Course Category")
        category.category_name = category_name
        category.is_active = 1
        category.flags.ignore_permissions = True
        category.insert()


def backfill_lms_display_links() -> None:
	"""Fill human-readable link targets on legacy progress and enrollment rows."""
	if frappe.db.exists("DocType", "ELMS Enrollment") and frappe.db.exists("DocType", "ELMS Course"):
		for row in frappe.get_all("ELMS Enrollment", fields=["name", "course", "course_name"], limit_page_length=0):
			if not row.get("course"):
				continue
			course_name = frappe.db.get_value("ELMS Course", row.get("course"), "course_name")
			if course_name and row.get("course_name") != course_name:
				frappe.db.set_value("ELMS Enrollment", row.get("name"), "course_name", course_name, update_modified=False)
			if frappe.db.exists("DocType", "ELMS Course Progress"):
				for progress in frappe.get_all("ELMS Course Progress", filters={"enrollment": row.get("name")}, fields=["name", "course_name"], limit_page_length=0):
					if course_name and progress.get("course_name") != course_name:
						frappe.db.set_value("ELMS Course Progress", progress.get("name"), "course_name", course_name, update_modified=False)

	if frappe.db.exists("DocType", "ELMS Lesson Progress") and frappe.db.exists("DocType", "ELMS Course Lesson"):
		lesson_fields = ["name", "lesson_id", "lesson", "lesson_name", "course_progress"]
		if frappe.db.has_column("ELMS Lesson Progress", "user"):
			lesson_fields.append("user")
		if frappe.db.has_column("ELMS Lesson Progress", "course_name"):
			lesson_fields.append("course_name")
		for row in frappe.get_all("ELMS Lesson Progress", fields=lesson_fields, limit_page_length=0):
			lesson_id = row.get("lesson_id")
			if lesson_id and frappe.db.exists("ELMS Course Lesson", lesson_id):
				if not row.get("lesson"):
					frappe.db.set_value("ELMS Lesson Progress", row.get("name"), "lesson", lesson_id, update_modified=False)
				lesson_name = frappe.db.get_value("ELMS Course Lesson", lesson_id, "lesson_name")
				if lesson_name and row.get("lesson_name") != lesson_name:
					frappe.db.set_value("ELMS Lesson Progress", row.get("name"), "lesson_name", lesson_name, update_modified=False)
			course_progress = row.get("course_progress")
			if course_progress and frappe.db.exists("ELMS Course Progress", course_progress):
				cp = frappe.db.get_value(
					"ELMS Course Progress",
					course_progress,
					["user", "course_name"],
					as_dict=True,
				)
				if cp:
					if (
						frappe.db.has_column("ELMS Lesson Progress", "user")
						and cp.get("user")
						and row.get("user") != cp.get("user")
					):
						frappe.db.set_value(
							"ELMS Lesson Progress",
							row.get("name"),
							"user",
							cp.get("user"),
							update_modified=False,
						)
					if (
						frappe.db.has_column("ELMS Lesson Progress", "course_name")
						and cp.get("course_name")
						and row.get("course_name") != cp.get("course_name")
					):
						frappe.db.set_value(
							"ELMS Lesson Progress",
							row.get("name"),
							"course_name",
							cp.get("course_name"),
							update_modified=False,
						)


def ensure_user_link_titles() -> None:
	"""Show User.full_name in LMS Link controls instead of email IDs."""
	if not frappe.db.exists("DocType", "User"):
		return
	if frappe.db.exists(
		"Property Setter",
		{
			"doc_type": "User",
			"doctype_or_field": "DocType",
			"property": "show_title_field_in_link",
		},
	):
		return
	from frappe.custom.doctype.property_setter.property_setter import make_property_setter

	make_property_setter(
		"User",
		None,
		"show_title_field_in_link",
		1,
		"Check",
		for_doctype=True,
	)


def migrate_exact_role_profile_users() -> None:
    """Attach a canonical profile only when it exactly matches existing user roles."""
    if not hasattr(frappe, "get_all"):
        return
    users = frappe.get_all(
        "User",
        filters={"name": ["not in", ["Administrator", "Guest"]]},
        fields=["name", "role_profile_name"],
    )
    for user in users:
        if user.get("role_profile_name"):
            continue
        roles = set(
            frappe.get_all(
                "Has Role",
                filters={"parent": user.get("name"), "parenttype": "User"},
                pluck="role",
            )
        )
        profile_name = next(
            (name for name, profile_roles in ROLE_PROFILES.items() if roles == set(profile_roles)),
            None,
        )
        if not profile_name:
            continue
        user_doc = frappe.get_doc("User", user.get("name"))
        user_doc.role_profile_name = profile_name
        user_doc.flags.ignore_permissions = True
        user_doc.save()


def ensure_user_group_fields() -> None:
    """Add explicit purpose/limitation fields without changing native group semantics."""
    if not frappe.db.exists("DocType", "User Group"):
        frappe.throw("Required DocType 'User Group' not found for ensure_user_group_fields.")
    fields = (
        ("elms_group_purpose", "Назначение группы", "Small Text"),
        ("elms_access_rule", "Ограничение доступа", "Small Text"),
    )
    for fieldname, label, fieldtype in fields:
        if frappe.db.exists("Custom Field", {"dt": "User Group", "fieldname": fieldname}):
            continue
        field = frappe.new_doc("Custom Field")
        field.update(
            {
                "dt": "User Group",
                "fieldname": fieldname,
                "label": label,
                "fieldtype": fieldtype,
                "insert_after": "user_group_members",
            }
        )
        field.flags.ignore_permissions = True
        field.insert()


def ensure_user_groups() -> None:
    """Seed organizational groups; membership never grants roles."""
    ensure_user_group_fields()
    legacy_group = "Elms"
    learner_group = "ELMS Learners"
    if frappe.db.exists("User Group", legacy_group) and not frappe.db.exists("User Group", learner_group):
        frappe.rename_doc("User Group", legacy_group, learner_group, force=True)
    elif frappe.db.exists("User Group", legacy_group) and frappe.db.exists("User Group", learner_group):
        legacy = frappe.get_doc("User Group", legacy_group)
        learner = frappe.get_doc("User Group", learner_group)
        current_members = {row.user for row in learner.user_group_members}
        for row in legacy.user_group_members:
            if row.user not in current_members:
                learner.append("user_group_members", {"user": row.user})
        learner.flags.ignore_mandatory = True
        learner.flags.ignore_permissions = True
        learner.save()
        frappe.delete_doc("User Group", legacy_group, force=True, ignore_permissions=True)
    for group_name, (purpose, limitation) in GROUP_POLICIES.items():
        if frappe.db.exists("User Group", group_name):
            group = frappe.get_doc("User Group", group_name)
            group.update({"elms_group_purpose": purpose, "elms_access_rule": limitation})
            group.flags.ignore_mandatory = True
            group.flags.ignore_permissions = True
            group.save()
            continue
        group = frappe.new_doc("User Group")
        group.name = group_name
        group.update(
            {
                "user_group_name": group_name,
                "elms_group_purpose": purpose,
                "elms_access_rule": limitation,
                "user_group_members": [],
            }
        )
        group.flags.ignore_permissions = True
        group.insert(ignore_mandatory=True)


def ensure_access_model_perms() -> None:
    """Give ELMS Admin the product-level administration surfaces."""
    access_rules = (
        ("User", {"read": 1, "write": 1, "create": 1, "delete": 0}, 0),
        ("User", {"read": 1, "write": 1}, 1),
        ("Role", {"read": 1}, 0),
        ("Role Profile", {"read": 1}, 0),
        ("User Group", {"read": 1, "write": 1, "create": 1, "delete": 1}, 0),
        ("User Group Member", {"read": 1, "write": 1, "create": 1, "delete": 1}, 0),
        ("User Permission", {"read": 1, "write": 1, "create": 1, "delete": 1}, 0),
    )
    for doctype, rights, permlevel in access_rules:
        if not frappe.db.exists("DocType", doctype):
            frappe.throw(f"Required DocType '{doctype}' not found for ensure_access_model_perms.")
        permission = {"role": ELMS_ADMIN_ROLE, "permlevel": permlevel, **rights}
        custom_perm_name = frappe.db.get_value(
            "Custom DocPerm", {"parent": doctype, "role": ELMS_ADMIN_ROLE, "permlevel": permlevel}, "name"
        )
        if custom_perm_name:
            doc = frappe.get_doc("Custom DocPerm", custom_perm_name)
            doc.update(permission)
            doc.flags.ignore_permissions = True
            doc.save()
        else:
            doc = frappe.new_doc("Custom DocPerm")
            doc.update({"parent": doctype, "parenttype": "DocType", "parentfield": "permissions", **permission})
            doc.flags.ignore_permissions = True
            doc.insert()


def ensure_permission_manager_access() -> None:
    """Expose the native page to ELMS Admin; API authorization is bridged in elms.permissions."""
    if not frappe.db.exists("Page", "permission-manager"):
        frappe.throw("Required Page 'permission-manager' not found for ensure_permission_manager_access.")
    page = frappe.get_doc("Page", "permission-manager")
    roles = {row.role for row in page.roles}
    if ELMS_ADMIN_ROLE not in roles:
        page.append("roles", {"role": ELMS_ADMIN_ROLE})
        page.flags.ignore_permissions = True
        page.save()


def ensure_section_perms() -> None:
    """Idempotently ensure required DocPerm entries for ELMS section DocTypes (FR-004, FR-005).

    Synchronizes permissions across ELMS section DocTypes:
    - ELMS Admin: full RWCD on Operations, LMS, Settings sections.
    - ELMS Operations User: RW on Operations section only.
    - ELMS Learner: RW on LMS section only.
    - Guest / Other roles: strictly denied access.
    """
    if not hasattr(frappe, "db") or frappe.db is None:
        frappe.throw("Database connection is not available for ensure_section_perms.")

    if not frappe.db.exists("DocType", "Custom DocPerm"):
        frappe.throw("Required DocType 'Custom DocPerm' not found for ensure_section_perms.")

    for doctype_name, perms in SECTION_DOCPERM_MATRIX.items():
        if not frappe.db.exists("DocType", doctype_name):
            frappe.throw(f"Required DocType '{doctype_name}' not found for ensure_section_perms.")

        for perm in perms:
            role = perm["role"]
            custom_perm_name = frappe.db.get_value(
                "Custom DocPerm",
                {"parent": doctype_name, "role": role, "permlevel": 0},
                "name",
            )
            if custom_perm_name:
                doc = frappe.get_doc("Custom DocPerm", custom_perm_name)
                doc.update(perm)
                doc.flags.ignore_permissions = True
                doc.save()
            else:
                doc = frappe.new_doc("Custom DocPerm")
                doc.parent = doctype_name
                doc.parenttype = "DocType"
                doc.parentfield = "permissions"
                doc.permlevel = 0
                doc.update(perm)
                doc.flags.ignore_permissions = True
                doc.insert()


def ensure_desk_page_read_perm() -> None:
    """Allow ELMS Desk roles to resolve standard JavaScript pages."""
    if not hasattr(frappe, "db") or frappe.db is None:
        frappe.throw("Database connection is not available for ensure_desk_page_read_perm.")

    if not frappe.db.exists("DocType", "Custom DocPerm"):
        frappe.throw("Required DocType 'Custom DocPerm' not found for ensure_desk_page_read_perm.")
    if not frappe.db.exists("DocType", DESK_PAGE_DOCTYPE):
        frappe.throw(f"Required DocType '{DESK_PAGE_DOCTYPE}' not found for ensure_desk_page_read_perm.")

    for role in ELMS_ROLES:
        permission = {
            "role": role,
            "read": 1,
            "write": 0,
            "create": 0,
            "delete": 0,
            "submit": 0,
            "cancel": 0,
            "amend": 0,
        }
        custom_perm_name = frappe.db.get_value(
            "Custom DocPerm",
            {"parent": DESK_PAGE_DOCTYPE, "role": role, "permlevel": 0},
            "name",
        )
        if custom_perm_name:
            doc = frappe.get_doc("Custom DocPerm", custom_perm_name)
            doc.update(permission)
            doc.flags.ignore_permissions = True
            doc.save()
        else:
            doc = frappe.new_doc("Custom DocPerm")
            doc.parent = DESK_PAGE_DOCTYPE
            doc.parenttype = "DocType"
            doc.parentfield = "permissions"
            doc.permlevel = 0
            doc.update(permission)
            doc.flags.ignore_permissions = True
            doc.insert()


def reconcile_keycloak_user(user_doc, keycloak_data: dict[str, Any]) -> None:
    """Idempotent one-way identity lifecycle and role reconciliation: Keycloak -> Frappe.

    Reconciles active status, core profile attributes, and approved group-to-role mappings.
    Does not replace or overwrite existing Frappe DocType permissions.
    Bidirectional role synchronization back to Keycloak is strictly prohibited.
    """
    if not user_doc or not keycloak_data:
        return

    # 1. Lifecycle status sync
    if "enabled" in keycloak_data:
        user_doc.enabled = 1 if keycloak_data["enabled"] else 0

    # 2. Profile attributes update
    if first_name := keycloak_data.get("firstName") or keycloak_data.get("first_name"):
        user_doc.first_name = first_name
    if last_name := keycloak_data.get("lastName") or keycloak_data.get("last_name"):
        user_doc.last_name = last_name

    # 3. Approved group-to-role mapping
    groups = keycloak_data.get("groups") or []
    if isinstance(groups, str):
        groups = [groups]

    roles_to_add: set[str] = set()
    mapped_profile = None
    for group in groups:
        if group in APPROVED_ROLE_MAPPINGS:
            for role_name in APPROVED_ROLE_MAPPINGS[group]:
                if frappe.db.exists("Role", role_name):
                    roles_to_add.add(role_name)

    existing_roles = {r.role for r in getattr(user_doc, "roles", [])}
    user_doc.flags.ignore_permissions = True
    for role in roles_to_add:
        if role not in existing_roles:
            user_doc.add_roles(role)

    # 4. Bitrix User ID reconciliation
    bitrix_uid = keycloak_data.get("bitrix_user_id")
    if not bitrix_uid and isinstance(keycloak_data.get("attributes"), dict):
        attr_vals = keycloak_data["attributes"].get("bitrix_user_id")
        if attr_vals and isinstance(attr_vals, list) and attr_vals[0]:
            bitrix_uid = attr_vals[0]

    if not bitrix_uid and getattr(user_doc, "email", None):
        from elms.sso.mapping import get_mapping_registry
        m = get_mapping_registry().get_mapping(user_doc.email)
        if m and m.bitrix_id:
            bitrix_uid = m.bitrix_id

    if getattr(user_doc, "email", None):
        mapping = get_mapping_registry().get_mapping(str(user_doc.email).strip().lower())
        if mapping and mapping.role_profile:
            profile_aliases = {
                "ELMS Admin": "ELMS Admin Profile",
                "ELMS Standard LMS": "ELMS Learner Profile",
                "ELMS Operations": "ELMS Operations Profile",
            }
            mapped_profile = profile_aliases.get(mapping.role_profile, mapping.role_profile)
            if frappe.db.exists("Role Profile", mapped_profile):
                user_doc.role_profile_name = mapped_profile

    if bitrix_uid:
        if hasattr(user_doc, "custom_bitrix_user_id"):
            user_doc.custom_bitrix_user_id = str(bitrix_uid)
        if hasattr(user_doc, "bitrix_user_id"):
            user_doc.bitrix_user_id = str(bitrix_uid)

    user_doc.save()


def on_login_sync_identity(login_manager=None) -> None:
    """Hook called on user login.

    If user logged in via Keycloak SSO, ensure one-way identity reconciliation is executed.
    """
    if not login_manager or not getattr(login_manager, "user", None):
        return

    user_email = login_manager.user
    if user_email in ("Administrator", "Guest"):
        return

    oauth_user_data = getattr(frappe.local, "oauth_user_data", None)
    if oauth_user_data and isinstance(oauth_user_data, dict):
        if frappe.db.exists("User", user_email):
            user_doc = frappe.get_doc("User", user_email)
            reconcile_keycloak_user(user_doc, oauth_user_data)


def setup_yandex_smtp() -> str:
    """Configure template Email Account for Yandex 360 SMTP (FR-016 boundary).

    Outage and delivery failures must fail closed and never be masked as success.
    """
    account_name = "Yandex SMTP"
    smtp_server = os.getenv("YANDEX_SMTP_SERVER", "smtp.yandex.ru")
    smtp_port = int(os.getenv("YANDEX_SMTP_PORT", "465"))
    smtp_user = os.getenv("YANDEX_SMTP_USER", "")
    smtp_password = os.getenv("YANDEX_SMTP_PASSWORD", "")

    doc = None
    if frappe.db.exists("Email Account", account_name):
        doc = frappe.get_doc("Email Account", account_name)
    else:
        doc = frappe.new_doc("Email Account")
        doc.email_account_name = account_name

    doc.update(
        {
            "email_id": smtp_user or "noreply@elms.local",
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "use_ssl": 1,
            "enable_outgoing": 1,
            "default_outgoing": 1,
            "auth_method": "Basic",
            "password": smtp_password or None,
        }
    )

    doc.flags.ignore_permissions = True
    if doc.is_new():
        doc.insert()
    else:
        doc.save()

    return doc.name


def handle_yandex_smtp_outage(error: Exception) -> None:
    """Explicit failure handling for unavailable Yandex SMTP delivery (FR-016).

    Forbidden to mask or catch-and-suppress SMTP transmission errors.
    """
    error_msg = f"Yandex SMTP service unavailable or delivery failed: {error}"
    frappe.log_error(title="Yandex SMTP Delivery Failure", message=error_msg)
    raise YandexSMTPDeliveryError(error_msg) from error


def after_migrate() -> None:
    """Post-migration hook for ELMS app.

    Idempotently ensures required ELMS roles, section permissions, review visibility field,
    and Social Login Key exist.
    """
    ensure_roles()
    ensure_section_perms()
    ensure_desk_page_read_perm()
    ensure_access_model_perms()
    ensure_role_profiles()
    ensure_course_categories()
    backfill_lms_display_links()
    ensure_user_link_titles()
    migrate_exact_role_profile_users()
    ensure_user_groups()
    ensure_permission_manager_access()
    from elms.sso.review import ensure_review_visibility_field
    ensure_review_visibility_field()
    from elms.sso.roles import ensure_bitrix_user_field
    ensure_bitrix_user_field()
    from elms.desk.workspaces import ensure_workspaces
    ensure_workspaces()
    from elms.sso.ensure import ensure_social_login_keys
    ensure_social_login_keys()


def after_install() -> None:
    """Post-installation hook for ELMS app.

    Sets up Keycloak Social Login Key, Yandex SMTP configuration,
    and ensures required ELMS roles, section permissions, and review visibility field exist.
    """
    ensure_roles()
    ensure_section_perms()
    ensure_desk_page_read_perm()
    ensure_access_model_perms()
    ensure_role_profiles()
    ensure_course_categories()
    backfill_lms_display_links()
    ensure_user_link_titles()
    migrate_exact_role_profile_users()
    ensure_user_groups()
    ensure_permission_manager_access()
    from elms.sso.review import ensure_review_visibility_field
    ensure_review_visibility_field()
    from elms.sso.roles import ensure_bitrix_user_field
    ensure_bitrix_user_field()
    from elms.desk.workspaces import ensure_workspaces
    ensure_workspaces()

    try:
        from elms.sso.ensure import ensure_social_login_keys
        ensure_social_login_keys()
    except Exception as e:
        frappe.log_error(title="ELMS ensure_social_login_keys error", message=str(e))
        raise

    try:
        setup_yandex_smtp()
    except Exception as e:
        frappe.log_error(title="ELMS setup_yandex_smtp error", message=str(e))
        raise

app_name = "elms"
app_title = "elms"
app_publisher = "ELMS Team"
app_description = "Система дистанционного обучения elms"
app_email = "admin@example.com"
app_license = "mit"
app_logo_url = "/assets/elms/images/nftgz-favicon.svg"

add_to_apps_screen = [
	{
		"name": "elms",
		"logo": "/assets/elms/images/nftgz-favicon.svg",
		"title": "elms",
		"route": "/app",
	},
]

web_include_css = [
    "/assets/elms/css/login.css",
    "/assets/elms/css/apply-forms.css?v=1",
]
web_include_js = [
    "/assets/elms/js/login-keycloak.js?v=3",
    "/assets/elms/js/apply-forms.js?v=1",
]
app_include_css = [
	"/assets/elms/css/desk-learning.css?v=6",
	"/assets/elms/css/first-login-password.css?v=1",
	"/assets/elms/css/desk-assistant.css?v=10",
	"/assets/elms/css/course-studio.css?v=11",
	"/assets/elms/css/desk-access.css?v=2",
	"/assets/elms/css/desk-cabinet.css?v=elms-cabinet-20261114-5",
"/assets/elms/css/desk-company-access.css?v=4",
	"/assets/elms/css/desk-company-integrations.css?v=1",
	"/assets/elms/css/desk-applications.css?v=1",
]
app_include_js = [
	"/assets/elms/js/desk-learning.js?v=6",
	"/assets/elms/js/first-login-password.js?v=1",
	"/assets/elms/js/desk-assistant.js?v=10",
	"/assets/elms/js/course-studio.js?v=12",
	"/assets/elms/js/desk-access.js?v=2",
"/assets/elms/js/desk-cabinet.js?v=14",
"/assets/elms/js/desk-company-access.js?v=4",
	"/assets/elms/js/desk-company-integrations.js?v=1",
	"/assets/elms/js/desk-applications.js?v=1",
]

doctype_js = {
    "Role": "public/js/role.js",
    "Role Profile": "public/js/role-profile.js",
    "User Group": "public/js/user-group.js",
}

page_js = {
	"elms-learning": "public/js/elms-learning-page.js",
	"elms-course-preview": "public/js/elms-course-preview-page.js",
	"elms-course-studio": "public/js/elms-course-studio-page.js",
	"elms-access": "public/js/elms-access-page.js",
	"elms-cabinet": "public/js/elms-cabinet-page.js",
	"elms-company-access": "public/js/elms-company-access-page.js",
	"elms-company-integrations": "public/js/elms-company-integrations-page.js",
	"elms-company-integration-llm": "public/js/elms-company-integrations-page.js",
	"elms-company-integration-bitrix24": "public/js/elms-company-integrations-page.js",
	"elms-company-integration-custom-api": "public/js/elms-company-integrations-page.js",
}

extend_bootinfo = [
	"elms.sso.review.extend_bootinfo",
	"elms.ai.boot.extend_bootinfo",
]

override_whitelisted_methods = {
    "frappe.desk.desktop.get_desktop_page": "elms.sso.review.get_desktop_page",
    "frappe.core.page.permission_manager.permission_manager.get_roles_and_doctypes": "elms.permissions.get_roles_and_doctypes",
    "frappe.core.page.permission_manager.permission_manager.get_permissions": "elms.permissions.get_permissions",
    "frappe.core.page.permission_manager.permission_manager.add": "elms.permissions.add",
    "frappe.core.page.permission_manager.permission_manager.update": "elms.permissions.update",
    "frappe.core.page.permission_manager.permission_manager.remove": "elms.permissions.remove",
    "frappe.core.page.permission_manager.permission_manager.reset": "elms.permissions.reset",
    "frappe.core.page.permission_manager.permission_manager.get_users_with_role": "elms.permissions.get_users_with_role",
    "frappe.core.page.permission_manager.permission_manager.get_standard_permissions": "elms.permissions.get_standard_permissions",
}
update_website_context = ["elms.install.update_website_context"]

after_install = "elms.install.after_install"
after_migrate = "elms.install.after_migrate"
on_login = "elms.install.on_login_sync_identity"

doc_events = {
	"User": {
		"after_insert": "elms.sso.roles.maybe_assign_sso_roles",
	}
}

_lms_tenant_doctypes = (
	"ELMS Organization Integration",
	"ELMS Organization Role",
	"ELMS Organization Member",
	"ELMS Course",
	"ELMS Course Category",
	"ELMS Course Chapter",
	"ELMS Course Lesson",
	"ELMS Batch",
	"ELMS Subscription",
	"ELMS Enrollment",
	"ELMS Course Progress",
	"ELMS Lesson Progress",
	"ELMS User Activity",
	"ELMS Video Watch Log",
	"ELMS Program",
	"ELMS Program Course",
	"ELMS Program Enrollment",
	"ELMS Quiz",
	"ELMS Quiz Question",
	"ELMS Quiz Attempt",
)

permission_query_conditions = {
	**{doctype: "elms.tenant.get_permission_query_conditions" for doctype in _lms_tenant_doctypes},
	"User": "elms.tenant.get_permission_query_conditions",
}

has_permission = {
	**{doctype: "elms.tenant.has_tenant_permission" for doctype in _lms_tenant_doctypes},
}

for _doctype in _lms_tenant_doctypes:
	if _doctype not in doc_events:
		doc_events[_doctype] = {}
	doc_events[_doctype]["before_validate"] = "elms.tenant.validate_lms_document"

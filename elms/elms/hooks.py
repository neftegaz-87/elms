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

web_include_css = "/assets/elms/css/login.css"
web_include_js = ["/assets/elms/js/login-keycloak.js?v=3"]
app_include_css = [
	"/assets/elms/css/desk-learning.css?v=6",
	"/assets/elms/css/desk-assistant.css?v=10",
	"/assets/elms/css/course-studio.css?v=11",
]
app_include_js = [
	"/assets/elms/js/desk-learning.js?v=6",
	"/assets/elms/js/desk-assistant.js?v=10",
	"/assets/elms/js/course-studio.js?v=12",
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

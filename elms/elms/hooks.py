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
	{
		"name": "elms-review",
		"logo": "/assets/elms/images/nftgz-favicon.svg",
		"title": "Сверка заявки",
		"route": "/app/review",
		"has_permission": "elms.sso.review.has_review_app_permission",
	}
]

web_include_css = "/assets/elms/css/login.css"
web_include_js = ["/assets/elms/js/login-keycloak.js"]
app_include_css = [
	"/assets/elms/css/desk-review.css?v=3",
	"/assets/elms/css/desk-learning.css?v=1",
]
app_include_js = [
	"/assets/elms/js/desk-review.js?v=3",
	"/assets/elms/js/desk-learning.js?v=1",
]

extend_bootinfo = ["elms.sso.review.extend_bootinfo"]

override_whitelisted_methods = {
	"frappe.desk.desktop.get_desktop_page": "elms.sso.review.get_desktop_page",
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

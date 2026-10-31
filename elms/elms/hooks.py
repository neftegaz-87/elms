app_name = "elms"
app_title = "ELMS СДО"
app_publisher = "ELMS Team"
app_description = "Система дистанционного обучения ELMS"
app_email = "admin@example.com"
app_license = "mit"

add_to_apps_screen = [
	{
		"name": "elms",
		"title": "ELMS СДО",
		"route": "/app",
	}
]

web_include_css = "/assets/elms/css/login.css"
web_include_js = ["/assets/elms/js/login-keycloak.js"]
app_include_css = ["/assets/elms/css/desk-review.css?v=3"]
app_include_js = ["/assets/elms/js/desk-review.js?v=2"]
update_website_context = ["elms.install.update_website_context"]

after_install = "elms.install.after_install"
after_migrate = "elms.install.after_migrate"
on_login = "elms.install.on_login_sync_identity"

doc_events = {
	"User": {
		"after_insert": "elms.sso.roles.maybe_assign_sso_roles",
	}
}

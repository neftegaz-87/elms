app_name = "elms"
app_title = "ELMS"
app_publisher = "ELMS Team"
app_description = "Enterprise Learning Management System"
app_email = "admin@example.com"
app_license = "mit"

web_include_css = "/assets/elms/css/login.css"

after_install = "elms.install.after_install"
after_migrate = "elms.install.after_migrate"
on_login = "elms.install.on_login_sync_identity"

doc_events = {
	"User": {
		"after_insert": "elms.sso.roles.maybe_assign_sso_roles",
	}
}

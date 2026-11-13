(function () {
	"use strict";

	var loginEndpoint = "elms.sso.login.login_with_keycloak";
	var loginTokenEndpoint = "/api/method/frappe.www.login.login_via_token";

	function showInvalidLogin(form) {
		login.set_invalid(__("Invalid Login. Try again."));
		$(form).find(".btn-login").prop("disabled", false).text(__("Login"));
	}

	function hideSocialChrome() {
		$(".for-login .social-logins, .for-login .login-divider, .for-login .btn-keycloak, .for-login .btn-login-with-email-link").hide();
	}

	function bindKeycloakLogin() {
		hideSocialChrome();

		var forms = $(".for-login form.form-login");
		if (!forms.length) {
			forms = $(".for-login .form-login");
		}
		if (!forms.length) return;

		forms.off("submit.elmsKeycloak");
		forms.on("submit.elmsKeycloak", function (event) {
			event.preventDefault();
			event.stopImmediatePropagation();

			var form = this;
			var username = frappe.utils.xss_sanitise(( $(form).find("#login_email").val() || "" ).trim());
			var password = $(form).find("#login_password").val() || "";
			var submit = $(form).find(".btn-login");

			if (!username || !password) {
				login.set_invalid(__("Both login and password required"));
				return false;
			}

			submit.prop("disabled", true);
			login.set_status(__("Verifying..."), "blue");

			frappe.call({
				type: "POST",
				method: loginEndpoint,
				args: { usr: username, pwd: password },
				freeze: true,
				error: function () {
					showInvalidLogin(form);
				}
			}).then(function (response) {
				var loginToken = response && response.message && response.message.login_token;
				if (!loginToken) {
					showInvalidLogin(form);
					return;
				}

				window.location.href = loginTokenEndpoint + "?login_token=" + encodeURIComponent(loginToken);
			}).catch(function () {
				showInvalidLogin(form);
			});

			return false;
		});
	}

	function tryBind() {
		if ($(".for-login .form-login").length) {
			bindKeycloakLogin();
		}
	}

	$(document).on("login_rendered", bindKeycloakLogin);
	$(tryBind);
	$(window).on("load", tryBind);
	setTimeout(tryBind, 0);
	setTimeout(tryBind, 250);
})();

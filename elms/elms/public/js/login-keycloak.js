(function () {
	var loginEndpoint = "elms.sso.login.login_with_keycloak";
	var loginTokenEndpoint = "/api/method/frappe.www.login.login_via_token";

	function showInvalidLogin(form) {
		login.set_invalid(__("Invalid Login. Try again."));
		$(form).find(".btn-login").prop("disabled", false);
	}

	function bindKeycloakLogin() {
		var forms = $(".for-login .form-login");
		if (!forms.length) {
			return;
		}

		forms.off("submit");
		forms.on("submit.elmsKeycloak", function (event) {
			event.preventDefault();
			var form = this;
			var username = frappe.utils.xss_sanitise(( $("#login_email").val() || "" ).trim());
			var password = $("#login_password").val() || "";
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
				},
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

	$(document).on("login_rendered", bindKeycloakLogin);
})();

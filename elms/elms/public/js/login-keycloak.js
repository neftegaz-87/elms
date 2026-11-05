(function () {
	"use strict";

	var authorizationEndpoint = "elms.sso.login.get_sso_authorization_url";

	function isLocalDevHost() {
		var hostname = window.location.hostname || "";
		return hostname === "localhost" || hostname === "127.0.0.1" || hostname.endsWith(".localhost");
	}

	function showLoginError(form) {
		login.set_invalid(__("Не удалось открыть страницу входа."));
		$(form).find(".btn-login").prop("disabled", false);
	}

	function redirectToKeycloak(form, mode) {
		var username = frappe.utils.xss_sanitise(( $("#login_email").val() || "" ).trim());
		var submit = $(form).find(".btn-login");

		if (!username) {
			login.set_invalid(__("Укажите рабочую почту или логин."));
			return;
		}

		submit.prop("disabled", true);
		login.set_status(
			mode === "yandex"
				? __("Переход к Yandex 360 через Keycloak…")
				: __("Переход к тестовому входу Keycloak…"),
			"blue"
		);

		frappe.call({
			type: "GET",
			method: authorizationEndpoint,
			args: { user_input: username, mode: mode, redirect_to: "/app" },
			error: function () {
				showLoginError(form);
			}
		}).then(function (response) {
			var authUrl = response && response.message && response.message.auth_url;
			if (!authUrl) {
				showLoginError(form);
				return;
			}
			window.location.assign(authUrl);
		}).catch(function () {
			showLoginError(form);
		});
	}

	function addLocalTestButton(form) {
		if (!isLocalDevHost()) return;
		var actions = $(form).find(".page-card-actions").first();
		if (!actions.length || actions.find(".elms-local-keycloak-login").length) return;

		var button = $("<button>", {
			type: "button",
			class: "btn btn-sm btn-default btn-block elms-local-keycloak-login",
			text: __("Тестовый вход Keycloak")
		});
		button.on("click", function () {
			redirectToKeycloak(form, "local");
		});
		actions.append(button);
	}

	function prepareForm(form) {
		var password = $(form).find("#login_password");
		password.prop("required", false).closest(".form-group").hide();
		$(form).find(".forgot-password-message").hide();

		var submit = $(form).find(".btn-login");
		submit.text(__("Войти через Yandex 360"));
		if (!$(form).find(".elms-sso-hint").length) {
			$(form).find(".page-card-body").first().prepend(
				$("<p>", {
					class: "elms-sso-hint text-muted",
					text: __("Аутентификация проходит в Yandex 360 через Keycloak. Пароль вводится только на странице провайдера.")
				})
			);
		}
		addLocalTestButton(form);
	}

	function bindKeycloakLogin() {
		var form = $(".for-login form.form-login").first();
		if (!form.length) return;

		prepareForm(form);
		form.off("submit.elmsKeycloak");
		form.on("submit.elmsKeycloak", function (event) {
			event.preventDefault();
			redirectToKeycloak(this, "yandex");
			return false;
		});
	}

	$(document).on("login_rendered", bindKeycloakLogin);
})();

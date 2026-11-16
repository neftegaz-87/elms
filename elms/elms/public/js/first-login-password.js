(function () {
	"use strict";

	var stateMethod = "elms.sso.password.get_password_change_state";
	var changeMethod = "elms.sso.password.change_password";
	var rootId = "elms-first-login-password";

	function errorMessage(error) {
		var message = error && (error.message || error.exception || error._server_messages);
		if (typeof message === "string") {
			try {
				var parsed = JSON.parse(message);
				if (Array.isArray(parsed) && parsed[0]) return String(parsed[0]);
			} catch (ignored) {}
			return message.replace(/<[^>]+>/g, "").trim();
		}
		return "Не удалось выполнить операцию. Повторите попытку.";
	}

	function call(method, args, callback) {
		frappe.call({
			method: method,
			args: args || {},
			callback: function (response) {
				callback(response && response.message, null);
			},
			error: function (error) {
				callback(null, error);
			}
		});
	}

	function removeModal() {
		var modal = document.getElementById(rootId);
		if (modal) modal.remove();
	}

	function renderModal() {
		if (document.getElementById(rootId)) return;

		var modal = document.createElement("div");
		modal.id = rootId;
		modal.className = "elms-first-login-password";
		modal.setAttribute("role", "dialog");
		modal.setAttribute("aria-modal", "true");
		modal.setAttribute("aria-labelledby", rootId + "-title");
		modal.innerHTML = [
			'<div class="elms-first-login-password__card">',
			'<div class="elms-first-login-password__eyebrow">БЕЗОПАСНОСТЬ АККАУНТА</div>',
			'<h1 id="' + rootId + '-title">Измените пароль</h1>',
			'<p class="elms-first-login-password__lead">Для первого входа установите свой пароль. После этого вы попадёте в рабочее пространство ELMS.</p>',
			'<form class="elms-first-login-password__form">',
			'<label>Новый пароль<input name="new_password" type="password" autocomplete="new-password" minlength="8" required></label>',
			'<label>Повторите пароль<input name="confirm_password" type="password" autocomplete="new-password" minlength="8" required></label>',
			'<p class="elms-first-login-password__hint">Минимум 8 символов.</p>',
			'<p class="elms-first-login-password__status" role="alert" aria-live="polite" hidden></p>',
			'<button class="elms-first-login-password__submit" type="submit">Сохранить новый пароль</button>',
			'</form>',
			'</div>'
		].join("");
		document.body.appendChild(modal);

		var form = modal.querySelector("form");
		var status = modal.querySelector("[role=alert]");
		var submit = modal.querySelector("button[type=submit]");
		var newPassword = form.querySelector('[name="new_password"]');
		var confirmPassword = form.querySelector('[name="confirm_password"]');
		form.addEventListener("submit", function (event) {
			event.preventDefault();
			status.hidden = true;
			submit.disabled = true;
			submit.setAttribute("aria-busy", "true");
			call(changeMethod, {
				new_password: newPassword.value,
				confirm_password: confirmPassword.value
			}, function (result, error) {
				submit.disabled = false;
				submit.removeAttribute("aria-busy");
				if (error || !result || !result.changed) {
					status.textContent = errorMessage(error);
					status.hidden = false;
					return;
				}
				removeModal();
			});
		});
		newPassword.focus();
	}

	function checkState() {
		if (!window.frappe || !frappe.call || !frappe.session || frappe.session.user === "Guest") return;
		call(stateMethod, {}, function (result, error) {
			if (error) {
				if (window.frappe && frappe.show_alert) frappe.show_alert({message: errorMessage(error), indicator: "red"});
				return;
			}
			if (result && result.required) renderModal();
		});
	}

	function start() {
		if (!window.frappe || !frappe.call || !frappe.session) {
			setTimeout(start, 250);
			return;
		}
		checkState();
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", start);
	} else {
		start();
	}
})();

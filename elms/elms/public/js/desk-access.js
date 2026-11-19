(function () {
	"use strict";

	var accessPageName = "elms-access";
	var accessPageLabel = "Доступ компаний";
	var retryDelays = [0, 250, 1000];

	function esc(value) {
		return String(value === null || value === undefined ? "" : value)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/\"/g, "&quot;")
			.replace(/'/g, "&#039;");
	}

	function call(method, args, callback) {
		if (!window.frappe || !frappe.call) return;
		frappe.call({
			method: method,
			args: args || {},
			callback: function (response) {
				if (response && response.message) callback(response.message, null);
				else callback(null, response || { message: "Пустой ответ сервера" });
			},
			error: function (error) {
				callback(null, error || { message: "Не удалось выполнить запрос" });
			}
		});
	}

	function errorMessage(error) {
		var message = error && (error.message || error.exception || error._server_messages);
		if (typeof message === "string") {
			try {
				var parsed = JSON.parse(message);
				if (Array.isArray(parsed) && parsed[0]) return String(parsed[0]);
			} catch (ignored) {}
			return message.replace(/<[^>]+>/g, "").trim();
		}
		return "Не удалось выполнить операцию. Проверьте права и повторите попытку.";
	}

	function roles() {
		var values = window.frappe && (frappe.user_roles || (frappe.boot && frappe.boot.user && frappe.boot.user.roles));
		return Array.isArray(values) ? values : [];
	}

	function hasRole(role) {
		return roles().indexOf(role) >= 0;
	}

	function isPlatformViewer() {
		return hasRole("ELMS Admin") || hasRole("ELMS Operations User") || hasRole("Administrator") || hasRole("System Manager");
	}

	function field(form, name) {
		var control = form.querySelector('[name="' + name + '"]');
		return control ? String(control.value || "").trim() : "";
	}

	function setStatus(root, message, kind) {
		var status = root.querySelector("[data-access-status]");
		if (!status) return;
		status.className = "elms-access-status" + (kind ? " " + kind : "");
		status.textContent = message || "";
		status.hidden = !message;
	}

	function setBusy(form, busy) {
		var button = form.querySelector("button[type=submit]");
		if (!button) return;
		button.disabled = busy;
		button.setAttribute("aria-busy", busy ? "true" : "false");
	}

	function activateTab(root, tabName, moveFocus) {
		var tabs = root.querySelectorAll("[data-access-tab]");
		var panels = root.querySelectorAll("[data-access-panel]");
		Array.prototype.forEach.call(tabs, function (tab) {
			var active = tab.getAttribute("data-access-tab") === tabName;
			tab.classList.toggle("is-active", active);
			tab.setAttribute("aria-selected", active ? "true" : "false");
			tab.tabIndex = active ? 0 : -1;
			if (active && moveFocus) tab.focus();
		});
		Array.prototype.forEach.call(panels, function (panel) {
			panel.hidden = panel.getAttribute("data-access-panel") !== tabName;
		});
	}

	function moveTab(root, tab, direction) {
		var tabs = Array.prototype.slice.call(root.querySelectorAll("[data-access-tab]:not([hidden])"));
		var index = tabs.indexOf(tab);
		if (index < 0 || !tabs.length) return;
		var nextIndex = (index + direction + tabs.length) % tabs.length;
		activateTab(root, tabs[nextIndex].getAttribute("data-access-tab"), true);
	}

	function bindTabs(root) {
		var tablist = root.querySelector("[data-access-tablist]");
		if (!tablist) return;
		tablist.addEventListener("click", function (event) {
			var tab = event.target.closest("[data-access-tab]");
			if (!tab || tab.hidden) return;
			activateTab(root, tab.getAttribute("data-access-tab"), false);
		});
		tablist.addEventListener("keydown", function (event) {
			var tab = event.target.closest("[data-access-tab]");
			if (!tab) return;
			if (event.key === "ArrowRight") {
				event.preventDefault();
				moveTab(root, tab, 1);
			} else if (event.key === "ArrowLeft") {
				event.preventDefault();
				moveTab(root, tab, -1);
			} else if (event.key === "Home") {
				event.preventDefault();
				var first = root.querySelector("[data-access-tab]:not([hidden])");
				if (first) activateTab(root, first.getAttribute("data-access-tab"), true);
			} else if (event.key === "End") {
				event.preventDefault();
				var visible = root.querySelectorAll("[data-access-tab]:not([hidden])");
				if (visible.length) activateTab(root, visible[visible.length - 1].getAttribute("data-access-tab"), true);
			}
		});
	}

	function organizationOptions(organizations, selected) {
		var placeholder = '<option value="">Выберите организацию</option>';
		if (!organizations || !organizations.length) {
			return placeholder + '<option value="" disabled>Нет доступных организаций</option>';
		}
		return placeholder + organizations.map(function (name) {
			return '<option value="' + esc(name) + '"' + (name === selected ? " selected" : "") + ">" + esc(name) + "</option>";
		}).join("");
	}

	function fillOrganizationSelects(root, organizations, preferred) {
		var selects = root.querySelectorAll("[data-access-org-select]");
		Array.prototype.forEach.call(selects, function (select) {
			var current = preferred || select.value || "";
			if (current && organizations.indexOf(current) < 0) current = "";
			select.innerHTML = organizationOptions(organizations, current);
			if (!select.value && organizations.length === 1) select.value = organizations[0];
		});
	}

	function loadOrganizations(root, preferred, done) {
		call("elms.access.api.get_company_access_context", {}, function (context, error) {
			if (error || !context) {
				if (done) done(null, error);
				else setStatus(root, errorMessage(error), "error");
				return;
			}
			var organizations = context.organizations || [];
			root._elmsAccessOrganizations = organizations;
			fillOrganizationSelects(root, organizations, preferred || context.organization || "");
			if (done) done(organizations, null);
		});
	}

	function submitForm(root, form, method, args, successMessage, afterSuccess) {
		setBusy(form, true);
		setStatus(root, "Выполняем операцию…", "pending");
		call(method, args, function (result, error) {
			setBusy(form, false);
			if (error || !result) {
				setStatus(root, errorMessage(error), "error");
				return;
			}
			setStatus(root, successMessage(result), "success");
			form.reset();
			if (root._elmsAccessOrganizations) {
				fillOrganizationSelects(root, root._elmsAccessOrganizations, "");
			}
			if (afterSuccess) afterSuccess(result);
		});
	}

	function render(root) {
		var admin = hasRole("ELMS Admin") || hasRole("Administrator") || hasRole("System Manager");
		var companyAdmin = hasRole("ELMS Company Admin");
		var platformViewer = isPlatformViewer();
		var companyAdminOption = companyAdmin ? '<option value="ELMS Company Admin Profile">ELMS Company Admin Profile — администратор компании</option>' : '';
		var defaultTab = admin ? "organization" : ((admin || companyAdmin) ? "invite" : "");

		root.innerHTML = [
			'<div class="elms-access-shell">',
			'<header class="elms-access-header"><div><div class="elms-access-kicker">OPERATIONS · B2B</div><h1>Доступ компаний</h1><p>' + (platformViewer && !companyAdmin ? "режим просмотра: выбранная организация не меняет сессию и не открывает приглашения." : "Организация задаёт границу доступа. Приглашение создаёт пользователя в ELMS и запускает настройку пароля Keycloak.") + '</p></div><span class="elms-access-mark">elms</span></header>',
			'<div class="elms-access-status" data-access-status role="status" aria-live="polite" hidden></div>',
			'<div class="elms-access-tabs" role="tablist" aria-label="Действия доступа" data-access-tablist>',
			'<button type="button" class="elms-access-tab' + (defaultTab === "organization" ? " is-active" : "") + '" role="tab" id="elms-access-tab-organization" data-access-tab="organization" data-access-admin-tab aria-controls="elms-access-panel-organization" aria-selected="' + (defaultTab === "organization" ? "true" : "false") + '" tabindex="' + (defaultTab === "organization" ? "0" : "-1") + '">Создать организацию</button>',
			'<button type="button" class="elms-access-tab' + (defaultTab === "company-admin" ? " is-active" : "") + '" role="tab" id="elms-access-tab-company-admin" data-access-tab="company-admin" data-access-admin-tab aria-controls="elms-access-panel-company-admin" aria-selected="' + (defaultTab === "company-admin" ? "true" : "false") + '" tabindex="' + (defaultTab === "company-admin" ? "0" : "-1") + '">Назначить Company Admin</button>',
			'<button type="button" class="elms-access-tab' + (defaultTab === "invite" ? " is-active" : "") + '" role="tab" id="elms-access-tab-invite" data-access-tab="invite" data-access-invite-tab aria-controls="elms-access-panel-invite" aria-selected="' + (defaultTab === "invite" ? "true" : "false") + '" tabindex="' + (defaultTab === "invite" ? "0" : "-1") + '">Пригласить сотрудника</button>',
			"</div>",
			'<div class="elms-access-panels">',
			'<section class="elms-access-card elms-access-panel" role="tabpanel" id="elms-access-panel-organization" data-access-panel="organization" aria-labelledby="elms-access-tab-organization"' + (defaultTab === "organization" ? "" : " hidden") + ' data-access-admin><div class="elms-access-card-head"><span class="elms-access-index">01</span><div><h2>Создать организацию</h2><p>Доступно администратору ELMS.</p></div></div><form data-access-form="organization"><label>Название<input name="name" required maxlength="140" autocomplete="organization"></label><label>ИНН<input name="inn" required maxlength="12" inputmode="numeric"></label><div class="elms-access-row"><label>ОГРН<input name="ogrn" maxlength="15" inputmode="numeric"></label><label>КПП<input name="kpp" maxlength="9" inputmode="numeric"></label></div><button class="elms-access-primary" type="submit">Создать организацию</button></form></section>',
			'<section class="elms-access-card elms-access-panel" role="tabpanel" id="elms-access-panel-company-admin" data-access-panel="company-admin" aria-labelledby="elms-access-tab-company-admin"' + (defaultTab === "company-admin" ? "" : " hidden") + ' data-access-admin><div class="elms-access-card-head"><span class="elms-access-index">02</span><div><h2>Назначить Company Admin</h2><p>Свяжите пользователя с организацией и её User Permission.</p></div></div><form data-access-form="company-admin"><label>Email пользователя<input name="user" required type="email" autocomplete="email"></label><label>Организация<select name="organization" required data-access-org-select="company-admin"><option value="">Загружаем организации…</option></select></label><button class="elms-access-primary" type="submit">Назначить роль</button></form></section>',
			'<section class="elms-access-card elms-access-panel" role="tabpanel" id="elms-access-panel-invite" data-access-panel="invite" aria-labelledby="elms-access-tab-invite"' + (defaultTab === "invite" ? "" : " hidden") + ' data-access-invite><div class="elms-access-card-head"><span class="elms-access-index">03</span><div><h2>Пригласить сотрудника</h2><p>Письмо с одноразовой настройкой пароля отправляется Keycloak после успешного создания доступа.</p></div></div><form data-access-form="invite"><div class="elms-access-row"><label>Имя<input name="first_name" required maxlength="120" autocomplete="given-name"></label><label>Фамилия<input name="last_name" required maxlength="120" autocomplete="family-name"></label></div><div class="elms-access-row"><label>Email<input name="email" required type="email" maxlength="180" autocomplete="email"></label><label>Организация<select name="organization" required data-access-org-select="invite"><option value="">Загружаем организации…</option></select></label></div><label>Профиль доступа<select name="role_profile"><option value="ELMS Learner Profile">ELMS Learner Profile — слушатель</option>' + companyAdminOption + '</select></label><button class="elms-access-primary" type="submit">Отправить приглашение</button></form></section>',
			"</div>",
			'<div class="elms-access-note"><strong>Граница безопасности</strong><span>Поля на этой странице только передают запрос. Роль, организация и User Permission проверяются сервером Frappe.</span></div>',
			"</div>"
		].join("");

		root.querySelectorAll("[data-access-admin-tab]").forEach(function (tab) {
			if (!admin) tab.remove();
		});
		root.querySelectorAll("[data-access-admin]").forEach(function (panel) {
			if (!admin) panel.remove();
		});
		var inviteTab = root.querySelector("[data-access-invite-tab]");
		var invitePanel = root.querySelector("[data-access-invite]");
		if (!companyAdmin) {
			if (inviteTab) inviteTab.remove();
			if (invitePanel) invitePanel.remove();
		}
		if (!admin && !companyAdmin) {
			setStatus(root, platformViewer ? "Режим просмотра: действия доступа доступны только Company Admin своей организации." : "Нет роли для управления организациями. Обратитесь к администратору ELMS.", platformViewer ? "pending" : "error");
			return;
		}

		bindTabs(root);
		if (defaultTab) activateTab(root, defaultTab, false);
		loadOrganizations(root);

		var organizationForm = root.querySelector('[data-access-form="organization"]');
		if (organizationForm) organizationForm.addEventListener("submit", function (event) {
			event.preventDefault();
			submitForm(root, organizationForm, "elms.access.api.create_organization", {
				name: field(organizationForm, "name"),
				inn: field(organizationForm, "inn"),
				ogrn: field(organizationForm, "ogrn"),
				kpp: field(organizationForm, "kpp")
			}, function (result) {
				return "Организация создана: " + (result.organization || "готово");
			}, function (result) {
				var created = result && result.organization ? String(result.organization) : "";
				loadOrganizations(root, created, function () {
					if (created && root.querySelector('[data-access-tab="invite"]')) {
						activateTab(root, "invite", false);
					}
				});
			});
		});

		var companyAdminForm = root.querySelector('[data-access-form="company-admin"]');
		if (companyAdminForm) companyAdminForm.addEventListener("submit", function (event) {
			event.preventDefault();
			submitForm(root, companyAdminForm, "elms.access.api.assign_company_admin", {
				user: field(companyAdminForm, "user"),
				organization: field(companyAdminForm, "organization")
			}, function () {
				return "Company Admin назначен, граница организации сохранена.";
			}, function () {
				loadOrganizations(root);
			});
		});

		var inviteForm = root.querySelector('[data-access-form="invite"]');
		if (inviteForm) inviteForm.addEventListener("submit", function (event) {
			event.preventDefault();
			submitForm(root, inviteForm, "elms.access.api.invite_org_user", {
				email: field(inviteForm, "email"),
				first_name: field(inviteForm, "first_name"),
				last_name: field(inviteForm, "last_name"),
				organization: field(inviteForm, "organization"),
				role_profile: field(inviteForm, "role_profile")
			}, function () {
				return "Приглашение отправлено. Пользователь задаст пароль в Keycloak и войдёт через ELMS.";
			});
		});
	}

	function renderPage(wrapper) {
		var page = frappe.ui.make_app_page({ parent: wrapper, title: accessPageLabel, single_column: true });
		$(wrapper).addClass("elms-access-page-wrapper");
		render(page.main[0]);
	}

	function registerPage() {
		if (!window.frappe || !frappe.container || !frappe.ui) return;
		frappe.provide("frappe.standard_pages");
		if (frappe.standard_pages[accessPageName]) return;
		frappe.standard_pages[accessPageName] = function () {
			var wrapper = frappe.container.add_page(accessPageName);
			renderPage(wrapper);
		};
	}

	window.elmsAccessPage = renderPage;

	retryDelays.forEach(function (delay) { setTimeout(registerPage, delay); });
	$(document).on("toolbar_setup", registerPage);
})();

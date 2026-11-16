(function () {
	"use strict";

	var profileLabels = {
		"ELMS Learner Profile": "Слушатель",
		"ELMS Instructor Profile": "Преподаватель / куратор",
		"ELMS Methodologist Profile": "Методист",
		"ELMS Company Admin Profile": "Администратор компании",
		"ELMS Operations Profile": "Оператор платформы",
		"ELMS Admin Profile": "Администратор ELMS"
	};
	var companyAccessStyleUrl = "/assets/elms/css/desk-company-access.css?v=4";

	function ensureCompanyAccessStyles() {
		var styleLink = document.querySelector('[data-elms-company-access-style="true"]');
		if (styleLink) return;
		styleLink = document.querySelector('link[href*="/assets/elms/css/desk-company-access.css"]');
		if (styleLink && styleLink.getAttribute("href").indexOf("?v=4") !== -1) {
			styleLink.setAttribute("data-elms-company-access-style", "true");
			return;
		}
		styleLink = document.createElement("link");
		styleLink.rel = "stylesheet";
		styleLink.href = companyAccessStyleUrl;
		styleLink.setAttribute("data-elms-company-access-style", "true");
		document.head.appendChild(styleLink);
	}

	function esc(value) {
		return String(value === null || value === undefined ? "" : value)
			.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
			.replace(/\"/g, "&quot;").replace(/'/g, "&#039;");
	}

	function call(method, args, callback) {
		frappe.call({
			method: method,
			args: args || {},
			callback: function (response) { callback(response && response.message, null); },
			error: function (error) { callback(null, error || { message: "Не удалось выполнить запрос" }); }
		});
	}

	function errorMessage(error) {
		var message = error && (error.message || error.exception || error._server_messages);
		if (typeof message === "string") return message.replace(/<[^>]+>/g, "").trim();
		return "Не удалось выполнить операцию. Проверьте права и повторите попытку.";
	}

	function setStatus(root, message, isError) {
		var node = root.querySelector("[data-company-access-status]");
		if (!node) return;
		node.textContent = message || "";
		node.hidden = !message;
		node.className = "elms-company-access-status" + (isError ? " error" : "");
	}

	function profileOptions(profiles, selected) {
		return (profiles || []).map(function (profile) {
			return '<option value="' + esc(profile) + '"' + (profile === selected ? " selected" : "") + ">" +
				esc(profileLabels[profile] || profile) + "</option>";
		}).join("");
	}

	function roleOptions(roles, selected) {
		return '<option value="">Без внутренней роли</option>' + (roles || []).filter(function (role) { return role.enabled; }).map(function (role) {
			return '<option value="' + esc(role.name) + '"' + (role.name === selected ? " selected" : "") + '>' + esc(role.role_name) + '</option>';
		}).join("");
	}

	function capabilityOptions(capabilities, selected) {
		selected = selected || [];
		return (capabilities || []).map(function (capability) {
			return '<label class="elms-company-access-capability"><input type="checkbox" name="capabilities" value="' + esc(capability.value) + '"' + (selected.indexOf(capability.value) >= 0 ? " checked" : "") + '> ' + esc(capability.label) + '</label>';
		}).join("");
	}

	function activateTab(root, tabName, moveFocus) {
		var tabs = root.querySelectorAll("[data-company-access-tab]");
		var panels = root.querySelectorAll("[data-company-access-panel]");
		Array.prototype.forEach.call(tabs, function (tab) {
			var active = tab.getAttribute("data-company-access-tab") === tabName;
			tab.classList.toggle("is-active", active);
			tab.setAttribute("aria-selected", active ? "true" : "false");
			tab.tabIndex = active ? 0 : -1;
			if (active && moveFocus) tab.focus();
		});
		Array.prototype.forEach.call(panels, function (panel) {
			panel.hidden = panel.getAttribute("data-company-access-panel") !== tabName;
		});
	}

	function moveTab(root, tab, direction) {
		var tabs = Array.prototype.slice.call(root.querySelectorAll("[data-company-access-tab]"));
		var index = tabs.indexOf(tab);
		var nextIndex = (index + direction + tabs.length) % tabs.length;
		activateTab(root, tabs[nextIndex].getAttribute("data-company-access-tab"), true);
	}

	function renderRoles(root) {
		var context = root._elmsCompanyAccessContext || {};
		var body = root.querySelector("[data-company-roles-body]");
		if (!body) return;
		var roles = context.company_roles || [];
		body.innerHTML = roles.length ? roles.map(function (role) {
			return '<tr><td><strong>' + esc(role.role_name) + '</strong><small>' + esc(role.description || "Без описания") + '</small></td><td>' + esc(role.capabilities.map(function (key) { var item = (context.capabilities || []).find(function (entry) { return entry.value === key; }); return item ? item.label : key; }).join(", ")) + '</td><td><div class="elms-company-access-actions"><button type="button" class="elms-company-access-button" data-company-role-edit="' + esc(role.name) + '">Изменить</button><button type="button" class="elms-company-access-button is-danger" data-company-role-delete="' + esc(role.name) + '">Удалить</button></div></td></tr>';
		}).join("") : '<tr><td colspan="3" class="elms-company-access-empty">Внутренних ролей пока нет.</td></tr>';
	}

	function resetRoleForm(root) {
		var form = root.querySelector("[data-company-role-form]");
		if (!form) return;
		form.reset();
		form.querySelector("[name='name']").value = "";
		form.querySelector("[data-company-role-submit]").textContent = "Создать роль";
	}

	function submitRole(root, form) {
		var values = { name: form.querySelector("[name='name']").value, organization: selectedOrganization(root), role_name: form.querySelector("[name='role_name']").value, description: form.querySelector("[name='description']").value, capabilities: Array.prototype.map.call(form.querySelectorAll("[name='capabilities']:checked"), function (field) { return field.value; }) };
		if (!values.organization || !values.role_name || !values.capabilities.length) { setStatus(root, "Укажите название и хотя бы одну возможность роли.", true); return; }
		var method = values.name ? "elms.access.api.update_organization_role" : "elms.access.api.create_organization_role";
		call(method, values, function (result, error) {
			if (error || !result) { setStatus(root, errorMessage(error), true); return; }
			setStatus(root, values.name ? "Роль обновлена." : "Роль создана.", false);
			loadMembers(root);
			loadRoles(root);
		});
	}

	function loadRoles(root) {
		var organization = selectedOrganization(root);
		if (!organization) return;
		call("elms.access.api.get_company_access_context", { organization: organization }, function (context, error) {
			if (error || !context) { setStatus(root, errorMessage(error), true); return; }
			root._elmsCompanyAccessContext = context;
			renderRoles(root);
			var roleSelect = root.querySelector("[data-company-role-invite]");
			if (roleSelect) roleSelect.innerHTML = roleOptions(context.company_roles, roleSelect.value);
			loadMembers(root);
		});
	}

	function selectedOrganization(root) {
		var select = root.querySelector("[data-company-access-organization]");
		return select ? select.value : (root.getAttribute("data-organization") || "");
	}

	function loadMembers(root) {
		var organization = selectedOrganization(root);
		if (!organization) {
			renderMembers(root, [], []);
			return;
		}
		setStatus(root, "Загружаем сотрудников…", false);
		call("elms.access.api.get_organization_members", { organization: organization }, function (result, error) {
			if (error || !result) {
				setStatus(root, errorMessage(error), true);
				return;
			}
			renderMembers(root, result.members || [], root._elmsCompanyAccessProfiles || []);
			setStatus(root, "Список обновлён.", false);
		});
	}

	function renderMembers(root, members, profiles) {
		var body = root.querySelector("[data-company-access-body]");
		var empty = root.querySelector("[data-company-access-empty]");
		if (!body || !empty) return;
		if (!members.length) {
			body.innerHTML = "";
			empty.hidden = false;
			return;
		}
		empty.hidden = true;
		body.innerHTML = members.map(function (member) {
			var name = member.full_name || member.user;
			return "<tr>" +
				'<td class="elms-company-access-person"><strong>' + esc(name) + "</strong><small>" + esc(member.email || member.user) + "</small></td>" +
				"<td>" + esc(member.enabled ? "Активна" : "Отключена") + "</td>" +
				'<td><select data-member-profile="' + esc(member.user) + '">' + profileOptions(profiles, member.role_profile) + '</select><select data-member-role="' + esc(member.user) + '">' + roleOptions((root._elmsCompanyAccessContext || {}).company_roles, member.organization_role) + "</select></td>" +
				'<td><div class="elms-company-access-actions"><button type="button" class="elms-company-access-button" data-member-save="' + esc(member.user) + '">Сохранить</button>' +
				(member.enabled ? '<button type="button" class="elms-company-access-button is-danger" data-member-disable="' + esc(member.user) + '">Отключить</button>' : "") + "</div></td>" +
				"</tr>";
		}).join("");
	}

	function submitInvite(root, form) {
		var values = {};
		Array.prototype.forEach.call(form.elements, function (field) { if (field.name) values[field.name] = field.value; });
		values.organization = selectedOrganization(root);
		if (!values.organization) { setStatus(root, "Сначала выберите организацию.", true); return; }
		var button = form.querySelector("button[type=submit]");
		if (button) button.disabled = true;
		call("elms.access.api.invite_org_user", values, function (result, error) {
			if (button) button.disabled = false;
			if (error || !result) { setStatus(root, errorMessage(error), true); return; }
			form.reset();
			setStatus(root, "Приглашение отправлено. Пользователь добавлен в организацию.", false);
			loadMembers(root);
		});
	}

	function bind(root) {
		var form = root.querySelector("[data-company-access-invite]");
		if (form) form.addEventListener("submit", function (event) { event.preventDefault(); submitInvite(root, form); });
		var roleForm = root.querySelector("[data-company-role-form]");
		if (roleForm) roleForm.addEventListener("submit", function (event) { event.preventDefault(); submitRole(root, roleForm); });
		var organization = root.querySelector("[data-company-access-organization]");
		if (organization) organization.addEventListener("change", function () { loadRoles(root); loadMembers(root); });
		Array.prototype.forEach.call(root.querySelectorAll("[data-company-access-tab]"), function (tab) {
			tab.addEventListener("click", function () {
				activateTab(root, tab.getAttribute("data-company-access-tab"), false);
			});
			tab.addEventListener("keydown", function (event) {
				if (event.key === "ArrowRight" || event.key === "ArrowDown") {
					event.preventDefault();
					moveTab(root, tab, 1);
				} else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
					event.preventDefault();
					moveTab(root, tab, -1);
				} else if (event.key === "Home" || event.key === "End") {
					event.preventDefault();
					var tabs = root.querySelectorAll("[data-company-access-tab]");
					var target = event.key === "Home" ? tabs[0] : tabs[tabs.length - 1];
					activateTab(root, target.getAttribute("data-company-access-tab"), true);
				}
			});
		});
		root.addEventListener("click", function (event) {
			var roleEdit = event.target.closest("[data-company-role-edit]");
			var roleDelete = event.target.closest("[data-company-role-delete]");
			if (roleEdit || roleDelete) {
				var roleName = (roleEdit || roleDelete).getAttribute(roleEdit ? "data-company-role-edit" : "data-company-role-delete");
				var role = (root._elmsCompanyAccessContext.company_roles || []).find(function (item) { return item.name === roleName; });
				if (roleDelete) {
					if (!window.confirm("Удалить внутреннюю роль «" + (role ? role.role_name : roleName) + "»?")) return;
					call("elms.access.api.delete_organization_role", { name: roleName, organization: selectedOrganization(root) }, function (result, error) {
						if (error || !result) { setStatus(root, errorMessage(error), true); return; }
						loadRoles(root);
						loadMembers(root);
					});
					return;
				}
				var roleForm = root.querySelector("[data-company-role-form]");
				if (role && roleForm) {
					roleForm.querySelector("[name='name']").value = role.name;
					roleForm.querySelector("[name='role_name']").value = role.role_name;
					roleForm.querySelector("[name='description']").value = role.description || "";
					Array.prototype.forEach.call(roleForm.querySelectorAll("[name='capabilities']"), function (field) { field.checked = role.capabilities.indexOf(field.value) >= 0; });
					roleForm.querySelector("[data-company-role-submit]").textContent = "Сохранить роль";
				}
				return;
			}
			if (event.target.closest("[data-company-role-reset]")) { resetRoleForm(root); return; }
			var save = event.target.closest("[data-member-save]");
			var disable = event.target.closest("[data-member-disable]");
			var user = (save || disable) && (save || disable).getAttribute(save ? "data-member-save" : "data-member-disable");
			if (!user) return;
			var organizationName = selectedOrganization(root);
			if (disable && !window.confirm("Отключить учётную запись " + user + "?")) return;
			var args = { user: user, organization: organizationName };
			var method = disable ? "elms.access.api.disable_organization_member" : "elms.access.api.update_organization_member";
			if (!disable) {
					var row = (save || disable).closest("tr");
					var select = row && row.querySelector("[data-member-profile]");
					args.role_profile = select ? select.value : "";
					var role = row && row.querySelector("[data-member-role]");
					args.organization_role = role ? role.value : "";
			}
			call(method, args, function (result, error) {
				if (error || !result) { setStatus(root, errorMessage(error), true); return; }
				setStatus(root, disable ? "Учётная запись отключена." : "Профиль доступа обновлён.", false);
				loadMembers(root);
			});
		});
	}

	function render(root, context) {
		root._elmsCompanyAccessContext = context;
		root._elmsCompanyAccessProfiles = context.profiles || [];
		root.setAttribute("data-organization", context.organization || "");
		var organizations = context.organizations || [];
		var selector = context.platform_admin ? '<label>Организация<select data-company-access-organization>' + organizations.map(function (value) {
			return '<option value="' + esc(value) + '"' + (value === context.organization ? " selected" : "") + ">" + esc(value) + "</option>";
		}).join("") + "</select></label>" : '<div><div class="elms-company-access-kicker">Организация</div><strong>' + esc(context.organization) + "</strong></div>";
		root.innerHTML = [
			'<div class="elms-company-access-shell">',
			'<header class="elms-company-access-header"><div><div class="elms-company-access-kicker">Внутренний контур компании</div><h1>Роли и доступы сотрудников</h1><p>Назначайте только роли внутри своей организации. Глобальные настройки, компании и матрица DocPerm остаются доступными только ELMS Admin.</p></div><span class="elms-company-access-mark">elms</span></header>',
			'<div class="elms-company-access-toolbar">' + selector + '<button type="button" class="elms-company-access-button" data-company-access-refresh>Обновить список</button></div>',
			'<div class="elms-company-access-status" data-company-access-status role="status" aria-live="polite" hidden></div>',
			'<div class="elms-company-access-tabs" role="tablist" aria-label="Разделы управления доступом">',
			'<button type="button" class="elms-company-access-tab is-active" id="company-access-tab-invite" role="tab" aria-selected="true" aria-controls="company-access-panel-invite" data-company-access-tab="invite">Пригласить сотрудника</button>',
			'<button type="button" class="elms-company-access-tab" id="company-access-tab-members" role="tab" aria-selected="false" aria-controls="company-access-panel-members" data-company-access-tab="members" tabindex="-1">Сотрудники и роли</button>',
			'<button type="button" class="elms-company-access-tab" id="company-access-tab-roles" role="tab" aria-selected="false" aria-controls="company-access-panel-roles" data-company-access-tab="roles" tabindex="-1">Внутренние роли компании</button>',
			'</div>',
			'<section class="elms-company-access-card elms-company-access-panel" id="company-access-panel-invite" role="tabpanel" aria-labelledby="company-access-tab-invite" data-company-access-panel="invite"><h2>Пригласить сотрудника</h2><p>Сотрудник получит базовый профиль и, при необходимости, внутреннюю роль компании.</p><form class="elms-company-access-form" data-company-access-invite><div class="elms-company-access-form-row"><label>Имя<input name="first_name" required maxlength="120"></label><label>Фамилия<input name="last_name" required maxlength="120"></label></div><label>Email<input name="email" type="email" required maxlength="180"></label><label>Базовый профиль<select name="role_profile">' + profileOptions(context.profiles, context.profiles[0]) + '</select></label><label>Внутренняя роль<select name="organization_role" data-company-role-invite>' + roleOptions(context.company_roles, "") + '</select></label><button type="submit" class="elms-company-access-button is-primary">Отправить приглашение</button></form></section>',
			'<section class="elms-company-access-card elms-company-access-panel" id="company-access-panel-members" role="tabpanel" aria-labelledby="company-access-tab-members" data-company-access-panel="members" hidden><h2>Сотрудники и роли</h2><p>Базовый профиль даёт безопасный продуктовый контур, а внутренняя роль компании добавляет выбранные возможности.</p><div class="elms-company-access-empty" data-company-access-empty hidden>В организации пока нет сотрудников.</div><div class="elms-company-access-table-wrap"><table class="elms-company-access-table"><thead><tr><th>Сотрудник</th><th>Учётка</th><th>Профиль и внутренняя роль</th><th></th></tr></thead><tbody data-company-access-body></tbody></table></div></section>',
			'<section class="elms-company-access-card elms-company-access-panel" id="company-access-panel-roles" role="tabpanel" aria-labelledby="company-access-tab-roles" data-company-access-panel="roles" hidden><h2>Внутренние роли компании</h2><p>Создавайте свои названия ролей и назначайте им функциональность учебного контура. Это не глобальные Frappe Role и не доступ к B2B/Settings.</p><form class="elms-company-access-form" data-company-role-form><input type="hidden" name="name"><div class="elms-company-access-form-row"><label>Название роли<input name="role_name" required maxlength="120" placeholder="Например, Куратор нефтегазовых курсов"></label><label>Описание<input name="description" maxlength="500" placeholder="Что делает эта роль"></label></div><div class="elms-company-access-capabilities">' + capabilityOptions(context.capabilities, []) + '</div><div class="elms-company-access-actions"><button type="submit" class="elms-company-access-button is-primary" data-company-role-submit>Создать роль</button><button type="button" class="elms-company-access-button" data-company-role-reset>Очистить</button></div></form><div class="elms-company-access-table-wrap"><table class="elms-company-access-table"><thead><tr><th>Роль</th><th>Функциональность</th><th></th></tr></thead><tbody data-company-roles-body></tbody></table></div></section>',
			'</div>'
		].join("");
		bind(root);
		activateTab(root, "invite", false);
		renderRoles(root);
		root.querySelector("[data-company-access-refresh]").addEventListener("click", function () { loadMembers(root); });
		if (context.organization) loadMembers(root);
		else setStatus(root, "Выберите организацию для просмотра.", false);
	}

	function mount(wrapper) {
		if (wrapper._elms_company_access_loading) return;
		wrapper._elms_company_access_loading = true;
		ensureCompanyAccessStyles();
		$(wrapper).addClass("elms-company-access-page-wrapper");
		if (!wrapper._elms_company_access_page) wrapper._elms_company_access_page = frappe.ui.make_app_page({ parent: wrapper, title: "Роли и доступы сотрудников", single_column: true });
		var root = wrapper._elms_company_access_page.main[0];
		call("elms.access.api.get_company_access_context", {}, function (context, error) {
			wrapper._elms_company_access_loading = false;
			if (error || !context) { root.innerHTML = "<div class=\"elms-company-access-shell\"><div class=\"elms-company-access-status error\">" + esc(errorMessage(error)) + "</div></div>"; return; }
			render(root, context);
		});
	}

	window.elmsCompanyAccessPage = mount;

	$(document).on("page-change.elmsCompanyAccess", function () {
		if (!frappe.get_route_str || frappe.get_route_str() !== "elms-company-access") return;
		var wrapper = frappe.pages["elms-company-access"];
		if (!wrapper) return;
		ensureCompanyAccessStyles();
		$(wrapper).addClass("elms-company-access-page-wrapper");
	});
})();

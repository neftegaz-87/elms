(function () {
	"use strict";

	var integrationMeta = {
		LLM: { title: "LLM / помощник", description: "OpenAI-compatible провайдер и модель для этой компании.", url: "/app/elms-company-integration-llm" },
		Bitrix24: { title: "Bitrix24 CRM", description: "Incoming Webhook для заявок и обмена с Bitrix24.", url: "/app/elms-company-integration-bitrix24" },
		"Custom API": { title: "Custom API", description: "Произвольный endpoint для операционных интеграций компании.", url: "/app/elms-company-integration-custom-api" }
	};

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
		return typeof message === "string" ? message.replace(/<[^>]+>/g, "").trim() : "Операция не выполнена. Проверьте права и настройки.";
	}

	function setStatus(root, message, isError) {
		var node = root.querySelector("[data-company-integrations-status]");
		if (!node) return;
		node.textContent = message || "";
		node.hidden = !message;
		node.className = "elms-company-integrations-status" + (isError ? " error" : "");
	}

	function organization(root) {
		var select = root.querySelector("[data-company-integrations-organization]");
		return select ? select.value : (root.getAttribute("data-organization") || "");
	}

	function fieldValue(form, name) {
		var field = form.querySelector("[name='" + name + "']");
		return field ? field.value : "";
	}

	function integrationMap(rows) {
		var map = {};
		(rows || []).forEach(function (row) { map[row.integration_type] = row; });
		return map;
	}

	function organizationSelector(context) {
		if (context.platform_admin) {
			return '<label>Организация<select data-company-integrations-organization>' + (context.organizations || []).map(function (value) {
				return '<option value="' + esc(value) + '"' + (value === context.organization ? " selected" : "") + '>' + esc(value) + '</option>';
			}).join("") + '</select></label>';
		}
		return '<div><div class="elms-company-integrations-kicker">Организация</div><strong>' + esc(context.organization) + '</strong></div>';
	}

	function statusBadge(row) {
		return '<span class="elms-company-integrations-badge ' + (row && row.enabled ? "is-on" : "") + '">' + (row && row.enabled ? "Включена" : "Не настроена") + '</span>';
	}

	function overviewCard(type, row) {
		var meta = integrationMeta[type];
		return '<section class="elms-company-integrations-card elms-company-integrations-overview-card"><div class="elms-company-integrations-card-head"><div><div class="elms-company-integrations-kicker">' + esc(type) + '</div><h2>' + esc(meta.title) + '</h2></div>' + statusBadge(row) + '</div><p>' + esc(meta.description) + '</p><a class="elms-company-integrations-button is-primary" href="' + esc(meta.url) + '" data-company-integrations-route="' + esc(meta.url.slice(5)) + '">Настроить</a></section>';
	}

	function formMarkup(type, row) {
		row = row || {};
		var meta = integrationMeta[type];
		var isLLM = type === "LLM";
		var configured = isLLM ? row.api_key_configured : row.webhook_configured;
		return '<section class="elms-company-integrations-card"><div class="elms-company-integrations-card-head"><div><div class="elms-company-integrations-kicker">' + esc(type) + '</div><h2>' + esc(meta.title) + '</h2></div>' + statusBadge(row) + '</div><p>' + esc(meta.description) + '</p>' +
			'<form data-company-integration-form data-integration-type="' + esc(type) + '">' +
			'<label class="elms-company-integrations-check"><input type="checkbox" name="enabled"' + (row.enabled ? " checked" : "") + '> Использовать интеграцию</label>' +
			'<label>Base URL<input name="base_url" value="' + esc(row.base_url || "") + '" placeholder="https://…"></label>' +
			(isLLM ? '<label>Модель по умолчанию<input name="default_model" value="' + esc(row.default_model || "") + '" placeholder="model-name"></label>' : "") +
			'<label>' + (isLLM ? "API Key" : "Webhook URL") + '<input name="' + (isLLM ? "api_key" : "webhook_url") + '" type="password" placeholder="' + (configured ? "Оставьте пустым, чтобы сохранить текущий секрет" : "Введите секрет") + '"></label>' +
			(type === "Custom API" ? '<label>Дополнительная конфигурация JSON<textarea name="config_json" rows="6">' + esc(row.config_json || "") + '</textarea></label>' : "") +
			'<div class="elms-company-integrations-actions"><button type="submit" class="elms-company-integrations-button is-primary">Сохранить</button>' + (row.name ? '<button type="button" class="elms-company-integrations-button is-danger" data-company-integration-delete="' + esc(type) + '">Удалить</button>' : "") + '</div></form></section>';
	}

	function headerMarkup(type) {
		var title = type ? integrationMeta[type].title : "Интеграции компании";
		var description = type ? integrationMeta[type].description : "Каждое подключение компании настраивается на своей странице. Платформенные настройки остаются в Settings и не смешиваются с кабинетом организации.";
		return '<header class="elms-company-integrations-header"><div><div class="elms-company-integrations-kicker">Контур компании</div><h1>' + esc(title) + '</h1><p>' + esc(description) + '</p></div><span class="elms-company-integrations-mark">elms</span></header>';
	}

	function render(root, context, type) {
		root.setAttribute("data-organization", context.organization || "");
		var rows = integrationMap(context.integrations);
		var content = type ? formMarkup(type, rows[type]) : Object.keys(integrationMeta).map(function (key) { return overviewCard(key, rows[key]); }).join("");
		var back = type ? '<a class="elms-company-integrations-back" href="/app/elms-company-integrations" data-company-integrations-route="elms-company-integrations">← Все интеграции</a>' : "";
		root.innerHTML = '<div class="elms-company-integrations-shell"><div class="elms-company-integrations-navigation">' + back + '</div>' + headerMarkup(type) + '<div class="elms-company-integrations-toolbar">' + organizationSelector(context) + '<button type="button" class="elms-company-integrations-button" data-company-integrations-refresh>Обновить</button></div><div class="elms-company-integrations-status" data-company-integrations-status role="status" aria-live="polite" hidden></div><div class="elms-company-integrations-grid ' + (type ? "is-detail" : "is-overview") + '">' + content + '</div></div>';
		bind(root, type);
	}

	function load(root, type, selected) {
		var args = selected ? { organization: selected } : {};
		setStatus(root, "Загружаем настройки…", false);
		call("elms.integrations.api.get_organization_integrations", args, function (context, error) {
			if (error || !context) { setStatus(root, errorMessage(error), true); return; }
			render(root, context, type);
			setStatus(root, "Настройки загружены.", false);
		});
	}

	function bind(root, type) {
		root.querySelectorAll("[data-company-integrations-route]").forEach(function (link) {
			link.addEventListener("click", function (event) {
				var route = link.getAttribute("data-company-integrations-route");
				event.preventDefault();
				if (frappe.pages && frappe.pages[route] && !frappe.pages[route].nodeType) delete frappe.pages[route];
				if (frappe.set_route) frappe.set_route(route);
			});
		});
		var selector = root.querySelector("[data-company-integrations-organization]");
		if (selector) selector.addEventListener("change", function () { load(root, type, selector.value); });
		var refresh = root.querySelector("[data-company-integrations-refresh]");
		if (refresh) refresh.addEventListener("click", function () { load(root, type, organization(root)); });
		var form = root.querySelector("[data-company-integration-form]");
		if (!form) return;
		form.addEventListener("submit", function (event) {
			event.preventDefault();
			var args = { organization: organization(root), integration_type: form.getAttribute("data-integration-type"), enabled: form.querySelector("[name='enabled']").checked ? 1 : 0, base_url: fieldValue(form, "base_url"), default_model: fieldValue(form, "default_model"), api_key: fieldValue(form, "api_key"), webhook_url: fieldValue(form, "webhook_url"), config_json: fieldValue(form, "config_json") };
			call("elms.integrations.api.save_organization_integration", args, function (result, error) {
				if (error || !result) { setStatus(root, errorMessage(error), true); return; }
				load(root, type, organization(root));
			});
		});
		var remove = form.querySelector("[data-company-integration-delete]");
		if (remove) remove.addEventListener("click", function () {
			if (!window.confirm("Удалить настройки " + remove.getAttribute("data-company-integration-delete") + " для этой организации?")) return;
			call("elms.integrations.api.delete_organization_integration", { organization: organization(root), integration_type: remove.getAttribute("data-company-integration-delete") }, function (result, error) {
				if (error || !result) { setStatus(root, errorMessage(error), true); return; }
				load(root, type, organization(root));
			});
		});
	}

	function mount(wrapper, type) {
		$(wrapper).addClass("elms-company-integrations-page-wrapper");
		if (!wrapper._elms_company_integrations_page) wrapper._elms_company_integrations_page = frappe.ui.make_app_page({ parent: wrapper, title: type ? integrationMeta[type].title : "Интеграции компании", single_column: true });
		load(wrapper._elms_company_integrations_page.main[0], type, "");
	}

	window.elmsCompanyIntegrationsPage = mount;
})();

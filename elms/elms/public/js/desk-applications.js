(function () {
	"use strict";

	var pageName = "elms-applications";
	var pageLabel = "Заявки из Bitrix";
	var retryDelays = [0, 250, 1000];

	function esc(value) {
		return String(value === null || value === undefined ? "" : value)
			.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
			.replace(/\"/g, "&quot;").replace(/'/g, "&#039;");
	}

	function call(method, args, done) {
		frappe.call({
			method: method,
			args: args || {},
			callback: function (response) {
				if (response && response.message !== undefined) done(response.message, null);
				else done(null, response || { message: "Пустой ответ сервера" });
			},
			error: function (error) { done(null, error || { message: "Не удалось выполнить запрос" }); }
		});
	}

	function errorText(error) {
		var message = error && (error.message || error.exception || error._server_messages);
		if (typeof message !== "string") return "Не удалось обновить заявку. Проверьте права и доступность Bitrix.";
		try {
			var parsed = JSON.parse(message);
			if (Array.isArray(parsed) && parsed[0]) message = parsed[0].message || parsed[0];
		} catch (ignored) {}
		return String(message).replace(/<[^>]+>/g, "").trim();
	}

	function setMessage(root, text, kind) {
		var node = root.querySelector("[data-applications-message]");
		if (!node) return;
		node.className = "elms-applications-message" + (kind ? " " + kind : "");
		node.textContent = text || "";
		node.hidden = !text;
	}

	function value(form, name) {
		var field = form.querySelector('[name="' + name + '"]');
		return field ? String(field.value || "").trim() : "";
	}

	function renderRows(root, rows) {
		var body = root.querySelector("[data-applications-rows]");
		if (!body) return;
		if (!rows || !rows.length) {
			body.innerHTML = '<tr><td colspan="6" class="elms-applications-empty">Заявки не найдены.</td></tr>';
			return;
		}
		body.innerHTML = rows.map(function (row) {
			var name = esc(row.name);
			var label = esc(row.display_label || row.last_status_snapshot || "Ожидает синхронизации");
			return '<tr><td><strong>' + esc(row.name) + '</strong><small>' + esc(row.bitrix_id) + '</small></td>' +
				'<td>' + esc(row.application_kind === "legal" ? "Юрлицо" : "Физлицо") + '</td>' +
				'<td>' + esc(row.applicant_name || row.company_name || "—") + '</td>' +
				'<td><span class="elms-applications-badge">' + label + '</span><small>' + esc(row.last_synced_at || "Не синхронизировано") + '</small></td>' +
				'<td>' + esc(row.course || "Несколько курсов") + '</td>' +
				'<td><button class="btn btn-default btn-xs" type="button" data-refresh-application="' + name + '">Обновить из Bitrix</button></td></tr>';
		}).join("");
	}

	function load(root, form) {
		setMessage(root, "Загружаем заявки…", "pending");
		var filters = {};
		var kind = value(form, "application_kind");
		if (kind) filters.application_kind = kind;
		call("elms.applications.api.list_application_links", filters, function (rows, error) {
			if (error || !Array.isArray(rows)) {
				setMessage(root, errorText(error || rows), "error");
				renderRows(root, []);
				return;
			}
			setMessage(root, "Статус в списке читается из Bitrix; локальное изменение недоступно.", "info");
			renderRows(root, rows);
		});
	}

	function render(root) {
		root.innerHTML = '<div class="elms-applications-shell"><header class="elms-applications-header"><div><div class="elms-applications-kicker">OPERATIONS · BITRIX</div><h1>Заявки из Bitrix</h1><p>Bitrix — источник статуса. ELMS показывает только сохранённый read-back snapshot.</p></div><span class="elms-applications-mark">elms</span></header><div class="elms-applications-toolbar"><form data-applications-filter><label>Тип заявки<select name="application_kind"><option value="">Все типы</option><option value="individual">Физлица</option><option value="legal">Юрлица</option></select></label><button class="btn btn-primary" type="submit">Загрузить</button></form><div class="elms-applications-message" data-applications-message role="status" aria-live="polite" hidden></div></div><div class="elms-applications-table-wrap"><table class="table table-bordered"><thead><tr><th>Tracking ref / Lead</th><th>Тип</th><th>Заявитель</th><th>Статус из Bitrix</th><th>Курс</th><th></th></tr></thead><tbody data-applications-rows></tbody></table></div></div>';
		var form = root.querySelector("[data-applications-filter]");
		form.addEventListener("submit", function (event) { event.preventDefault(); load(root, form); });
		root.addEventListener("click", function (event) {
			var button = event.target.closest("[data-refresh-application]");
			if (!button) return;
			button.disabled = true;
			setMessage(root, "Запрашиваем свежий статус из Bitrix…", "pending");
			call("elms.applications.api.refresh_application_status", { name: button.getAttribute("data-refresh-application") }, function (result, error) {
				button.disabled = false;
				if (error || !result) { setMessage(root, errorText(error), "error"); return; }
				setMessage(root, "Статус обновлён из Bitrix.", "success");
				load(root, form);
			});
		});
		load(root, form);
	}

	function registerPage() {
		if (!window.frappe || !frappe.container || !frappe.ui) return;
		frappe.provide("frappe.standard_pages");
		if (frappe.standard_pages[pageName]) return;
		frappe.standard_pages[pageName] = function () {
			var wrapper = frappe.container.add_page(pageName);
			var page = frappe.ui.make_app_page({ parent: wrapper, title: pageLabel, single_column: true });
			$(wrapper).addClass("elms-applications-page-wrapper");
			render(page.main[0]);
		};
	}

	window.elmsApplicationsPage = render;
	retryDelays.forEach(function (delay) { setTimeout(registerPage, delay); });
	$(document).on("toolbar_setup", registerPage);
})();

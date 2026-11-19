(function () {
	"use strict";

	var pageTitle = "Кабинет компании";

	function hasRole(role) {
		return !!(window.frappe && frappe.user && typeof frappe.user.has_role === "function" && frappe.user.has_role(role));
	}

	function isPlatformViewer() {
		return hasRole("ELMS Admin") || hasRole("ELMS Operations User") || hasRole("Administrator") || hasRole("System Manager");
	}

	function escapeHtml(value) {
		return String(value == null ? "" : value)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;")
			.replace(/'/g, "&#039;");
	}

	function errorMessage(error) {
		if (!error) return "Не удалось загрузить кабинет.";
		return error.message || error.exception || error._server_messages || "Не удалось загрузить кабинет.";
	}

	function call(method, args, callback) {
		frappe.call({
			method: method,
			args: args,
			callback: function (response) {
				callback(response && response.message, response && response.exc ? response : null);
			},
		});
	}

	function setFlash(root, message, kind) {
		var flash = root.querySelector("[data-cabinet-status]");
		if (!flash) return;
		flash.textContent = message || "";
		flash.className = "elms-cabinet-flash" + (kind ? " " + kind : "");
		flash.hidden = !message;
	}

	function setPill(root, message, kind) {
		var pill = root.querySelector("[data-cabinet-pill]");
		if (!pill) return;
		pill.textContent = message || "Готово";
		pill.className = "elms-cabinet-status-pill" + (kind ? " " + kind : "");
	}

	function setBusy(root, busy) {
		var buttons = root.querySelectorAll("[data-cabinet-action]");
		for (var index = 0; index < buttons.length; index += 1) {
			buttons[index].disabled = busy;
			buttons[index].setAttribute("aria-busy", busy ? "true" : "false");
		}
	}

	function selectedOrganization(root) {
		var organizationSelect = root.querySelector("[data-cabinet-organization]");
		return organizationSelect ? String(organizationSelect.value || "").trim() : "";
	}

	function organizationOptions(organizations, selected) {
		var options = '<option value="">Выберите организацию</option>';
		return options + (organizations || []).map(function (name) {
			return '<option value="' + escapeHtml(name) + '"' + (name === selected ? " selected" : "") + ">" + escapeHtml(name) + "</option>";
		}).join("");
	}

	function setContext(root, context) {
		var select = root.querySelector("[data-cabinet-organization]");
		var organizations = context && context.organizations ? context.organizations : [];
		var selected = context && context.organization ? context.organization : "";
		if (select) {
			select.innerHTML = organizationOptions(organizations, selected);
			select.value = selected;
			select.disabled = organizations.length < 2;
		}
		root._elmsCabinetContext = context || {};
		var mode = root.querySelector("[data-cabinet-mode]");
		if (mode) {
			mode.textContent = context && context.read_only
				? "режим просмотра: права организации не меняются"
				: "Организация: доступ ограничен членством";
		}
	}

	function loadContext(root, preferred, done) {
		setPill(root, "Проверка доступа…", "is-pending");
		call("elms.access.api.get_company_access_context", { organization: preferred || null }, function (context, error) {
			if (error || !context) {
				setPill(root, "Ошибка", "is-error");
				setFlash(root, errorMessage(error), "error");
				return;
			}
			setContext(root, context);
			if (!selectedOrganization(root)) {
				setPill(root, "Нет организации", "is-pending");
				setFlash(root, "Нет доступной организации для просмотра.", "pending");
				return;
			}
			if (done) done(context);
			else load(root);
		});
	}

	function summarize(rows) {
		var activeAccounts = 0;
		var enrollments = 0;
		var progressSum = 0;
		var progressCount = 0;
		(rows || []).forEach(function (row) {
			if (row.user_enabled) activeAccounts += 1;
			(row.enrollments || []).forEach(function (enrollment) {
				enrollments += 1;
				progressSum += Number(enrollment.progress_pct || 0);
				progressCount += 1;
			});
		});
		return {
			employees: (rows || []).length,
			activeAccounts: activeAccounts,
			enrollments: enrollments,
			avgProgress: progressCount ? Math.round((progressSum / progressCount) * 10) / 10 : 0,
		};
	}

	function renderSummary(root, result) {
		var summary = summarize(result && result.rows ? result.rows : []);
		var total = result && result.total != null ? result.total : summary.employees;
		var orgNames = root.querySelectorAll("[data-cabinet-org-name]");
		var employees = root.querySelector("[data-cabinet-stat-employees]");
		var accounts = root.querySelector("[data-cabinet-stat-accounts]");
		var enrollments = root.querySelector("[data-cabinet-stat-enrollments]");
		var progress = root.querySelector("[data-cabinet-stat-progress]");
		var countLabel = root.querySelector("[data-cabinet-count]");
		var resolvedOrg = (result && result.organization) || "—";
		for (var index = 0; index < orgNames.length; index += 1) {
			orgNames[index].textContent = resolvedOrg;
		}
		if (employees) employees.textContent = String(total);
		if (accounts) accounts.textContent = String(summary.activeAccounts);
		if (enrollments) enrollments.textContent = String(summary.enrollments);
		if (progress) progress.textContent = summary.avgProgress + "%";
		if (countLabel) countLabel.textContent = total ? total + " в списке" : "пусто";
	}

	function enrollmentMarkup(enrollments) {
		if (!enrollments || !enrollments.length) {
			return '<span class="elms-cabinet-muted">Нет зачислений</span>';
		}
		return '<div class="elms-cabinet-enrollments">' + enrollments.map(function (enrollment) {
			var pct = Number(enrollment.progress_pct || 0);
			var clamped = Math.max(0, Math.min(100, pct));
			return [
				'<div class="elms-cabinet-enrollment">',
				"<strong>" + escapeHtml(enrollment.course_name || enrollment.course || "Курс") + "</strong>",
				'<span class="elms-cabinet-enrollment-status">' + escapeHtml(enrollment.status || "—") + "</span>",
				'<div class="elms-cabinet-progress">',
				'<div class="elms-cabinet-progress-meta"><span>Прогресс</span><span>' + escapeHtml(pct) + "%</span></div>",
				'<div class="elms-cabinet-progress-bar" aria-hidden="true"><span style="width:' + clamped + '%"></span></div>',
				"</div>",
				"</div>",
			].join("");
		}).join("") + "</div>";
	}

	function renderRows(root, result) {
		var body = root.querySelector("[data-cabinet-body]");
		var empty = root.querySelector("[data-cabinet-empty]");
		var table = root.querySelector("[data-cabinet-table]");
		var rows = result && result.rows ? result.rows : [];
		if (!body || !empty || !table) return;
		body.innerHTML = rows.map(function (row) {
			return [
				"<tr>",
				'<td class="elms-cabinet-person"><strong>' + escapeHtml(row.full_name || row.user) + "</strong><small>" + escapeHtml(row.email || row.user) + "</small></td>",
				'<td><span class="elms-cabinet-account ' + (row.user_enabled ? "is-enabled" : "is-disabled") + '">' + (row.user_enabled ? "Активна" : "Отключена") + "</span></td>",
				"<td>" + enrollmentMarkup(row.enrollments) + "</td>",
				"</tr>",
			].join("");
		}).join("");
		empty.hidden = rows.length !== 0;
		table.hidden = rows.length === 0;
		renderSummary(root, result || { rows: [] });
	}

	function load(root) {
		var organization = selectedOrganization(root);
		setBusy(root, true);
		setPill(root, "Загрузка…", "is-pending");
		setFlash(root, "Запрашиваем актуальный список…", "pending");
		call("elms.cabinet.api.get_org_roster", { organization: organization || null, page: 1, page_size: 50 }, function (result, error) {
			setBusy(root, false);
			if (error || !result) {
				setPill(root, "Ошибка", "is-error");
				setFlash(root, errorMessage(error), "error");
				return;
			}
			renderRows(root, result);
			setPill(root, result.empty ? "Пусто" : "Готово", result.empty ? "" : "is-ready");
			setFlash(root, result.empty ? "В организации пока нет сотрудников." : "Список обновлён.", result.empty ? "" : "success");
		});
	}

	function exportProgress(root) {
		setBusy(root, true);
		setPill(root, "Экспорт…", "is-pending");
		setFlash(root, "Готовим серверную выгрузку…", "pending");
		call("elms.cabinet.api.export_org_progress", { organization: selectedOrganization(root) || null }, function (result, error) {
			setBusy(root, false);
			if (error || !result || !result.content_base64) {
				setPill(root, "Ошибка", "is-error");
				setFlash(root, errorMessage(error), "error");
				return;
			}
			var link = document.createElement("a");
			link.href = "data:text/csv;charset=utf-8;base64," + result.content_base64;
			link.download = result.filename || "elms-org-export.csv";
			link.rel = "noopener";
			link.hidden = true;
			document.body.appendChild(link);
			link.click();
			link.remove();
			setPill(root, "Готово", "is-ready");
			setFlash(root, "Выгрузка сформирована: " + (result.row_count || 0) + " строк.", "success");
		});
	}

	function render(root) {
		root.innerHTML = [
			'<div class="elms-cabinet-shell">',
			'<header class="elms-cabinet-header">',
			'<div class="elms-cabinet-heading"><div class="elms-cabinet-kicker">Организационный контур</div><h1>Кабинет компании</h1><p>Сотрудники, зачисления и прогресс обучения в выбранной организации.</p></div>',
			'<div class="elms-cabinet-actions"><span data-cabinet-pill class="elms-cabinet-status-pill">Ожидание</span><button class="elms-cabinet-button" data-cabinet-action data-cabinet-export type="button">Экспорт CSV</button><button class="elms-cabinet-button is-primary" data-cabinet-action data-cabinet-refresh type="button">Обновить список</button></div>',
			"</header>",
			'<div class="elms-cabinet-toolbar">',
			'<div class="elms-cabinet-toolbar-meta">',
			'<label data-cabinet-org-label>Организация<select data-cabinet-organization aria-label="Организация для просмотра"><option value="">Загружаем организации…</option></select></label>',
			'<div class="elms-cabinet-org-label elms-cabinet-mode" data-cabinet-mode>Проверяем границу доступа…</div>',
			"</div>",
			"</div>",
			'<div class="elms-cabinet-flash" data-cabinet-status role="status" aria-live="polite" hidden></div>',
			'<div class="elms-cabinet-grid">',
			'<aside class="elms-cabinet-panel">',
			'<div><h3>Организация</h3><div class="elms-cabinet-org-label"><strong data-cabinet-org-name>—</strong></div></div>',
			"<div><h3>Сводка</h3><ul class=\"elms-cabinet-stat-list\">",
			'<li class="elms-cabinet-stat"><span>Сотрудники</span><strong data-cabinet-stat-employees>0</strong></li>',
			'<li class="elms-cabinet-stat"><span>Активные учётки</span><strong data-cabinet-stat-accounts>0</strong></li>',
			'<li class="elms-cabinet-stat"><span>Зачисления</span><strong data-cabinet-stat-enrollments>0</strong></li>',
			'<li class="elms-cabinet-stat"><span>Средний прогресс</span><strong data-cabinet-stat-progress>0%</strong></li>',
			"</ul></div>",
			'<div class="elms-cabinet-note-block"><strong>Данные организации</strong><span>Список формируется на сервере по членству организации. Поле выбора не расширяет права доступа.</span></div>',
			"</aside>",
			'<main class="elms-cabinet-main">',
			'<div class="elms-cabinet-kicker">Состав организации</div>',
			'<div class="elms-cabinet-main-head"><h2>Сотрудники и прогресс</h2><span data-cabinet-count>пусто</span></div>',
			'<div class="elms-cabinet-empty" data-cabinet-empty hidden><strong>Пока нет сотрудников</strong><span>Добавьте участника в организации, чтобы увидеть его зачисления и прогресс.</span></div>',
			'<div class="elms-cabinet-table-wrap"><table class="elms-cabinet-table" data-cabinet-table hidden><thead><tr><th>Сотрудник</th><th>Учётная запись</th><th>Зачисления и прогресс</th></tr></thead><tbody data-cabinet-body></tbody></table></div>',
			"</main>",
			"</div>",
			"</div>",
		].join("");

		var refresh = root.querySelector("[data-cabinet-refresh]");
		if (refresh) refresh.addEventListener("click", function () { load(root); });
		var exportButton = root.querySelector("[data-cabinet-export]");
		if (exportButton) exportButton.addEventListener("click", function () { exportProgress(root); });
		var organizationSelect = root.querySelector("[data-cabinet-organization]");
		if (organizationSelect) {
			organizationSelect.addEventListener("change", function () {
				loadContext(root, organizationSelect.value, function () { load(root); });
			});
		}
		loadContext(root);
	}

	function ensureCss() {
		var styleId = "elms-cabinet-css-inline";
		var style = document.getElementById(styleId);
		if (!style) {
			style = document.createElement("style");
			style.id = styleId;
			document.head.appendChild(style);
		}
		style.textContent = ".elms-cabinet-page-wrapper .page-head {\n\tdisplay: none;\n}\n\n.elms-cabinet-page-wrapper .layout-main-section {\n\tpadding: 0 !important;\n\tborder: 0 !important;\n\tbackground: transparent !important;\n}\n\n.elms-cabinet-shell {\n\t--cabinet-ink: #0b1f33;\n\t--cabinet-muted: #66727f;\n\t--cabinet-line: #d5dce3;\n\t--cabinet-surface: #ffffff;\n\t--cabinet-paper: #f5f7fa;\n\t--cabinet-action: #0d4cd3;\n\t--cabinet-action-soft: #eaf2ff;\n\t--cabinet-success: #167a4a;\n\t--cabinet-success-soft: #eaf7f0;\n\t--cabinet-danger: #a32d25;\n\t--cabinet-danger-soft: #fff0ee;\n\t--cabinet-warning: #b54708;\n\t--cabinet-warning-soft: #fff4e5;\n\tbox-sizing: border-box;\n\tmin-height: calc(100vh - 60px);\n\tpadding: 24px;\n\tbackground: var(--cabinet-paper);\n\tcolor: var(--cabinet-ink);\n\tfont-family: \"Source Sans 3\", -apple-system, BlinkMacSystemFont, \"Segoe UI\", Arial, sans-serif;\n}\n\n.elms-cabinet-shell *,\n.elms-cabinet-shell *::before,\n.elms-cabinet-shell *::after {\n\tbox-sizing: border-box;\n}\n\n.elms-cabinet-header,\n.elms-cabinet-toolbar,\n.elms-cabinet-actions {\n\tdisplay: flex;\n\talign-items: center;\n}\n\n.elms-cabinet-header {\n\tjustify-content: space-between;\n\tgap: 18px;\n\tmargin-bottom: 18px;\n\tpadding-bottom: 18px;\n\tborder-bottom: 1px solid var(--cabinet-line);\n}\n\n.elms-cabinet-heading h1,\n.elms-cabinet-heading p,\n.elms-cabinet-panel h3,\n.elms-cabinet-main h2 {\n\tmargin: 0;\n}\n\n.elms-cabinet-heading h1 {\n\tfont-size: 24px;\n\tline-height: 1.15;\n}\n\n.elms-cabinet-heading p {\n\tmargin-top: 6px;\n\tcolor: var(--cabinet-muted);\n\tmax-width: 640px;\n}\n\n.elms-cabinet-kicker {\n\tcolor: var(--cabinet-action);\n\tfont: 600 11px/1.2 \"IBM Plex Mono\", monospace;\n\tletter-spacing: 0.14em;\n\ttext-transform: uppercase;\n}\n\n.elms-cabinet-actions,\n.elms-cabinet-toolbar {\n\tgap: 8px;\n\tflex-wrap: wrap;\n}\n\n.elms-cabinet-toolbar {\n\tjustify-content: space-between;\n\tmargin-bottom: 14px;\n}\n\n.elms-cabinet-toolbar-meta {\n\tdisplay: flex;\n\talign-items: end;\n\tgap: 12px;\n\tflex-wrap: wrap;\n\tmin-width: 0;\n\tflex: 1;\n}\n\n.elms-cabinet-toolbar label {\n\tdisplay: grid;\n\tgap: 5px;\n\tmin-width: min(320px, 100%);\n\tcolor: var(--cabinet-ink);\n\tfont-size: 13px;\n\tfont-weight: 600;\n}\n\n.elms-cabinet-toolbar input {\n\tmin-height: 38px;\n\tpadding: 8px 10px;\n\tborder: 1px solid var(--cabinet-line);\n\tborder-radius: 4px;\n\tbackground: #fff;\n\tcolor: var(--cabinet-ink);\n\tfont: inherit;\n\tfont-weight: 400;\n}\n\n.elms-cabinet-toolbar input:focus,\n.elms-cabinet-button:focus-visible {\n\toutline: 2px solid rgba(13, 76, 211, 0.22);\n\toutline-offset: 1px;\n\tborder-color: var(--cabinet-action);\n}\n\n.elms-cabinet-org-label {\n\tcolor: var(--cabinet-muted);\n\tfont-size: 14px;\n}\n\n.elms-cabinet-org-label strong {\n\tcolor: var(--cabinet-ink);\n}\n\n.elms-cabinet-status-pill {\n\tdisplay: inline-flex;\n\talign-items: center;\n\tgap: 6px;\n\tpadding: 4px 8px;\n\tborder-radius: 3px;\n\tbackground: #eef2f5;\n\tcolor: var(--cabinet-muted);\n\tfont-size: 12px;\n\tfont-weight: 600;\n}\n\n.elms-cabinet-status-pill.is-ready {\n\tbackground: var(--cabinet-success-soft);\n\tcolor: var(--cabinet-success);\n}\n\n.elms-cabinet-status-pill.is-pending {\n\tbackground: var(--cabinet-action-soft);\n\tcolor: var(--cabinet-action);\n}\n\n.elms-cabinet-status-pill.is-error {\n\tbackground: var(--cabinet-danger-soft);\n\tcolor: var(--cabinet-danger);\n}\n\n.elms-cabinet-button {\n\tborder: 1px solid var(--cabinet-line);\n\tborder-radius: 4px;\n\tbackground: var(--cabinet-surface);\n\tcolor: var(--cabinet-ink);\n\tpadding: 8px 12px;\n\tfont: inherit;\n\tcursor: pointer;\n}\n\n.elms-cabinet-button:hover,\n.elms-cabinet-button:focus-visible {\n\tborder-color: var(--cabinet-action);\n\tcolor: var(--cabinet-action);\n}\n\n.elms-cabinet-button.is-primary {\n\tborder-color: var(--cabinet-action);\n\tbackground: var(--cabinet-action);\n\tcolor: #fff;\n}\n\n.elms-cabinet-button.is-primary:hover,\n.elms-cabinet-button.is-primary:focus-visible {\n\tbackground: #0939a3;\n\tborder-color: #0939a3;\n\tcolor: #fff;\n}\n\n.elms-cabinet-button:disabled {\n\topacity: 0.45;\n\tcursor: wait;\n}\n\n.elms-cabinet-flash {\n\tmargin-bottom: 14px;\n\tpadding: 12px 16px;\n\tborder: 1px solid var(--cabinet-line);\n\tborder-radius: 6px;\n\tbackground: var(--cabinet-surface);\n}\n\n.elms-cabinet-flash.pending {\n\tborder-left: 3px solid var(--cabinet-action);\n}\n\n.elms-cabinet-flash.success {\n\tborder-color: #9fd3b7;\n\tbackground: var(--cabinet-success-soft);\n\tcolor: var(--cabinet-success);\n}\n\n.elms-cabinet-flash.error {\n\tborder-color: #e5b5b0;\n\tbackground: var(--cabinet-danger-soft);\n\tcolor: var(--cabinet-danger);\n}\n\n.elms-cabinet-grid {\n\tdisplay: grid;\n\tgrid-template-columns: minmax(230px, 280px) minmax(0, 1fr);\n\tgap: 14px;\n\talign-items: start;\n}\n\n.elms-cabinet-panel,\n.elms-cabinet-main {\n\tbackground: var(--cabinet-surface);\n\tborder: 1px solid var(--cabinet-line);\n\tborder-radius: 6px;\n}\n\n.elms-cabinet-panel {\n\tpadding: 16px;\n\tdisplay: grid;\n\tgap: 16px;\n}\n\n.elms-cabinet-panel h3 {\n\tmargin-bottom: 10px;\n\tfont-size: 12px;\n\tletter-spacing: 0.08em;\n\ttext-transform: uppercase;\n\tcolor: var(--cabinet-muted);\n}\n\n.elms-cabinet-stat-list {\n\tdisplay: grid;\n\tgap: 10px;\n\tmargin: 0;\n\tpadding: 0;\n\tlist-style: none;\n}\n\n.elms-cabinet-stat {\n\tdisplay: flex;\n\tjustify-content: space-between;\n\tgap: 12px;\n\talign-items: baseline;\n\tpadding: 10px 12px;\n\tborder: 1px solid var(--cabinet-line);\n\tborder-radius: 6px;\n\tbackground: #fafbfc;\n}\n\n.elms-cabinet-stat span {\n\tcolor: var(--cabinet-muted);\n\tfont-size: 13px;\n}\n\n.elms-cabinet-stat strong {\n\tfont: 600 18px/1 \"IBM Plex Mono\", monospace;\n\tcolor: var(--cabinet-ink);\n}\n\n.elms-cabinet-note-block {\n\tdisplay: grid;\n\tgap: 6px;\n\tpadding-top: 4px;\n\tborder-top: 1px solid var(--cabinet-line);\n\tcolor: var(--cabinet-muted);\n\tfont-size: 13px;\n\tline-height: 1.45;\n}\n\n.elms-cabinet-note-block strong {\n\tcolor: var(--cabinet-ink);\n}\n\n.elms-cabinet-main {\n\tpadding: 22px;\n\tmin-height: 440px;\n}\n\n.elms-cabinet-main > .elms-cabinet-kicker {\n\tmargin-bottom: 8px;\n}\n\n.elms-cabinet-main-head {\n\tdisplay: flex;\n\tjustify-content: space-between;\n\talign-items: baseline;\n\tgap: 12px;\n\tmargin-bottom: 18px;\n}\n\n.elms-cabinet-main-head h2 {\n\tfont-size: 21px;\n}\n\n.elms-cabinet-main-head span {\n\tcolor: var(--cabinet-muted);\n\tfont-size: 13px;\n}\n\n.elms-cabinet-table-wrap {\n\toverflow-x: auto;\n}\n\n.elms-cabinet-table {\n\twidth: 100%;\n\tborder-collapse: collapse;\n\ttext-align: left;\n}\n\n.elms-cabinet-table th {\n\tpadding: 10px 12px;\n\tborder-bottom: 1px solid var(--cabinet-line);\n\tcolor: var(--cabinet-muted);\n\tfont: 600 11px/1.2 \"IBM Plex Mono\", monospace;\n\tletter-spacing: 0.08em;\n\ttext-transform: uppercase;\n}\n\n.elms-cabinet-table td {\n\tpadding: 14px 12px;\n\tborder-bottom: 1px solid #e7ebef;\n\tvertical-align: top;\n}\n\n.elms-cabinet-table tr:last-child td {\n\tborder-bottom: 0;\n}\n\n.elms-cabinet-person strong {\n\tdisplay: block;\n\tfont-size: 15px;\n}\n\n.elms-cabinet-person small {\n\tdisplay: block;\n\tmargin-top: 4px;\n\tcolor: var(--cabinet-muted);\n}\n\n.elms-cabinet-account {\n\tdisplay: inline-flex;\n\talign-items: center;\n\tpadding: 4px 8px;\n\tborder-radius: 3px;\n\tbackground: #edf1f5;\n\tcolor: var(--cabinet-muted);\n\tfont-size: 12px;\n\tfont-weight: 600;\n}\n\n.elms-cabinet-account.is-enabled {\n\tbackground: var(--cabinet-success-soft);\n\tcolor: var(--cabinet-success);\n}\n\n.elms-cabinet-account.is-disabled {\n\tbackground: var(--cabinet-danger-soft);\n\tcolor: var(--cabinet-danger);\n}\n\n.elms-cabinet-enrollments {\n\tdisplay: grid;\n\tgap: 8px;\n}\n\n.elms-cabinet-enrollment {\n\tdisplay: grid;\n\tgrid-template-columns: minmax(160px, 1fr) 110px minmax(90px, 120px);\n\tgap: 10px;\n\talign-items: center;\n\tpadding: 8px 10px;\n\tborder: 1px solid var(--cabinet-line);\n\tborder-radius: 6px;\n\tbackground: #fafbfc;\n}\n\n.elms-cabinet-enrollment strong {\n\tfont-size: 13px;\n\tline-height: 1.3;\n}\n\n.elms-cabinet-enrollment-status {\n\tcolor: var(--cabinet-muted);\n\tfont-size: 12px;\n}\n\n.elms-cabinet-progress {\n\tdisplay: grid;\n\tgap: 4px;\n}\n\n.elms-cabinet-progress-meta {\n\tdisplay: flex;\n\tjustify-content: space-between;\n\tgap: 8px;\n\tfont: 600 12px/1 \"IBM Plex Mono\", monospace;\n\tcolor: var(--cabinet-action);\n}\n\n.elms-cabinet-progress-bar {\n\theight: 6px;\n\toverflow: hidden;\n\tborder-radius: 999px;\n\tbackground: #e8eef5;\n}\n\n.elms-cabinet-progress-bar > span {\n\tdisplay: block;\n\theight: 100%;\n\tborder-radius: inherit;\n\tbackground: var(--cabinet-action);\n}\n\n.elms-cabinet-muted {\n\tcolor: var(--cabinet-muted);\n}\n\n.elms-cabinet-empty {\n\tdisplay: grid;\n\tgap: 8px;\n\tpadding: 56px 24px;\n\ttext-align: center;\n\tcolor: var(--cabinet-muted);\n}\n\n.elms-cabinet-empty strong {\n\tcolor: var(--cabinet-ink);\n\tfont-size: 16px;\n}\n\n@media (max-width: 960px) {\n\t.elms-cabinet-grid {\n\t\tgrid-template-columns: 1fr;\n\t}\n\n\t.elms-cabinet-enrollment {\n\t\tgrid-template-columns: 1fr;\n\t}\n}\n\n@media (max-width: 720px) {\n\t.elms-cabinet-shell {\n\t\tpadding: 14px;\n\t}\n\n\t.elms-cabinet-header {\n\t\talign-items: flex-start;\n\t\tflex-direction: column;\n\t}\n\n\t.elms-cabinet-toolbar {\n\t\talign-items: stretch;\n\t\tflex-direction: column;\n\t}\n\n\t.elms-cabinet-actions {\n\t\twidth: 100%;\n\t}\n\n\t.elms-cabinet-button {\n\t\tflex: 1;\n\t}\n}\n\n@media (prefers-reduced-motion: reduce) {\n\t.elms-cabinet-shell *,\n\t.elms-cabinet-shell *::before,\n\t.elms-cabinet-shell *::after {\n\t\ttransition: none !important;\n\t\tanimation: none !important;\n\t}\n}\n";
	}

	function rootFrom(wrapper) {
		if (!wrapper._elms_cabinet_page) return null;
		return wrapper._elms_cabinet_page.main[0];
	}

	function renderPage(wrapper) {
		ensureCss();
		$(wrapper).addClass("elms-cabinet-page-wrapper");
		if (!wrapper._elms_cabinet_page) {
			wrapper._elms_cabinet_page = frappe.ui.make_app_page({
				parent: wrapper,
				title: pageTitle,
				single_column: true,
			});
		}
		wrapper._elms_cabinet_mounted = true;
		render(wrapper._elms_cabinet_page.main[0]);
	}

	function reloadPage(wrapper) {
		ensureCss();
		var root = rootFrom(wrapper);
		if (!root || !root.querySelector(".elms-cabinet-shell")) {
			renderPage(wrapper);
			return;
		}
		loadContext(root, selectedOrganization(root));
	}

	window.elmsCabinetPage = renderPage;
	window.elmsCabinetReload = reloadPage;
})();

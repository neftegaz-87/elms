(function () {
	"use strict";

	var state = {
		allowed: false,
		open: false,
		models: [],
		model: "",
		messages: [],
		error: null,
		busy: false,
		insufficient: false,
		sources: [],
		mounted: false,
		accessChecked: false,
		draft: "",
		pos: null,
		dragging: false,
	};

	var HISTORY_KEY = "elms-assistant-history";
	var POS_KEY = "elms-assistant-pos";
	var RETRY_MS = [0, 200, 500, 1000, 2000, 4000];
	var eventsBound = false;
	var dragBound = false;

	function esc(value) {
		return String(value === null || value === undefined ? "" : value)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;")
			.replace(/'/g, "&#039;");
	}

	function call(method, args, callback) {
		if (!window.frappe || !frappe.call) return;
		frappe.call({
			method: method,
			args: args || {},
			callback: function (response) {
				if (response && response.message) callback(response.message, null);
				else if (callback) callback(null, { message: "Пустой ответ сервера" });
			},
			error: function (error) {
				if (callback) callback(null, error || { message: "Не удалось выполнить запрос" });
			},
		});
	}

	function apiErrorMessage(error) {
		return (error && (error.message || error.exception)) || "Не удалось выполнить запрос. Повторите попытку.";
	}

	function uniqueTexts(items, limit) {
		var seen = {};
		var out = [];
		(items || []).forEach(function (item) {
			var text = String(item || "").replace(/\s+/g, " ").trim();
			if (!text || seen[text]) return;
			seen[text] = true;
			out.push(text);
		});
		return out.slice(0, limit || 16);
	}

	function pathnameWorkspaceSlug() {
		var path = (window.location && window.location.pathname) || "";
		var match = path.match(/\/app\/([^\/?#]+)/i);
		if (!match) return "";
		var slug = decodeURIComponent(match[1] || "").trim();
		var reserved = {
			form: 1,
			list: 1,
			"query-report": 1,
			workspaces: 1,
			workspace: 1,
			"elms-learning": 1,
			"elms-course-studio": 1,
			"elms-course-preview": 1,
			"elms-review": 1,
		};
		if (!slug || reserved[slug.toLowerCase()]) return "";
		return slug;
	}

	function collectCurrentView() {
		var route = [];
		var routeStr = "";
		try {
			route = (window.frappe && frappe.get_route && frappe.get_route()) || [];
		} catch (error) {
			route = [];
		}
		try {
			routeStr = (window.frappe && frappe.get_route_str && frappe.get_route_str()) || "";
		} catch (error) {
			routeStr = Array.isArray(route) ? route.join("/") : "";
		}
		var pathname = (window.location && window.location.pathname) || "";
		var view = {
			route: Array.isArray(route) ? route.slice(0, 12) : [],
			route_str: routeStr || pathname || "",
			pathname: pathname,
			title: document.title || "",
			page: "",
			workspace: "",
			doctype: "",
			docname: "",
			active_tab: "",
			breadcrumbs: [],
			headings: [],
			labels: [],
		};
		if (route[0] === "Form") {
			view.doctype = route[1] || "";
			view.docname = route[2] || "";
		} else if (route[0] === "List" || route[0] === "query-report") {
			view.doctype = route[1] || "";
		} else if (route[0] === "Workspaces" || route[0] === "workspace") {
			view.workspace = route[1] || route[route.length - 1] || "";
		} else if (route[0]) {
			view.page = String(route[0]);
			view.workspace = String(route[0]);
		}
		var slug = pathnameWorkspaceSlug();
		if (slug) {
			view.workspace = view.workspace || slug;
			view.page = view.page || slug;
			if (!view.route_str || view.route_str === "/") view.route_str = "app/" + slug;
		}
		if ((routeStr || pathname).indexOf("elms-learning") >= 0) {
			view.page = "elms-learning";
			view.workspace = "";
		}
		if ((routeStr || pathname).indexOf("elms-course-studio") >= 0) {
			view.page = "elms-course-studio";
			view.workspace = "";
		}
		if ((routeStr || pathname).indexOf("elms-course-preview") >= 0) {
			view.page = "elms-course-preview";
			view.workspace = "";
		}

		var activeTab = document.querySelector(".elms-tab-btn.active, .nav-link.active, .form-tabs .nav-link.active");
		if (activeTab) view.active_tab = (activeTab.textContent || "").trim();

		var crumbs = [];
		document.querySelectorAll("#navbar-breadcrumbs a, #navbar-breadcrumbs li").forEach(function (node) {
			crumbs.push(node.textContent || "");
		});
		view.breadcrumbs = uniqueTexts(crumbs, 8);

		var root =
			document.querySelector(".codex-editor") ||
			document.querySelector(".workspace-sidebar + .layout-main-section") ||
			document.querySelector(".page-container:not(.hide)") ||
			document.querySelector(".elms-learning-shell") ||
			document.querySelector(".elms-course-studio") ||
			document.querySelector("main") ||
			document.body;
		var headings = [];
		var labels = [];
		if (root) {
			root.querySelectorAll(
				"h1, h2, h3, .elms-kicker, .workspace-title, .ellipsis.title-text, .widget-title, .shortcut-widget-box .widget-title, .link-item .link-content, .ce-header"
			).forEach(function (node) {
				headings.push(node.textContent || "");
			});
			root.querySelectorAll(
				"label.control-label, .section-head .section-title, .elms-tab-btn, .form-dashboard-section .section-head, [data-fieldname] > label, .widget .widget-head .widget-title, .onboarding-step-link, .shortcut-widget-box"
			).forEach(function (node) {
				labels.push(node.textContent || "");
			});
		}
		view.headings = uniqueTexts(headings, 16);
		view.labels = uniqueTexts(labels, 24);
		return view;
	}

	function bootAllowed() {
		var value = window.frappe && frappe.boot && frappe.boot.elms_assistant_allowed;
		return value === true || value === 1 || value === "1";
	}

	function historyKey() {
		var user = (window.frappe && frappe.session && frappe.session.user) || "Guest";
		return HISTORY_KEY + ":" + user + ":navbar";
	}

	function loadHistory() {
		try {
			var raw = window.sessionStorage && sessionStorage.getItem(historyKey());
			var parsed = raw ? JSON.parse(raw) : [];
			state.messages = Array.isArray(parsed) ? parsed.slice(-16) : [];
		} catch (error) {
			state.messages = [];
		}
	}

	function saveHistory() {
		if (!window.sessionStorage) return;
		try {
			sessionStorage.setItem(historyKey(), JSON.stringify((state.messages || []).slice(-16)));
		} catch (error) {}
	}

	function posKey() {
		var user = (window.frappe && frappe.session && frappe.session.user) || "Guest";
		return POS_KEY + ":" + user;
	}

	function loadPos() {
		try {
			var raw = window.sessionStorage && sessionStorage.getItem(posKey());
			var parsed = raw ? JSON.parse(raw) : null;
			if (parsed && typeof parsed.left === "number" && typeof parsed.top === "number") {
				state.pos = parsed;
			}
		} catch (error) {
			state.pos = null;
		}
	}

	function savePos() {
		if (!window.sessionStorage || !state.pos) return;
		try {
			sessionStorage.setItem(posKey(), JSON.stringify(state.pos));
		} catch (error) {}
	}

	function modelLabel(model) {
		var text = String(model || "");
		var slash = text.lastIndexOf("/");
		if (slash >= 0 && slash < text.length - 1) return text.slice(slash + 1);
		return text;
	}

	function clampPos(left, top, width, height) {
		var maxLeft = Math.max(8, window.innerWidth - width - 8);
		var maxTop = Math.max(8, window.innerHeight - height - 8);
		return {
			left: Math.min(Math.max(8, left), maxLeft),
			top: Math.min(Math.max(8, top), maxTop),
		};
	}

	function applySlotPos(slot) {
		if (!slot) return;
		if (!state.pos) {
			slot.classList.remove("is-placed");
			slot.style.left = "";
			slot.style.top = "";
			return;
		}
		var rect = slot.getBoundingClientRect();
		var width = rect.width || 400;
		var height = rect.height || 560;
		var next = clampPos(state.pos.left, state.pos.top, width, height);
		state.pos = next;
		slot.classList.add("is-placed");
		slot.style.left = next.left + "px";
		slot.style.top = next.top + "px";
	}

	function captureDraft() {
		var slot = document.querySelector("#elms-assistant-slot");
		var input = slot && slot.querySelector("[data-assistant-input]");
		var select = slot && slot.querySelector("[data-assistant-model]");
		if (input) state.draft = String(input.value || "");
		if (select && select.value) state.model = select.value;
	}

	function findAnchor() {
		var searchBar = document.querySelector("header.navbar .search-bar");
		if (searchBar) return searchBar;
		var input = document.querySelector("#navbar-search");
		if (input && input.closest) {
			var group = input.closest(".search-bar") || input.closest(".input-group") || input;
			return group;
		}
		var form = document.querySelector("header.navbar form.form-inline");
		if (form) return form.lastElementChild || form;
		return document.querySelector("header.navbar .navbar-nav");
	}

	function ensureMount() {
		if (document.querySelector("[data-elms-platform-assistant]")) {
			state.mounted = true;
			return true;
		}
		var anchor = findAnchor();
		if (!anchor || !anchor.parentNode) return false;
		var wrap = document.createElement("div");
		wrap.className = "elms-navbar-assistant";
		wrap.setAttribute("data-elms-platform-assistant", "");
		wrap.hidden = true;
		if (anchor.nextSibling) anchor.parentNode.insertBefore(wrap, anchor.nextSibling);
		else anchor.parentNode.appendChild(wrap);
		if (!document.querySelector("#elms-assistant-slot")) {
			var slot = document.createElement("div");
			slot.id = "elms-assistant-slot";
			slot.className = "elms-assistant-slot elms-assistant-float";
			slot.setAttribute("data-elms-assistant-float", "");
			document.body.appendChild(slot);
		}
		state.mounted = true;
		return true;
	}

	function panelHtml() {
		if (!state.open || !state.allowed) return "";
		var modelOptions = (state.models || [])
			.map(function (model) {
				return (
					'<option value="' +
					esc(model) +
					'"' +
					(model === state.model ? " selected" : "") +
					" title=\"" +
					esc(model) +
					'">' +
					esc(modelLabel(model)) +
					"</option>"
				);
			})
			.join("");
		var messages =
			(state.messages || [])
				.map(function (item) {
					return (
						'<div class="elms-assistant-message is-' +
						esc(item.role) +
						'"><span class="elms-assistant-message-role">' +
						esc(item.role === "user" ? "Вы" : "Помощник") +
						'</span><p class="elms-assistant-message-body">' +
						esc(item.content) +
						"</p></div>"
					);
				})
				.join("") ||
			'<div class="elms-assistant-empty">Спросите про текущее окно Desk, DocType или whitelist API.</div>';
		var status = "";
		if (state.busy) status = '<div class="elms-assistant-status">Запрос к провайдеру…</div>';
		else if (state.error) status = '<div class="elms-assistant-status is-error">' + esc(state.error) + "</div>";
		else if (state.insufficient)
			status = '<div class="elms-assistant-status is-warning">Недостаточно данных в grounded-контексте платформы.</div>';
		return (
			'<div class="elms-assistant-panel' +
			(state.dragging ? " is-dragging" : "") +
			'" data-elms-assistant-panel role="dialog" aria-label="Помощник ELMS">' +
			'<div class="elms-assistant-panel-head" data-assistant-drag>' +
			'<div class="elms-assistant-panel-title"><span class="elms-assistant-drag-hint" aria-hidden="true">⋮⋮</span><h4>Помощник ELMS</h4></div>' +
			'<button class="elms-assistant-close" type="button" data-action="assistant-close" aria-label="Закрыть">×</button>' +
			"</div>" +
			'<div class="elms-assistant-toolbar">' +
			'<label class="elms-assistant-model"><span>Модель</span><select data-assistant-model title="' +
			esc(state.model || "") +
			'">' +
			(modelOptions || '<option value="">Нет моделей</option>') +
			"</select></label>" +
			"</div>" +
			'<div class="elms-assistant-messages" data-assistant-messages>' +
			messages +
			"</div>" +
			status +
			'<div class="elms-assistant-compose">' +
			'<textarea data-assistant-input rows="1" placeholder="Сообщение…">' +
			esc(state.draft || "") +
			"</textarea>" +
			'<button class="elms-assistant-send" type="button" data-action="assistant-send" aria-label="Отправить" title="Отправить"' +
			(state.busy ? " disabled" : "") +
			">↑</button></div></div>"
		);
	}

	function render() {
		if (!ensureMount()) return;
		var mount = document.querySelector("[data-elms-platform-assistant]");
		var slot = document.querySelector("#elms-assistant-slot");
		if (!mount || !slot) return;
		if (!state.dragging) captureDraft();
		if (!state.allowed) {
			mount.hidden = true;
			mount.innerHTML = "";
			slot.innerHTML = "";
			slot.hidden = true;
			return;
		}
		mount.hidden = false;
		mount.innerHTML =
			'<button class="btn btn-default btn-sm elms-navbar-assistant-btn" type="button" data-elms-assistant data-action="assistant-toggle">' +
			(state.open ? "Скрыть" : "Помощник ELMS") +
			"</button>";
		slot.hidden = !state.open;
		slot.innerHTML = panelHtml();
		bindEvents();
		if (state.open) {
			applySlotPos(slot);
			var box = slot.querySelector("[data-assistant-messages]");
			if (box) box.scrollTop = box.scrollHeight;
			var input = slot.querySelector("[data-assistant-input]");
			if (input) {
				input.style.height = "40px";
				input.style.height = Math.min(96, Math.max(40, input.scrollHeight)) + "px";
			}
		}
	}

	function openPanel() {
		if (!state.allowed) return;
		state.open = true;
		state.error = null;
		loadHistory();
		loadPos();
		render();
		call("elms.ai.api.get_models", {}, function (result, error) {
			if (error) {
				state.error = apiErrorMessage(error);
				state.models = [];
				render();
				return;
			}
			state.models = (result && result.models) || [];
			state.model = (result && result.default_model) || state.models[0] || "";
			render();
		});
	}

	function sendQuestion(presetQuestion) {
		var slot = document.querySelector("#elms-assistant-slot");
		var input = slot && slot.querySelector("[data-assistant-input]");
		var select = slot && slot.querySelector("[data-assistant-model]");
		var question = presetQuestion || (input ? String(input.value || "").trim() : "");
		if (!question || state.busy || !state.allowed) return;
		state.model = select ? select.value : state.model;
		state.draft = "";
		state.busy = true;
		state.error = null;
		state.insufficient = false;
		state.sources = [];
		state.open = true;
		state.messages = (state.messages || []).concat([{ role: "user", content: question }]);
		saveHistory();
		render();
		var history = (state.messages || []).slice(0, -1).map(function (item) {
			return { role: item.role, content: item.content };
		});
		function finish(result, error) {
			state.busy = false;
			if (error) {
				state.error = apiErrorMessage(error);
				render();
				return;
			}
			state.messages = (state.messages || []).concat([
				{ role: "assistant", content: (result && result.answer) || "" },
			]);
			state.sources = (result && result.sources) || [];
			state.insufficient = !!(result && result.insufficient_data);
			state.model = (result && result.model) || state.model;
			saveHistory();
			render();
		}
		var view = collectCurrentView();
		if (!state.model) {
			call("elms.ai.api.get_models", {}, function (modelsResult, modelsError) {
				if (modelsError) {
					finish(null, modelsError);
					return;
				}
				state.models = (modelsResult && modelsResult.models) || [];
				state.model = (modelsResult && modelsResult.default_model) || state.models[0] || "";
				call(
					"elms.ai.api.ask",
					{ question: question, model: state.model, history: history, view: view },
					finish
				);
			});
			return;
		}
		call("elms.ai.api.ask", { question: question, model: state.model, history: history, view: view }, finish);
	}

	function bindEvents() {
		if (eventsBound) return;
		eventsBound = true;
		document.addEventListener("click", function (event) {
			var actionEl = event.target && event.target.closest && event.target.closest("[data-action]");
			if (!actionEl) return;
			var inAssistant =
				actionEl.closest("[data-elms-platform-assistant]") ||
				actionEl.closest("#elms-assistant-slot");
			if (!inAssistant) return;
			var action = actionEl.getAttribute("data-action");
			if (action === "assistant-toggle") {
				if (state.open) {
					captureDraft();
					state.open = false;
					render();
				} else {
					openPanel();
				}
			}
			if (action === "assistant-close") {
				captureDraft();
				state.open = false;
				render();
			}
			if (action === "assistant-send") sendQuestion();
		});
		document.addEventListener("change", function (event) {
			var select = event.target && event.target.closest && event.target.closest("[data-assistant-model]");
			if (!select || !select.closest("#elms-assistant-slot")) return;
			state.model = select.value || "";
			select.setAttribute("title", state.model);
		});
		document.addEventListener("input", function (event) {
			var input = event.target && event.target.closest && event.target.closest("[data-assistant-input]");
			if (!input || !input.closest("#elms-assistant-slot")) return;
			state.draft = String(input.value || "");
			input.style.height = "40px";
			input.style.height = Math.min(96, Math.max(40, input.scrollHeight)) + "px";
		});
		document.addEventListener("keydown", function (event) {
			var input = event.target && event.target.closest && event.target.closest("[data-assistant-input]");
			if (!input || !input.closest("#elms-assistant-slot")) return;
			if (event.key === "Enter" && !event.shiftKey) {
				event.preventDefault();
				sendQuestion();
			}
		});
		bindDrag();
	}

	function bindDrag() {
		if (dragBound) return;
		dragBound = true;
		var origin = null;
		document.addEventListener("mousedown", function (event) {
			if (event.button !== 0) return;
			var handle = event.target && event.target.closest && event.target.closest("[data-assistant-drag]");
			if (!handle || !handle.closest("#elms-assistant-slot")) return;
			if (event.target.closest("[data-action]")) return;
			var slot = document.querySelector("#elms-assistant-slot");
			var panel = slot && slot.querySelector("[data-elms-assistant-panel]");
			if (!slot || !panel) return;
			var rect = slot.getBoundingClientRect();
			origin = {
				startX: event.clientX,
				startY: event.clientY,
				left: rect.left,
				top: rect.top,
				width: rect.width,
				height: rect.height,
			};
			state.dragging = true;
			panel.classList.add("is-dragging");
			event.preventDefault();
		});
		document.addEventListener("mousemove", function (event) {
			if (!origin) return;
			var slot = document.querySelector("#elms-assistant-slot");
			if (!slot) return;
			var next = clampPos(
				origin.left + (event.clientX - origin.startX),
				origin.top + (event.clientY - origin.startY),
				origin.width,
				origin.height
			);
			state.pos = next;
			slot.classList.add("is-placed");
			slot.style.left = next.left + "px";
			slot.style.top = next.top + "px";
		});
		document.addEventListener("mouseup", function () {
			if (!origin) return;
			origin = null;
			state.dragging = false;
			savePos();
			var panel = document.querySelector("#elms-assistant-slot [data-elms-assistant-panel]");
			if (panel) panel.classList.remove("is-dragging");
		});
	}

	function resolveAccess() {
		if (bootAllowed()) {
			state.allowed = true;
			state.accessChecked = true;
			render();
		}
		call("elms.ai.api.get_access", {}, function (access, error) {
			state.accessChecked = true;
			if (!error && access) {
				state.allowed = !!access.allowed;
			} else if (!state.allowed) {
				state.allowed = bootAllowed();
			}
			render();
		});
	}

	function bootstrap() {
		if (!window.frappe || !frappe.session || frappe.session.user === "Guest") return;
		if (!ensureMount()) return;
		resolveAccess();
	}

	function installWithRetries() {
		RETRY_MS.forEach(function (delay) {
			setTimeout(bootstrap, delay);
		});
	}

	$(document).on("toolbar_setup", function () {
		setTimeout(bootstrap, 0);
		setTimeout(bootstrap, 300);
	});
	$(document).ready(installWithRetries);
})();

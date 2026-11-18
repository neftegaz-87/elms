(function () {
	"use strict";

	var state = { root: null, catalog: [], profile: null, payment: null, loading: false, admissionImport: null };

	function esc(value) {
		return String(value == null ? "" : value)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;")
			.replace(/'/g, "&#039;");
	}

	function call(method, args, callback) {
		frappe.call({
			method: method,
			args: args || {},
			callback: function (response) {
				if (response && response.message) callback(response.message, null);
				else callback(null, response || { message: "Пустой ответ сервера" });
			},
			error: function (error) { callback(null, error || { message: "Не удалось выполнить запрос" }); }
		});
	}

	function status(root, message, kind) {
		var node = root.querySelector("[data-admission-status]");
		if (!node) return;
		node.textContent = message || "";
		node.className = "elms-admission-status" + (kind ? " " + kind : "");
		node.hidden = !message;
	}

	function errorText(error) {
		return (error && (error.message || error.exception)) || "Не удалось сохранить анкету. Проверьте поля и попробуйте снова.";
	}

	function selectedBatch(root) {
		var select = root.querySelector("[data-admission-batch]");
		return select ? select.value : "";
	}

	function routeBatch() {
		var route = frappe.get_route && frappe.get_route();
		if (route && route[0] === "elms-admission" && route[1]) return route[1];
		return frappe.route_options && frappe.route_options.batch ? frappe.route_options.batch : "";
	}

	function selectedCourse(root) {
		var batch = selectedBatch(root);
		var item = state.catalog.find(function (course) { return course.batch === batch; });
		return item ? item.course : "";
	}

	function canManageImport() {
		var roles = frappe.user_roles || [];
		return roles.indexOf("ELMS Company Admin") !== -1 || roles.indexOf("ELMS Admin") !== -1 || roles.indexOf("ELMS Operations User") !== -1;
	}

	function importMarkup() {
		if (!canManageImport()) return "";
		return [
			'<section class="elms-admission-import" data-admission-import>',
				'<div class="elms-admission-import-heading"><div><span class="elms-admission-section-label">B2B / admission desk</span><h2>Загрузка заявки организации</h2><p>Канонический XLSX станет проверяемым preview. Непрошедшие строки останутся с явной ошибкой.</p></div><span class="elms-admission-import-version">admission-xlsx-v1</span></div>',
			'<form data-admission-import-form class="elms-admission-import-form"><label class="elms-admission-field"><span>Файл заявки</span><input data-admission-import-file type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" required></label><label class="elms-admission-checkbox"><input data-admission-new-revision type="checkbox"><span>Создать новую ревизию при повторной загрузке</span></label><button type="submit" class="elms-admission-button is-primary">Загрузить и разобрать</button></form>',
			'<div class="elms-admission-import-status" data-admission-import-status aria-live="polite" hidden></div>',
			'<div class="elms-admission-import-result" data-admission-import-result hidden><div class="elms-admission-import-toolbar"><div><strong data-admission-import-title>Preview</strong><span data-admission-import-meta></span></div><div class="elms-admission-import-actions"><button type="button" class="elms-admission-button" data-admission-import-export>Экспорт проверенных строк</button><button type="button" class="elms-admission-button is-subtle" data-admission-import-refresh>Обновить preview</button></div></div><div class="elms-admission-import-table-wrap"><table class="elms-admission-import-table"><thead><tr><th>Строка</th><th>ФИО</th><th>СНИЛС</th><th>Программа</th><th>Статус</th><th>Учётные данные</th></tr></thead><tbody data-admission-import-rows></tbody></table></div></div>',
			'</section>'
		].join("");
	}

	function importStatus(root, message, kind) {
		var node = root.querySelector("[data-admission-import-status]");
		if (!node) return;
		node.textContent = message || "";
		node.className = "elms-admission-import-status" + (kind ? " " + kind : "");
		node.hidden = !message;
	}

	function renderImportPreview(root, result) {
		var section = root.querySelector("[data-admission-import-result]");
		var body = root.querySelector("[data-admission-import-rows]");
		if (!section || !body || !result) return;
		state.admissionImport = result;
		section.hidden = false;
		var title = root.querySelector("[data-admission-import-title]");
		var meta = root.querySelector("[data-admission-import-meta]");
		if (title) title.textContent = "Preview " + (result.name || "");
		if (meta) meta.textContent = " · " + (result.status || "draft") + " · ревизия " + (result.revision || 1) + " · строк " + (result.total_rows || 0);
		body.innerHTML = (result.rows || []).map(function (row) {
			var errors = (row.errors || []).join("; ");
			var credential = row.credential ? '<button type="button" class="elms-admission-reveal" data-admission-reveal data-credential="' + esc(row.credential) + '">Показать invite-token</button><span class="elms-admission-token" data-admission-token="' + esc(row.credential) + '"></span>' : "—";
			return '<tr class="is-' + esc(row.status || "invalid") + '"><td>' + esc(row.source_row_number) + '</td><td><strong>' + esc(row.fio) + '</strong><small>' + esc(row.profession || "") + '</small></td><td>' + esc(row.snils || "") + '</td><td>' + esc(row.program || "") + '</td><td><span class="elms-admission-row-state">' + esc(row.status || "invalid") + '</span><small>' + esc(errors) + '</small></td><td>' + credential + '</td></tr>';
		}).join("") || '<tr><td colspan="6" class="elms-admission-empty">Проверенных строк пока нет.</td></tr>';
		Array.prototype.forEach.call(root.querySelectorAll("[data-admission-reveal]"), function (button) {
			button.addEventListener("click", function () { revealImportCredential(root, button); });
		});
	}

	function inspectImport(root, importName) {
		if (!importName) return;
		call("elms.admission.import_api.inspect_import", { import_name: importName, page: 1, page_length: 100 }, function (result, error) {
			if (error || !result) return importStatus(root, errorText(error), "is-error");
			renderImportPreview(root, result);
			importStatus(root, result.status === "parsed" ? "Проверка завершена. Можно экспортировать validated rows." : (result.parse_error || "Импорт завершён с ошибками."), result.status === "parsed" ? "is-success" : "is-error");
		});
	}

	function revealImportCredential(root, button) {
		button.disabled = true;
		call("elms.admission.import_api.reveal_credential", { credential: button.getAttribute("data-credential"), reveal_intent: true }, function (result, error) {
			if (error || !result) {
				button.disabled = false;
				return importStatus(root, errorText(error), "is-error");
			}
			var token = root.querySelector('[data-admission-token="' + button.getAttribute("data-credential") + '"]');
			if (token) token.textContent = " · " + result.invite_token;
			button.remove();
			importStatus(root, "Invite-token раскрыт один раз и записан в аудит.", "is-success");
		});
	}

	function exportImport(root) {
		if (!state.admissionImport || !state.admissionImport.name) return;
		call("elms.admission.import_api.export_import", { import_name: state.admissionImport.name }, function (result, error) {
			if (error || !result) return importStatus(root, errorText(error), "is-error");
			var blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
			var link = document.createElement("a");
			link.href = URL.createObjectURL(blob);
			link.download = (state.admissionImport.name || "admission-import") + ".json";
			link.click();
			URL.revokeObjectURL(link.href);
			importStatus(root, "Экспорт проверенных строк подготовлен.", "is-success");
		});
	}

	function wireImport(root) {
		var form = root.querySelector("[data-admission-import-form]");
		if (!form) return;
		form.addEventListener("submit", function (event) {
			event.preventDefault();
			var input = root.querySelector("[data-admission-import-file]");
			var button = form.querySelector("button[type='submit']");
			if (!input.files || !input.files[0]) return importStatus(root, "Прикрепите XLSX-файл заявки.", "is-error");
			button.disabled = true;
			importStatus(root, "Загружаем файл и ждём bounded AI parse…", "is-pending");
			fileAsPayload(input).then(function (file) {
				return new Promise(function (resolve, reject) {
					call("elms.admission.import_api.upload_import", { file_name: file.file_name, content: file.content, content_type: file.content_type, new_revision: root.querySelector("[data-admission-new-revision]").checked }, function (result, error) {
						if (error || !result) reject(error || new Error("Пустой ответ сервера"));
						else resolve(result);
					});
				});
			}).then(function (result) {
				inspectImport(root, result.name);
			}).catch(function (error) {
				importStatus(root, errorText(error), "is-error");
			}).then(function () { button.disabled = false; });
		});
		var exportButton = root.querySelector("[data-admission-import-export]");
		if (exportButton) exportButton.addEventListener("click", function () { exportImport(root); });
		var refreshButton = root.querySelector("[data-admission-import-refresh]");
		if (refreshButton) refreshButton.addEventListener("click", function () { inspectImport(root, state.admissionImport && state.admissionImport.name); });
	}

	function fileAsPayload(input) {
		return new Promise(function (resolve, reject) {
			var file = input && input.files && input.files[0];
			if (!file) return reject(new Error("Прикрепите обязательный документ"));
			var reader = new FileReader();
			reader.onload = function () {
				resolve({ file_name: file.name, content: String(reader.result), content_type: file.type || null });
			};
			reader.onerror = function () { reject(new Error("Не удалось прочитать файл")); };
			reader.readAsDataURL(file);
		});
	}

	function formPayload(root) {
		var form = root.querySelector("[data-admission-form]");
		var consent = form.querySelector("[name='consent_version']");
		var value = function (name) {
			var field = form.querySelector("[name='" + name + "']");
			return field ? field.value.trim() : "";
		};
		return Promise.all([
			fileAsPayload(form.querySelector("[name='passport_scan']")),
			fileAsPayload(form.querySelector("[name='snils_scan']")),
			fileAsPayload(form.querySelector("[name='education_doc_scan']")),
		]).then(function (files) {
			return {
				fio_first_name: value("fio_first_name"),
				fio_last_name: value("fio_last_name"),
				fio_middle_name: value("fio_middle_name"),
				birth_date: value("birth_date"),
				passport_series: value("passport_series"),
				passport_number: value("passport_number"),
				snils: value("snils"),
				education_level: value("education_level"),
				profession: value("profession"),
				phone: value("phone"),
				consent_version: consent.checked ? consent.value : "",
				passport_scan: files[0],
				snils_scan: files[1],
				education_doc_scan: files[2],
			};
		});
	}

	function input(name, label, type, value) {
		return '<label class="elms-admission-field"><span>' + esc(label) + '</span><input name="' + name + '" type="' + (type || "text") + '" value="' + esc(value || "") + '" required></label>';
	}

	function render(root) {
		var profile = state.profile && state.profile.profile ? state.profile.profile : {};
		var catalog = state.catalog || [];
		var profileReady = Boolean(state.profile && state.profile.exists);
		var requestedBatch = routeBatch();
		var options = catalog.map(function (course) {
			var selected = course.batch === requestedBatch ? " selected" : "";
			return '<option value="' + esc(course.batch) + '"' + selected + '>' + esc(course.course_name || "Курс") + " — " + esc(course.batch_name || course.batch) + "</option>";
		}).join("");
		root.innerHTML = [
			'<div class="elms-admission-shell">',
			'<header class="elms-admission-header"><div><div class="elms-admission-kicker">ПОСТУПЛЕНИЕ / 01</div><h1>Анкета слушателя</h1><p>Заполните профиль и приложите документы. Оплата откроется после проверки анкеты.</p></div><span class="elms-admission-badge">LearnerProfile</span></header>',
			'<div class="elms-admission-route" aria-label="Порядок поступления"><span class="is-active">01 Анкета</span><span>02 Документы</span><span>03 Оплата</span></div>',
			importMarkup(),
			'<div class="elms-admission-status" data-admission-status aria-live="polite" hidden></div>',
			'<form data-admission-form novalidate>',
			'<section class="elms-admission-card"><div class="elms-admission-card-head"><span>Выбор обучения</span><small>Опубликованный поток</small></div>',
			'<label class="elms-admission-field"><span>Курс и поток</span><select name="batch" data-admission-course data-admission-batch required>' + (options || '<option value="">Нет доступных потоков</option>') + '</select></label></section>',
			'<section class="elms-admission-card"><div class="elms-admission-card-head"><span>Данные слушателя</span><small>Обязательные поля отмечены</small></div><div class="elms-admission-grid">',
			input("fio_last_name", "Фамилия", "text", profile.fio_last_name), input("fio_first_name", "Имя", "text", profile.fio_first_name), input("fio_middle_name", "Отчество", "text", profile.fio_middle_name), input("birth_date", "Дата рождения", "date", profile.birth_date), input("passport_series", "Серия паспорта", "text", profile.passport_series), input("passport_number", "Номер паспорта", "text", profile.passport_number), input("snils", "СНИЛС", "text", profile.snils), input("education_level", "Образование", "text", profile.education_level), input("profession", "Профессия", "text", profile.profession), input("phone", "Телефон", "tel", profile.phone),
			'</div></section>',
			'<section class="elms-admission-card"><div class="elms-admission-card-head"><span>Сканы документов</span><small>Файлы сохраняются приватно</small></div><div class="elms-admission-grid elms-admission-files">',
			'<label class="elms-admission-field"><span>Паспорт</span><input name="passport_scan" type="file" accept="application/pdf,image/*" required></label>',
			'<label class="elms-admission-field"><span>СНИЛС</span><input name="snils_scan" type="file" accept="application/pdf,image/*" required></label>',
			'<label class="elms-admission-field"><span>Документ об образовании</span><input name="education_doc_scan" type="file" accept="application/pdf,image/*" required></label>',
			'</div></section>',
			'<section class="elms-admission-card elms-admission-consent"><label><input name="consent_version" type="checkbox" value="pd-2026-01" required><span>Согласен на обработку персональных данных по тексту версии <strong>pd-2026-01</strong>.</span></label></section>',
			'<section class="elms-admission-card elms-admission-payment" data-admission-payment data-payment-state="idle"' + (profileReady ? '' : ' hidden') + '><div class="elms-admission-card-head"><span>Оплата обучения</span><small data-admission-payment-status>Профиль проверен</small></div><p>Оплата создаётся через платёжный сервис. Зачисление появится только после подтверждённого webhook. Статус оплаты хранится в ELMS Payment; ручная отметка недоступна.</p><button type="button" class="elms-admission-button" data-admission-pay>Перейти к оплате</button><a class="elms-admission-learning-link" data-admission-learning-link hidden href="/app/elms-learning">Открыть обучение</a></section>',
			'<div class="elms-admission-actions"><button type="submit" class="elms-admission-button is-primary" data-admission-submit>Сохранить анкету</button><span>После сохранения станет доступен следующий шаг — оплата.</span></div>',
			'</form></div>',
		].join("");
		var consent = root.querySelector("[name='consent_version']");
		if (consent && profile.consent_version) consent.checked = true;
		var form = root.querySelector("[data-admission-form]");
		wireImport(root);
		form.addEventListener("submit", function (event) {
			event.preventDefault();
			save(root);
		});
		var payButton = root.querySelector("[data-admission-pay]");
		if (payButton) payButton.addEventListener("click", function () { startPayment(root); });
	}

	function showPaymentAction(root) {
		var section = root.querySelector("[data-admission-payment]");
		if (section) section.hidden = false;
	}

	function paymentState(root, value) {
		var section = root.querySelector("[data-admission-payment]");
		if (section) section.setAttribute("data-payment-state", value);
	}

	function showPaymentSuccess(root, result) {
		paymentState(root, "success");
		var link = root.querySelector("[data-admission-learning-link]");
		if (link) {
			link.hidden = false;
			link.href = result.learning_url || "/app/elms-learning";
		}
		status(root, "Оплата подтверждена сервером. Зачисление активно.", "is-success");
	}

	function startPayment(root) {
		var button = root.querySelector("[data-admission-pay]");
		var course = selectedCourse(root);
		var batch = selectedBatch(root);
		if (!course || !batch || state.loading) {
			status(root, "Выберите доступный курс и поток перед оплатой.", "is-error");
			return;
		}
		state.loading = true;
		button.disabled = true;
		paymentState(root, "waiting");
		status(root, "Создаём платёж…", "is-pending");
		call("elms.admission.api.create_payment", { course: course, batch: batch }, function (result, error) {
			state.loading = false;
			button.disabled = false;
			if (error || !result) {
				paymentState(root, "error");
				status(root, errorText(error), "is-error");
				return;
			}
			state.payment = result;
			if (result.status === "paid" || result.enrollment) return showPaymentSuccess(root, result);
			var session = result.provider_session || {};
			var paymentStatus = root.querySelector("[data-admission-payment-status]");
			if (paymentStatus) paymentStatus.textContent = "Ожидаем подтверждение оплаты";
			status(root, "Платёж создан. Завершите оплату в платёжном сервисе — зачисление появится после webhook.", "is-pending");
			if (session.payment_url) window.open(session.payment_url, "_blank", "noopener");
			pollPayment(root);
		});
	}

	function pollPayment(root) {
		if (!state.payment || !state.payment.name) return;
		window.setTimeout(function () {
			call("elms.admission.api.get_payment_status", { payment: state.payment.name }, function (result, error) {
				if (error || !result) return pollPayment(root);
				state.payment = result;
				if (result.status === "paid" && result.enrollment) return showPaymentSuccess(root, result);
				pollPayment(root);
			});
		}, 3000);
	}

	function save(root) {
		var button = root.querySelector("[data-admission-submit]");
		if (state.loading) return;
		if (!selectedBatch(root)) {
			status(root, "Выберите курс и поток перед сохранением.", "is-error");
			return;
		}
		state.loading = true;
		button.disabled = true;
		status(root, "Проверяем поля и загружаем документы…", "is-pending");
		formPayload(root).then(function (payload) {
			return new Promise(function (resolve, reject) {
				call("elms.admission.api.save_profile", { payload: JSON.stringify(payload) }, function (result, error) {
					if (error || !result) reject(error || new Error("Пустой ответ сервера"));
					else resolve(result);
				});
			});
		}).then(function (result) {
			state.profile = { exists: true, profile: result };
			showPaymentAction(root);
			status(root, "Анкета сохранена. Документы приняты в приватное хранилище.", "is-success");
		}).catch(function (error) {
			status(root, errorText(error), "is-error");
		}).then(function () {
			state.loading = false;
			button.disabled = false;
		});
	}

	function load(root) {
		status(root, "Загружаем доступные потоки…", "is-pending");
		call("elms.lms.api.get_course_catalog", {}, function (catalog, catalogError) {
			if (catalogError) return status(root, errorText(catalogError), "is-error");
			state.catalog = catalog.courses || [];
			call("elms.admission.api.get_profile", {}, function (profile, profileError) {
				if (profileError) return status(root, errorText(profileError), "is-error");
				state.profile = profile;
				render(root);
				status(root, profile.exists ? "Профиль загружен. Проверьте документы перед сохранением." : "Профиль ещё не заполнен.", profile.exists ? "is-success" : "");
			});
		});
	}

	window.elmsAdmissionPage = function (wrapper) {
		var page = frappe.ui.make_app_page({ parent: wrapper, title: "Поступление", single_column: true });
		$(wrapper).addClass("elms-admission-page-wrapper");
		state.root = page.main[0];
		render(state.root);
		load(state.root);
	};
})();

(function () {
	"use strict";

	var state = { root: null, catalog: [], profile: null, loading: false };

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
		var options = catalog.map(function (course) {
			return '<option value="' + esc(course.batch) + '">' + esc(course.course_name || "Курс") + " — " + esc(course.batch_name || course.batch) + "</option>";
		}).join("");
		root.innerHTML = [
			'<div class="elms-admission-shell">',
			'<header class="elms-admission-header"><div><div class="elms-admission-kicker">ПОСТУПЛЕНИЕ / 01</div><h1>Анкета слушателя</h1><p>Заполните профиль и приложите документы. Оплата откроется после проверки анкеты.</p></div><span class="elms-admission-badge">LearnerProfile</span></header>',
			'<div class="elms-admission-route" aria-label="Порядок поступления"><span class="is-active">01 Анкета</span><span>02 Документы</span><span>03 Оплата</span></div>',
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
			'<div class="elms-admission-actions"><button type="submit" class="elms-admission-button is-primary" data-admission-submit>Сохранить анкету</button><span>После сохранения станет доступен следующий шаг — оплата.</span></div>',
			'</form></div>',
		].join("");
		var consent = root.querySelector("[name='consent_version']");
		if (consent && profile.consent_version) consent.checked = true;
		var form = root.querySelector("[data-admission-form]");
		form.addEventListener("submit", function (event) {
			event.preventDefault();
			save(root);
		});
	}

	function save(root) {
		var button = root.querySelector("[data-admission-submit]");
		if (state.loading) return;
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

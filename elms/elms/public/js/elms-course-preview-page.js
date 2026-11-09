(function () {
	"use strict";

	var state = { root: null, courses: [], structure: null, lesson: null };

	function esc(value) {
		return String(value === null || value === undefined ? "" : value)
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
			callback: function (response) { callback(response && response.message); },
			error: function () { callback(null); }
		});
	}

	function flattenLessons(structure) {
		var lessons = [];
		(structure && structure.chapters || []).forEach(function (chapter) {
			(chapter.lessons || []).forEach(function (lesson) { lessons.push(lesson); });
		});
		return lessons;
	}

	function renderError(message) {
		var pane = state.root && state.root.querySelector("#elms-course-preview-content");
		if (pane) pane.innerHTML = '<div class="elms-empty-state"><h3>Предпросмотр недоступен</h3><p>' + esc(message) + '</p></div>';
	}

	function renderContent() {
		var pane = state.root && state.root.querySelector("#elms-course-preview-content");
		if (!pane) return;
		if (!state.structure) {
			var cards = state.courses.map(function (course) {
				return '<button class="elms-preview-course-card" data-preview-course="' + esc(course.name) + '"><span class="elms-course-batch">' + esc(course.category || "Курс") + '</span><strong>' + esc(course.course_name || "Курс без названия") + '</strong><span>' + esc(course.short_description || course.description || "Материалы курса") + '</span><small>' + esc(course.academic_hours || 0) + ' акад. ч. · ' + (Number(course.is_published) ? "Опубликован" : "Черновик") + '</small></button>';
			}).join("");
			pane.innerHTML = '<div class="elms-section-intro"><div><div class="elms-kicker">КОНТРОЛЬ ПУБЛИКАЦИИ</div><h2>Выберите курс</h2><p>Откройте курс и проверьте содержание в том же формате, который увидит слушатель.</p></div><span class="elms-count-badge">' + state.courses.length + ' курсов</span></div><div class="elms-preview-course-grid">' + (cards || '<div class="elms-empty-state"><h3>Курсов пока нет</h3><p>Сначала создайте курс и добавьте уроки.</p></div>') + '</div>';
			pane.querySelectorAll("[data-preview-course]").forEach(function (button) {
				button.addEventListener("click", function () {
					call("elms.lms.api.get_course_structure", { course: button.getAttribute("data-preview-course") }, function (structure) {
						if (!structure) return;
						state.structure = structure;
						state.lesson = null;
						renderContent();
					});
				});
			});
			return;
		}

		var lessons = flattenLessons(state.structure);
		var selected = lessons.filter(function (lesson) { return lesson.name === state.lesson; })[0] || lessons[0];
		state.lesson = selected && selected.name;
		var lessonLinks = lessons.map(function (lesson, index) {
			return '<button class="elms-preview-lesson-item ' + (lesson.name === state.lesson ? 'active' : '') + '" data-preview-lesson="' + esc(lesson.name) + '">' + (index + 1) + '. ' + esc(lesson.lesson_name) + '<small>' + esc(lesson.duration_minutes || 0) + ' мин</small></button>';
		}).join("");
		var body = selected && selected.body ? selected.body : '<p class="elms-muted">Материал урока пока не добавлен.</p>';
		var material = selected && selected.video_url ? '<a class="elms-material-link" href="' + esc(selected.video_url) + '" target="_blank" rel="noopener">Открыть видеоматериал ↗</a>' : '';
		pane.innerHTML = '<div class="elms-preview-toolbar"><button class="elms-link-btn" id="elms-preview-courses">← Все курсы</button><span class="elms-status-pill ' + (Number(state.structure.course.is_published) ? 'success' : 'warning') + '">' + (Number(state.structure.course.is_published) ? 'Опубликован' : 'Черновик') + '</span></div><div class="elms-preview-layout"><aside class="elms-preview-outline"><div class="elms-sidebar-title">Содержание курса</div>' + (lessonLinks || '<p class="elms-muted">Уроки не добавлены.</p>') + '</aside><article class="elms-preview-main"><div class="elms-kicker">' + esc(state.structure.course.category || "Учебный курс") + '</div><h2>' + esc(state.structure.course.course_name || "Курс без названия") + '</h2><p class="elms-preview-description">' + esc(state.structure.course.short_description || state.structure.course.description || "") + '</p>' + (selected ? '<div class="elms-kicker">УРОК ' + esc(selected.sequence_id || "") + '</div><h3>' + esc(selected.lesson_name) + '</h3><div class="elms-lesson-body">' + body + '</div>' + material : '<div class="elms-empty-state"><h3>Программа ещё не заполнена</h3><p>Добавьте разделы и уроки, чтобы проверить курс.</p></div>') + '</article></div>';
		var allCourses = pane.querySelector("#elms-preview-courses");
		if (allCourses) allCourses.addEventListener("click", function () { state.structure = null; state.lesson = null; renderContent(); });
		pane.querySelectorAll("[data-preview-lesson]").forEach(function (button) {
			button.addEventListener("click", function () { state.lesson = button.getAttribute("data-preview-lesson"); renderContent(); });
		});
	}

	function loadData() {
		call("elms.lms.api.get_course_preview_catalog", {}, function (result) {
			if (!result) {
				renderError("Предпросмотр доступен только методистам, инструкторам и администраторам.");
				return;
			}
			state.courses = result.courses || [];
			renderContent();
		});
	}

	function render(wrapper) {
		var page = frappe.ui.make_app_page({ parent: wrapper, title: "Предпросмотр курсов", single_column: true });
		$(wrapper).addClass("elms-course-preview-page-wrapper");
		state.root = page.main[0];
		state.structure = null;
		state.lesson = null;
		state.root.innerHTML = '<div class="elms-learning-shell elms-course-preview-shell"><div class="elms-learning-header"><div><h1 class="elms-learning-title"><span>elms</span><span class="elms-learning-badge">Предпросмотр курса</span></h1><div class="elms-learning-subtitle">Проверьте материал глазами обычного слушателя до публикации.</div></div><button class="elms-btn-secondary" id="elms-preview-back">← Кабинет обучения</button></div><div id="elms-course-preview-content"></div></div>';
		state.root.querySelector("#elms-preview-back").addEventListener("click", function () { frappe.set_route("elms-learning"); });
		loadData();
	}

	frappe.pages["elms-course-preview"] = frappe.pages["elms-course-preview"] || {};
	frappe.pages["elms-course-preview"].on_page_load = render;
})();

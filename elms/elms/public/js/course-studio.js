(function () {
	"use strict";

	var state = {
		root: null,
		course: null,
		chapters: [],
		quizzes: [],
		selected: { type: "course", id: null },
		deletedChapters: [],
		deletedLessons: [],
		dirty: false,
		saving: false
	};

	var categories = [
		"Охрана труда (ПП РФ № 2464)",
		"Промышленная безопасность (Ростехнадзор)",
		"Повышение квалификации (ДПО)",
		"Профессиональная переподготовка",
		"Корпоративный курс",
		"Электробезопасность"
	];

	function esc(value) {
		return String(value === null || value === undefined ? "" : value)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;")
			.replace(/'/g, "&#039;");
	}

	function routeCourse() {
		var route = frappe.get_route ? frappe.get_route() : [];
		return route && route[1] ? route[1] : null;
	}

	function localId(prefix) {
		return "new-" + prefix + "-" + Date.now().toString(36) + "-" + Math.floor(Math.random() * 1000);
	}

	function call(method, args, callback) {
		frappe.call({
			method: method,
			args: args || {},
			callback: function (response) {
				if (response && response.message) callback(response.message);
			},
			error: function (error) {
				var message = error && error.message ? error.message : "Не удалось выполнить операцию";
				if (frappe.msgprint) frappe.msgprint(message);
				callback(null);
			}
		});
	}

	function makeCourse(course) {
		return Object.assign({
			name: "",
			course_name: "",
			course_code: "",
			category: "Корпоративный курс",
			academic_hours: 40,
			is_published: 0,
			passing_percentage: 80,
			short_description: "",
			description: ""
		}, course || {});
	}

	function prepareData(data) {
		state.course = makeCourse(data && data.course);
		state.chapters = (data && data.chapters || []).map(function (chapter) {
			return Object.assign({ lessons: [] }, chapter, {
				lessons: (chapter.lessons || []).map(function (lesson) {
					return Object.assign({
						lesson_name: "",
						content_type: "Article",
						duration_minutes: 15,
						minimum_time_seconds: 180,
						is_mandatory: 1,
						video_url: "",
						body: "",
						quiz: ""
					}, lesson);
				})
			});
		});
		state.quizzes = data && data.quizzes || [];
		state.deletedChapters = [];
		state.deletedLessons = [];
		state.dirty = false;
		if (!state.selected.id || !findSelected()) state.selected = { type: "course", id: null };
	}

	function findChapter(id) {
		return state.chapters.filter(function (chapter) { return chapter.name === id; })[0] || null;
	}

	function findLesson(id) {
		var found = null;
		state.chapters.some(function (chapter) {
			return (chapter.lessons || []).some(function (lesson) {
				if (lesson.name === id) { found = lesson; return true; }
				return false;
			});
		});
		return found;
	}

	function findSelected() {
		if (state.selected.type === "course") return state.course;
		if (state.selected.type === "chapter") return findChapter(state.selected.id);
		return findLesson(state.selected.id);
	}

	function isNew(record) {
		return !record || !record.name || String(record.name).indexOf("new-") === 0;
	}

	function markDirty() {
		state.dirty = true;
		var status = state.root && state.root.querySelector("[data-studio-status]");
		if (status) {
			status.textContent = "Есть несохранённые изменения";
			status.classList.add("is-dirty");
			status.classList.remove("is-published");
		}
	}

	function render() {
		if (!state.root) return;
		state.root.innerHTML = [
			'<div class="elms-course-studio">',
				'<header class="elms-course-studio-header">',
					'<div class="elms-course-studio-heading"><div class="elms-kicker">МЕТОДИЧЕСКИЙ КОНТУР</div><h1>Конструктор курса</h1><p>Соберите структуру и материалы в одном рабочем пространстве.</p></div>',
					'<div class="elms-course-studio-actions"><span data-studio-status class="elms-course-studio-status">' + (Number(state.course.is_published) ? "Опубликован" : "Черновик") + '</span><button class="elms-course-studio-button" data-action="back">Назад</button><button class="elms-course-studio-button" data-action="preview">Предпросмотр</button><button class="elms-course-studio-button is-primary" data-action="save">Сохранить черновик</button></div>',
				'</header>',
				'<div class="elms-course-studio-toolbar"><div class="elms-course-studio-muted">' + esc(state.course.course_name || "Новый курс") + '</div><div class="elms-course-studio-actions"><button class="elms-course-studio-button" data-action="add-chapter">+ Раздел</button><button class="elms-course-studio-button" data-action="add-lesson">+ Урок</button></div></div>',
				'<div class="elms-course-studio-grid">',
					'<aside class="elms-course-studio-panel elms-course-studio-outline"><h3>Структура курса</h3><div data-studio-outline></div></aside>',
					'<main class="elms-course-studio-editor" data-studio-editor></main>',
					'<aside class="elms-course-studio-panel elms-course-studio-properties"><h3>Правила прохождения</h3><div class="elms-course-studio-description">Порядок, обязательность и длительность уроков сохраняются вместе с курсом. Слушатель увидит эту структуру в учебном плеере.</div><div class="elms-course-studio-empty">Выберите раздел или урок, чтобы изменить его свойства.</div></aside>',
				'</div>',
			'</div>'
		].join("");
		renderOutline();
		renderEditor();
		bindActions();
	}

	function renderOutline() {
		var target = state.root.querySelector("[data-studio-outline]");
		var chapterHtml = state.chapters.map(function (chapter, chapterIndex) {
			var lessonHtml = (chapter.lessons || []).map(function (lesson, lessonIndex) {
				return '<li><div class="elms-course-studio-item elms-course-studio-lesson-item ' + (state.selected.type === "lesson" && state.selected.id === lesson.name ? "is-selected" : "") + '"><button class="elms-course-studio-item" data-select-type="lesson" data-select-id="' + esc(lesson.name) + '"><span>' + esc(lesson.lesson_name || "Новый урок") + '</span><span>' + esc(lesson.content_type || "Article") + '</span></button><span class="elms-course-studio-mini-actions"><button class="elms-course-studio-button" title="Выше" data-move="lesson-up" data-chapter-id="' + esc(chapter.name) + '" data-item-id="' + esc(lesson.name) + '"' + (lessonIndex === 0 ? " disabled" : "") + '>↑</button><button class="elms-course-studio-button" title="Ниже" data-move="lesson-down" data-chapter-id="' + esc(chapter.name) + '" data-item-id="' + esc(lesson.name) + '"' + (lessonIndex === chapter.lessons.length - 1 ? " disabled" : "") + '>↓</button></span></div></li>';
			}).join("");
			return '<li><div class="elms-course-studio-item ' + (state.selected.type === "chapter" && state.selected.id === chapter.name ? "is-selected" : "") + '"><button class="elms-course-studio-item" data-select-type="chapter" data-select-id="' + esc(chapter.name) + '"><span>' + esc(chapter.chapter_name || "Новый раздел") + '</span><span>' + (chapter.lessons || []).length + '</span></button><span class="elms-course-studio-mini-actions"><button class="elms-course-studio-button" title="Выше" data-move="chapter-up" data-item-id="' + esc(chapter.name) + '"' + (chapterIndex === 0 ? " disabled" : "") + '>↑</button><button class="elms-course-studio-button" title="Ниже" data-move="chapter-down" data-item-id="' + esc(chapter.name) + '"' + (chapterIndex === state.chapters.length - 1 ? " disabled" : "") + '>↓</button></span></div><ul class="elms-course-studio-lessons">' + lessonHtml + '</ul></li>';
		}).join("");
		target.innerHTML = '<ul class="elms-course-studio-tree"><li><button class="elms-course-studio-item ' + (state.selected.type === "course" ? "is-selected" : "") + '" data-select-type="course"><span>' + esc(state.course.course_name || "Новый курс") + '</span><span>Курс</span></button></li>' + (chapterHtml || '<li class="elms-course-studio-empty">Разделов пока нет. Добавьте первый раздел.</li>') + '</ul>';
	}

	function input(name, label, value, type) {
		type = type || "text";
		return '<label>' + label + '<input type="' + type + '" data-field="' + name + '" value="' + esc(value) + '"></label>';
	}

	function select(name, label, value, options) {
		return '<label>' + label + '<select data-field="' + name + '">' + options.map(function (option) { return '<option value="' + esc(option) + '"' + (option === value ? " selected" : "") + '>' + esc(option) + '</option>'; }).join("") + '</select></label>';
	}

	function renderEditor() {
		var target = state.root.querySelector("[data-studio-editor]");
		var selected = findSelected();
		if (state.selected.type === "course") {
			target.innerHTML = '<div class="elms-kicker">КАРТОЧКА КУРСА</div><h2>Основные сведения</h2><div class="elms-course-studio-form">' + input("course_name", "Название курса", state.course.course_name) + '<div class="elms-course-studio-field-row">' + input("course_code", "Код курса", state.course.course_code) + input("academic_hours", "Академические часы", state.course.academic_hours, "number") + '</div>' + select("category", "Категория", state.course.category, categories) + '<label>Короткое описание<textarea data-field="short_description">' + esc(state.course.short_description) + '</textarea></label><label>Цели и программа<textarea data-field="description">' + esc(state.course.description) + '</textarea></label><label class="elms-course-studio-check"><input type="checkbox" data-field="is_published"' + (Number(state.course.is_published) ? " checked" : "") + '> Опубликовать курс</label></div>';
			bindEditorFields(state.course);
			return;
		}
		if (!selected) {
			target.innerHTML = '<div class="elms-course-studio-empty">Выберите элемент структуры.</div>';
			return;
		}
		if (state.selected.type === "chapter") {
			target.innerHTML = '<div class="elms-kicker">РАЗДЕЛ КУРСА</div><h2>Содержание раздела</h2><div class="elms-course-studio-form">' + input("chapter_name", "Название раздела", selected.chapter_name) + '<label>Описание<textarea data-field="chapter_description">' + esc(selected.description || "") + '</textarea></label><button class="elms-course-studio-button is-danger" data-action="remove-selected">Удалить раздел</button></div>';
			bindEditorFields(selected);
			return;
		}
		var quizOptions = ['<option value="">Без теста</option>'].concat(state.quizzes.map(function (quiz) { return '<option value="' + esc(quiz.name) + '"' + (quiz.name === selected.quiz ? " selected" : "") + '>' + esc(quiz.quiz_name || quiz.name) + '</option>'; })).join("");
		target.innerHTML = '<div class="elms-kicker">УРОК</div><h2>Материал урока</h2><div class="elms-course-studio-form">' + input("lesson_name", "Название урока", selected.lesson_name) + '<div class="elms-course-studio-field-row">' + select("content_type", "Тип материала", selected.content_type, ["Article", "Video", "Quiz"]) + input("duration_minutes", "Длительность, мин", selected.duration_minutes, "number") + '</div><div class="elms-course-studio-field-row">' + input("minimum_time_seconds", "Минимальное время, сек", selected.minimum_time_seconds, "number") + '<label class="elms-course-studio-check"><input type="checkbox" data-field="is_mandatory"' + (Number(selected.is_mandatory) ? " checked" : "") + '> Обязательный урок</label></div><label>Видео или ссылка на материал<input type="url" data-field="video_url" value="' + esc(selected.video_url || "") + '"></label><label>Связанный тест<select data-field="quiz">' + quizOptions + '</select></label><label>Содержание<textarea data-field="body">' + esc(selected.body || "") + '</textarea></label><button class="elms-course-studio-button is-danger" data-action="remove-selected">Удалить урок</button></div>';
		bindEditorFields(selected);
	}

	function bindEditorFields(record) {
		state.root.querySelectorAll("[data-field]").forEach(function (field) {
			field.addEventListener("input", function () { updateField(record, field); });
			field.addEventListener("change", function () { updateField(record, field); });
		});
	}

	function updateField(record, field) {
		var key = field.getAttribute("data-field");
		var value = field.type === "checkbox" ? (field.checked ? 1 : 0) : field.value;
		if (state.selected.type === "course") record[key] = value;
		else if (state.selected.type === "chapter") record[key === "chapter_description" ? "description" : key] = value;
		else record[key] = value;
		markDirty();
		if (key === "course_name") {
			var courseTitle = state.root.querySelector('[data-studio-outline] [data-select-type="course"] span');
			var toolbarTitle = state.root.querySelector(".elms-course-studio-muted");
			var title = state.course.course_name || "Новый курс";
			if (courseTitle) courseTitle.textContent = title;
			if (toolbarTitle) toolbarTitle.textContent = title;
		}
	}

	function selectItem(type, id) {
		state.selected = { type: type, id: id || null };
		render();
	}

	function addChapter() {
		var chapter = { name: localId("chapter"), chapter_name: "Новый раздел", description: "", lessons: [] };
		state.chapters.push(chapter);
		state.selected = { type: "chapter", id: chapter.name };
		markDirty();
		render();
	}

	function addLesson() {
		var chapter = state.selected.type === "chapter" ? findChapter(state.selected.id) : state.chapters[state.chapters.length - 1];
		if (!chapter) { addChapter(); chapter = state.chapters[state.chapters.length - 1]; }
		var lesson = { name: localId("lesson"), lesson_name: "Новый урок", content_type: "Article", duration_minutes: 15, minimum_time_seconds: 180, is_mandatory: 1, video_url: "", body: "", quiz: "" };
		chapter.lessons = chapter.lessons || [];
		chapter.lessons.push(lesson);
		state.selected = { type: "lesson", id: lesson.name };
		markDirty();
		render();
	}

	function moveItem(direction, chapterId, itemId) {
		var collection = chapterId ? (findChapter(chapterId) || {}).lessons : state.chapters;
		if (!collection) return;
		var index = collection.findIndex(function (item) { return item.name === itemId; });
		var next = index + direction;
		if (index < 0 || next < 0 || next >= collection.length) return;
		var item = collection.splice(index, 1)[0];
		collection.splice(next, 0, item);
		markDirty();
		render();
	}

	function removeSelected() {
		if (state.selected.type === "course") return;
		var selectedId = state.selected.id;
		if (!window.confirm || window.confirm("Удалить этот элемент из курса?")) {
			if (state.selected.type === "chapter") {
				var chapterIndex = state.chapters.findIndex(function (chapter) { return chapter.name === selectedId; });
				var chapter = chapterIndex >= 0 ? state.chapters[chapterIndex] : null;
				if (chapter && !isNew(chapter)) state.deletedChapters.push(chapter.name);
				(chapter && chapter.lessons || []).forEach(function (lesson) { if (!isNew(lesson)) state.deletedLessons.push(lesson.name); });
				if (chapterIndex >= 0) state.chapters.splice(chapterIndex, 1);
			} else {
				state.chapters.forEach(function (chapter) {
					var lessonIndex = (chapter.lessons || []).findIndex(function (lesson) { return lesson.name === selectedId; });
					if (lessonIndex >= 0) {
						if (!isNew(chapter.lessons[lessonIndex])) state.deletedLessons.push(chapter.lessons[lessonIndex].name);
						chapter.lessons.splice(lessonIndex, 1);
					}
				});
			}
			state.selected = { type: "course", id: null };
			markDirty();
			render();
		}
	}

	function serialize() {
		return {
			course: state.course,
			chapters: state.chapters.map(function (chapter) {
				return {
					name: isNew(chapter) ? null : chapter.name,
					chapter_name: chapter.chapter_name,
					description: chapter.description || "",
					lessons: (chapter.lessons || []).map(function (lesson) {
						return Object.assign({}, lesson, { name: isNew(lesson) ? null : lesson.name });
					})
				};
			}),
			deleted_chapters: state.deletedChapters,
			deleted_lessons: state.deletedLessons
		};
	}

	function save() {
		if (state.saving) return;
		if (!String(state.course.course_name || "").trim()) {
			frappe.msgprint("Укажите название курса");
			return;
		}
		state.saving = true;
		call("elms.lms.api.save_course_draft", { payload: JSON.stringify(serialize()) }, function (result) {
			state.saving = false;
			if (!result) return;
			prepareData(result);
			frappe.show_alert({ message: Number(state.course.is_published) ? "Курс опубликован" : "Черновик сохранён", indicator: "green" });
			render();
			if (state.course.name && frappe.set_route) frappe.set_route("elms-course-studio", state.course.name);
		});
	}

	function bindActions() {
		state.root.querySelectorAll("[data-action]").forEach(function (button) {
			button.addEventListener("click", function () {
				var action = button.getAttribute("data-action");
				if (action === "back") frappe.set_route("elms-learning");
				if (action === "preview") frappe.set_route("elms-course-preview");
				if (action === "save") save();
				if (action === "add-chapter") addChapter();
				if (action === "add-lesson") addLesson();
				if (action === "remove-selected") removeSelected();
			});
		});
		state.root.querySelectorAll("[data-select-type]").forEach(function (button) {
			button.addEventListener("click", function () { selectItem(button.getAttribute("data-select-type"), button.getAttribute("data-select-id")); });
		});
		state.root.querySelectorAll("[data-move]").forEach(function (button) {
			button.addEventListener("click", function () {
				var move = button.getAttribute("data-move");
				moveItem(move.indexOf("up") >= 0 ? -1 : 1, button.getAttribute("data-chapter-id"), button.getAttribute("data-item-id"));
			});
		});
	}

	function load() {
		call("elms.lms.api.get_course_editor_data", { course: routeCourse() }, function (data) {
			if (!data) return;
			prepareData(data);
			render();
		});
	}

	window.elmsCourseStudio = function (wrapper) {
		var page = frappe.ui.make_app_page({ parent: wrapper, title: "Конструктор курсов", single_column: true });
		$(wrapper).addClass("elms-course-studio-page-wrapper");
		state.root = page.main[0];
		state.selected = { type: "course", id: null };
		load();
	};
})();

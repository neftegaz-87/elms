(function () {
	"use strict";

	var state = {
		root: null,
		course: null,
		chapters: [],
		quizzes: [],
		categories: [],
		selected: { type: "course", id: null },
		deletedChapters: [],
		deletedLessons: [],
		dirty: false,
		saving: false
	};

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

	function categoryOptions() {
		var values = state.categories.slice();
		var current = state.course && state.course.category;
		if (current && values.indexOf(current) < 0) values.unshift(current);
		return values;
	}

	function defaultQuizDraft(lessonName) {
		return {
			name: null,
			quiz_name: lessonName || "Новый тест",
			quiz_type: "Practice",
			passing_percentage: 80,
			time_limit_minutes: 20,
			max_attempts: 0,
			is_published: 1,
			instructions: "Выберите один или несколько вариантов. Результат проверяется сервером.",
			questions: [defaultQuestion(1)],
			deleted_questions: []
		};
	}

	function defaultQuestion(sequence) {
		return {
			name: localId("question"),
			question_text: "",
			question_type: "Single Choice",
			points: 1,
			topic: "Общие вопросы",
			explanation: "",
			options: [
				{ id: "A", text: "", correct: true },
				{ id: "B", text: "", correct: false }
			],
			_local: true,
			_sequence: sequence || 1
		};
	}

	function trueFalseOptions() {
		return [
			{ id: "A", text: "Верно", correct: true },
			{ id: "B", text: "Неверно", correct: false }
		];
	}

	function normalizeQuizDraft(draft, lessonName) {
		var base = defaultQuizDraft(lessonName);
		if (!draft || typeof draft !== "object") return base;
		var questions = (draft.questions || []).map(function (question, index) {
			var options = (question.options || []).map(function (option, optionIndex) {
				return {
					id: option.id || String.fromCharCode(65 + optionIndex),
					text: option.text || "",
					correct: Boolean(option.correct)
				};
			});
			if (!options.length) options = defaultQuestion(1).options;
			return {
				name: question.name || localId("question"),
				question_text: question.question_text || "",
				question_type: question.question_type || "Single Choice",
				points: question.points || 1,
				topic: question.topic || "Общие вопросы",
				explanation: question.explanation || "",
				options: options,
				_local: !question.name || String(question.name).indexOf("new-") === 0,
				_sequence: index + 1
			};
		});
		if (!questions.length) questions = [defaultQuestion(1)];
		return {
			name: draft.name || null,
			quiz_name: draft.quiz_name || lessonName || base.quiz_name,
			quiz_type: draft.quiz_type || "Practice",
			passing_percentage: draft.passing_percentage == null ? 80 : draft.passing_percentage,
			time_limit_minutes: draft.time_limit_minutes == null ? 20 : draft.time_limit_minutes,
			max_attempts: draft.max_attempts == null ? 0 : draft.max_attempts,
			is_published: draft.is_published == null ? 1 : draft.is_published,
			instructions: draft.instructions || base.instructions,
			questions: questions,
			deleted_questions: (draft.deleted_questions || []).slice()
		};
	}

	function ensureLessonQuizDraft(lesson) {
		if (!lesson) return;
		if (lesson.content_type === "Quiz") {
			lesson.quiz_draft = normalizeQuizDraft(lesson.quiz_draft, lesson.lesson_name);
		}
	}

	function prepareData(data) {
		state.course = makeCourse(data && data.course);
		state.chapters = (data && data.chapters || []).map(function (chapter) {
			return Object.assign({ lessons: [] }, chapter, {
				lessons: (chapter.lessons || []).map(function (lesson) {
					var prepared = Object.assign({
						lesson_name: "",
						content_type: "Article",
						duration_minutes: 15,
						minimum_time_seconds: 180,
						is_mandatory: 1,
						video_url: "",
						body: "",
						quiz: "",
						quiz_draft: null
					}, lesson);
					ensureLessonQuizDraft(prepared);
					return prepared;
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
					'<aside class="elms-course-studio-panel elms-course-studio-properties" data-studio-properties></aside>',
				'</div>',
			'</div>'
		].join("");
		renderOutline();
		renderEditor();
		renderProperties();
		bindActions();
	}

	function renderProperties() {
		var target = state.root.querySelector("[data-studio-properties]");
		if (!target) return;
		var selected = findSelected();
		if (state.selected.type === "lesson" && selected && selected.content_type === "Quiz" && selected.quiz_draft) {
			var draft = selected.quiz_draft;
			var counts = { "Single Choice": 0, "Multiple Choice": 0, "True/False": 0 };
			(draft.questions || []).forEach(function (question) {
				if (counts[question.question_type] != null) counts[question.question_type] += 1;
			});
			var modeLabel = draft.quiz_type === "Assessment" ? "Аттестация" : "Тренировка";
			target.innerHTML = '<h3>Правила теста</h3><div class="elms-course-studio-description">Режим: <b>' + esc(modeLabel) + '</b>. Проходной балл ' + esc(draft.passing_percentage) + '%. Попыток: ' + (Number(draft.max_attempts) ? esc(draft.max_attempts) : "без лимита") + '.</div><ul class="elms-course-studio-prop-list"><li>Один из списка — ' + counts["Single Choice"] + '</li><li>Несколько из списка — ' + counts["Multiple Choice"] + '</li><li>Верно / Неверно — ' + counts["True/False"] + '</li></ul>';
			return;
		}
		target.innerHTML = '<h3>Правила прохождения</h3><div class="elms-course-studio-description">Порядок, обязательность и длительность уроков сохраняются вместе с курсом. Слушатель увидит эту структуру в учебном плеере.</div><div class="elms-course-studio-empty">Выберите раздел или урок, чтобы изменить его свойства.</div>';
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

	function flagSelect(name, label, value, onLabel, offLabel, attr) {
		attr = attr || "data-field";
		var current = Number(value) ? "1" : "0";
		return '<label>' + label + '<select ' + attr + '="' + name + '"><option value="1"' + (current === "1" ? " selected" : "") + '>' + esc(onLabel) + '</option><option value="0"' + (current === "0" ? " selected" : "") + '>' + esc(offLabel) + '</option></select></label>';
	}

	function renderEditor() {
		var target = state.root.querySelector("[data-studio-editor]");
		var selected = findSelected();
		if (state.selected.type === "course") {
			target.innerHTML = '<div class="elms-kicker">КАРТОЧКА КУРСА</div><h2>Основные сведения</h2><div class="elms-course-studio-form">' + input("course_name", "Название курса", state.course.course_name) + '<div class="elms-course-studio-field-row">' + input("course_code", "Код курса", state.course.course_code) + input("academic_hours", "Академические часы", state.course.academic_hours, "number") + '</div>' + select("category", "Категория", state.course.category, categoryOptions()) + '<button type="button" class="elms-course-studio-button elms-course-studio-category-button" data-action="category-new">+ Добавить категорию</button><label>Короткое описание<textarea data-field="short_description">' + esc(state.course.short_description) + '</textarea></label><label>Цели и программа<textarea data-field="description">' + esc(state.course.description) + '</textarea></label>' + flagSelect("is_published", "Статус курса", state.course.is_published, "Опубликован", "Черновик") + '</div>';
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
		ensureLessonQuizDraft(selected);
		var quizEditor = selected.content_type === "Quiz" ? renderQuizEditor(selected) : "";
		var materialFields = selected.content_type === "Quiz"
			? ""
			: '<label>Видео или ссылка на материал<input type="url" data-field="video_url" value="' + esc(selected.video_url || "") + '"></label><label>Содержание<textarea data-field="body">' + esc(selected.body || "") + '</textarea></label>';
		target.innerHTML = '<div class="elms-kicker">УРОК</div><h2>Материал урока</h2><div class="elms-course-studio-form">' + input("lesson_name", "Название урока", selected.lesson_name) + '<div class="elms-course-studio-field-row">' + select("content_type", "Тип материала", selected.content_type, ["Article", "Video", "Quiz"]) + input("duration_minutes", "Длительность, мин", selected.duration_minutes, "number") + '</div><div class="elms-course-studio-field-row">' + input("minimum_time_seconds", "Минимальное время, сек", selected.minimum_time_seconds, "number") + flagSelect("is_mandatory", "Обязательность", selected.is_mandatory, "Обязательный", "Необязательный") + '</div>' + materialFields + quizEditor + '<button class="elms-course-studio-button is-danger" data-action="remove-selected">Удалить урок</button></div>';
		bindEditorFields(selected);
		if (selected.content_type === "Quiz") bindQuizEditor(selected);
	}

	function optionLabel(option, index) {
		var letter = String.fromCharCode(65 + index);
		var text = String(option.text || "").trim();
		return text ? letter + " — " + text : letter + " — (пустой вариант)";
	}

	function renderCorrectSelect(question) {
		var multi = question.question_type === "Multiple Choice";
		var options = question.options || [];
		var selectOptions = options.map(function (option, index) {
			return '<option value="' + index + '"' + (option.correct ? " selected" : "") + ">" + esc(optionLabel(option, index)) + "</option>";
		}).join("");
		if (multi) {
			return '<label class="elms-course-studio-correct-select"><span class="elms-course-studio-field-note">Удерживайте Ctrl / ⌘, чтобы выбрать несколько</span><select multiple size="' + Math.min(Math.max(options.length, 2), 6) + '" data-correct-select="1">' + selectOptions + "</select></label>";
		}
		var selected = options.findIndex(function (option) { return option.correct; });
		if (selected < 0) selected = 0;
		var singleOptions = options.map(function (option, index) {
			return '<option value="' + index + '"' + (index === selected ? " selected" : "") + ">" + esc(optionLabel(option, index)) + "</option>";
		}).join("");
		return '<div class="elms-course-studio-correct-select"><select data-correct-select="1">' + singleOptions + "</select></div>";
	}

	function renderQuizEditor(lesson) {
		ensureLessonQuizDraft(lesson);
		var draft = lesson.quiz_draft;
		if (!draft) return "";
		var questionHtml = (draft.questions || []).map(function (question, index) {
			return renderQuestionCard(question, index);
		}).join("");
		return [
			'<section class="elms-course-studio-quiz">',
				'<div class="elms-course-studio-quiz-block">',
					'<div class="elms-course-studio-quiz-block-title">Параметры теста</div>',
					'<div class="elms-course-studio-quiz-settings">',
						'<label class="elms-course-studio-span-2">Название<input type="text" data-quiz-field="quiz_name" value="' + esc(draft.quiz_name) + '"></label>',
						'<label>Режим<select data-quiz-field="quiz_type"><option value="Practice"' + (draft.quiz_type === "Practice" ? " selected" : "") + '>Тренировка</option><option value="Assessment"' + (draft.quiz_type === "Assessment" ? " selected" : "") + '>Аттестация</option></select></label>',
						'<label>Проходной балл, %<input type="number" min="0" max="100" data-quiz-field="passing_percentage" value="' + esc(draft.passing_percentage) + '"></label>',
						'<label>Время, мин<input type="number" min="0" data-quiz-field="time_limit_minutes" value="' + esc(draft.time_limit_minutes) + '"></label>',
						'<label>Попытки <span class="elms-course-studio-field-note">0 = без лимита</span><input type="number" min="0" data-quiz-field="max_attempts" value="' + esc(draft.max_attempts) + '"></label>',
					'</div>',
					flagSelect("is_published", "Доступность теста", draft.is_published, "Опубликован — доступен слушателю", "Черновик — скрыт от слушателя", "data-quiz-field"),
				'</div>',
				'<div class="elms-course-studio-quiz-block">',
					'<div class="elms-course-studio-quiz-block-title">Инструкция для слушателя</div>',
					'<textarea class="elms-course-studio-textarea-sm" data-quiz-field="instructions" placeholder="Что увидит слушатель перед стартом">' + esc(draft.instructions || "") + '</textarea>',
				'</div>',
				'<div class="elms-course-studio-quiz-block">',
					'<div class="elms-course-studio-quiz-block-title">Вопросы <span>' + (draft.questions || []).length + '</span></div>',
					'<div class="elms-course-studio-quiz-questions">' + (questionHtml || '<div class="elms-course-studio-empty">Пока нет вопросов</div>') + '</div>',
					'<button type="button" class="elms-course-studio-button is-primary elms-course-studio-btn-block" data-quiz-action="add-question">Добавить вопрос</button>',
				'</div>',
			'</section>'
		].join("");
	}

	function renderQuestionCard(question, index) {
		var trueFalse = question.question_type === "True/False";
		var canRemoveOption = !trueFalse && (question.options || []).length > 2;
		var optionsHtml = (question.options || []).map(function (option, optionIndex) {
			var letter = String.fromCharCode(65 + optionIndex);
			var removeBtn = canRemoveOption
				? '<button type="button" class="elms-course-studio-icon-btn" title="Удалить вариант" aria-label="Удалить вариант" data-quiz-action="remove-option" data-option-index="' + optionIndex + '">×</button>'
				: '<span class="elms-course-studio-icon-btn is-spacer" aria-hidden="true"></span>';
			if (trueFalse) {
				return '<div class="elms-course-studio-option-row is-locked" data-option-index="' + optionIndex + '"><span class="elms-course-studio-choice-letter">' + letter + '</span><span class="elms-course-studio-option-locked">' + esc(option.text || "") + '</span></div>';
			}
			return [
				'<div class="elms-course-studio-option-row" data-option-index="' + optionIndex + '">',
					'<span class="elms-course-studio-choice-letter">' + letter + '</span>',
					'<input type="text" class="elms-course-studio-option-text" data-question-option-text="' + optionIndex + '" value="' + esc(option.text || "") + '" placeholder="Текст варианта">',
					removeBtn,
				'</div>'
			].join("");
		}).join("");
		var removeQuestion = lessonQuestionCount() > 1
			? '<button type="button" class="elms-course-studio-button is-danger is-ghost" data-quiz-action="remove-question">Удалить вопрос</button>'
			: "";
		var addOption = trueFalse
			? ""
			: '<button type="button" class="elms-course-studio-button elms-course-studio-btn-block" data-quiz-action="add-option">Добавить вариант ответа</button>';
		return [
			'<article class="elms-course-studio-question" data-question-id="' + esc(question.name) + '">',
				'<div class="elms-course-studio-question-head"><strong>Вопрос ' + (index + 1) + '</strong>' + removeQuestion + '</div>',
				'<div class="elms-course-studio-q-section"><div class="elms-course-studio-q-label">Текст</div><textarea class="elms-course-studio-question-text" data-question-field="question_text" placeholder="Сформулируйте вопрос">' + esc(question.question_text || "") + '</textarea></div>',
				'<div class="elms-course-studio-q-section"><div class="elms-course-studio-q-label">Настройки</div><div class="elms-course-studio-question-meta"><label>Тип ответа<select data-question-field="question_type"><option value="Single Choice"' + (question.question_type === "Single Choice" ? " selected" : "") + '>Один ответ</option><option value="Multiple Choice"' + (question.question_type === "Multiple Choice" ? " selected" : "") + '>Несколько ответов</option><option value="True/False"' + (question.question_type === "True/False" ? " selected" : "") + '>Верно / Неверно</option></select></label><label>Баллы<input type="number" min="1" data-question-field="points" value="' + esc(question.points || 1) + '"></label></div></div>',
				'<div class="elms-course-studio-q-section"><div class="elms-course-studio-q-label">Варианты</div><div class="elms-course-studio-options">' + optionsHtml + '</div>' + addOption + '</div>',
				'<div class="elms-course-studio-q-section is-correct"><div class="elms-course-studio-q-label">' + (question.question_type === "Multiple Choice" ? "Правильные ответы" : "Правильный ответ") + '</div>' + renderCorrectSelect(question) + '</div>',
				'<div class="elms-course-studio-q-section"><div class="elms-course-studio-q-label">Пояснение <span class="elms-course-studio-field-note">только для тренировки</span></div><textarea class="elms-course-studio-textarea-sm" data-question-field="explanation" placeholder="Необязательно">' + esc(question.explanation || "") + '</textarea></div>',
			'</article>'
		].join("");
	}

	function lessonQuestionCount() {
		var selected = findSelected();
		return selected && selected.quiz_draft && selected.quiz_draft.questions ? selected.quiz_draft.questions.length : 0;
	}

	function bindEditorFields(record) {
		state.root.querySelectorAll("[data-field]").forEach(function (field) {
			field.addEventListener("input", function () { updateField(record, field); });
			field.addEventListener("change", function () { updateField(record, field); });
		});
	}

	function coerceFlag(key, value) {
		if (key === "is_published" || key === "is_mandatory") return Number(value) ? 1 : 0;
		return value;
	}

	function updateField(record, field) {
		var key = field.getAttribute("data-field");
		var value = coerceFlag(key, field.type === "checkbox" ? (field.checked ? 1 : 0) : field.value);
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
		if (key === "is_published" && state.selected.type === "course") render();
		if (state.selected.type === "lesson" && key === "content_type") {
			if (value === "Quiz") ensureLessonQuizDraft(record);
			else record.quiz_draft = null;
			render();
			return;
		}
		if (state.selected.type === "lesson" && key === "lesson_name" && record.content_type === "Quiz" && record.quiz_draft && !record.quiz_draft.name) {
			record.quiz_draft.quiz_name = value || record.quiz_draft.quiz_name;
		}
	}

	function findQuestion(lesson, questionId) {
		if (!lesson || !lesson.quiz_draft) return null;
		return (lesson.quiz_draft.questions || []).filter(function (question) { return question.name === questionId; })[0] || null;
	}

	function bindQuizEditor(lesson) {
		state.root.querySelectorAll("[data-quiz-field]").forEach(function (field) {
			field.addEventListener("input", function () { updateQuizField(lesson, field); });
			field.addEventListener("change", function () { updateQuizField(lesson, field); });
		});
		state.root.querySelectorAll("[data-quiz-action]").forEach(function (button) {
			button.addEventListener("click", function () {
				var action = button.getAttribute("data-quiz-action");
				var card = button.closest("[data-question-id]");
				var questionId = card ? card.getAttribute("data-question-id") : null;
				var optionIndex = button.getAttribute("data-option-index");
				if (action === "add-question") {
					lesson.quiz_draft.questions.push(defaultQuestion(lesson.quiz_draft.questions.length + 1));
					markDirty();
					render();
					return;
				}
				var question = findQuestion(lesson, questionId);
				if (!question) return;
				if (action === "remove-question") {
					if (lesson.quiz_draft.questions.length <= 1) return;
					if (!question._local && question.name) lesson.quiz_draft.deleted_questions.push(question.name);
					lesson.quiz_draft.questions = lesson.quiz_draft.questions.filter(function (item) { return item.name !== question.name; });
					markDirty();
					render();
					return;
				}
				if (action === "add-option") {
					if (question.question_type === "True/False") return;
					question.options.push({ id: String.fromCharCode(65 + question.options.length), text: "", correct: false });
					markDirty();
					render();
					return;
				}
				if (action === "remove-option") {
					var removeAt = Number(optionIndex);
					if (question.question_type === "True/False" || question.options.length <= 2 || isNaN(removeAt)) return;
					question.options.splice(removeAt, 1);
					question.options.forEach(function (option, index) { option.id = String.fromCharCode(65 + index); });
					if (!question.options.some(function (option) { return option.correct; }) && question.options[0]) question.options[0].correct = true;
					markDirty();
					render();
				}
			});
		});
		state.root.querySelectorAll("[data-question-id]").forEach(function (card) {
			var question = findQuestion(lesson, card.getAttribute("data-question-id"));
			if (!question) return;
			card.querySelectorAll("[data-question-field]").forEach(function (field) {
				field.addEventListener("input", function () { updateQuestionField(lesson, question, field); });
				field.addEventListener("change", function () { updateQuestionField(lesson, question, field); });
			});
			card.querySelectorAll("[data-question-option-text]").forEach(function (field) {
				field.addEventListener("input", function () {
					var index = Number(field.getAttribute("data-question-option-text"));
					if (!question.options[index]) return;
					question.options[index].text = field.value;
					refreshCorrectSelectLabels(card, question);
					markDirty();
				});
			});
			card.querySelectorAll("[data-correct-select]").forEach(function (field) {
				field.addEventListener("change", function () {
					applyCorrectSelect(question, field);
					markDirty();
				});
			});
		});
	}

	function refreshCorrectSelectLabels(card, question) {
		var select = card.querySelector("[data-correct-select]");
		if (!select) return;
		Array.prototype.forEach.call(select.options, function (optionEl, index) {
			if (!question.options[index]) return;
			optionEl.textContent = optionLabel(question.options[index], index);
		});
	}

	function applyCorrectSelect(question, field) {
		if (field.multiple) {
			var selected = {};
			Array.prototype.forEach.call(field.selectedOptions, function (optionEl) {
				selected[Number(optionEl.value)] = true;
			});
			question.options.forEach(function (option, index) {
				option.correct = Boolean(selected[index]);
			});
			if (!question.options.some(function (option) { return option.correct; }) && question.options[0]) {
				question.options[0].correct = true;
				if (field.options[0]) field.options[0].selected = true;
			}
			return;
		}
		var index = Number(field.value);
		question.options.forEach(function (option, optionIndex) {
			option.correct = optionIndex === index;
		});
	}

	function updateQuizField(lesson, field) {
		if (!lesson.quiz_draft) return;
		var key = field.getAttribute("data-quiz-field");
		lesson.quiz_draft[key] = coerceFlag(key, field.type === "checkbox" ? (field.checked ? 1 : 0) : field.value);
		markDirty();
	}

	function updateQuestionField(lesson, question, field) {
		var key = field.getAttribute("data-question-field");
		var value = field.value;
		if (key === "points") value = Number(value) || 1;
		if (key === "question_type" && value !== question.question_type) {
			question.question_type = value;
			if (value === "True/False") question.options = trueFalseOptions();
			else if (question.options.length < 2) question.options = defaultQuestion(1).options;
			else if (value !== "Multiple Choice") {
				var firstCorrect = question.options.findIndex(function (option) { return option.correct; });
				question.options.forEach(function (option, index) { option.correct = index === (firstCorrect >= 0 ? firstCorrect : 0); });
			}
			markDirty();
			render();
			return;
		}
		question[key] = value;
		markDirty();
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
		var lesson = { name: localId("lesson"), lesson_name: "Новый урок", content_type: "Article", duration_minutes: 15, minimum_time_seconds: 180, is_mandatory: 1, video_url: "", body: "", quiz: "", quiz_draft: null };
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

	function serializeQuizDraft(draft) {
		if (!draft) return null;
		return {
			name: draft.name && String(draft.name).indexOf("new-") !== 0 ? draft.name : null,
			quiz_name: draft.quiz_name,
			quiz_type: draft.quiz_type,
			passing_percentage: Number(draft.passing_percentage) || 0,
			time_limit_minutes: Number(draft.time_limit_minutes) || 0,
			max_attempts: Number(draft.max_attempts) || 0,
			is_published: Number(draft.is_published) ? 1 : 0,
			instructions: draft.instructions || "",
			questions: (draft.questions || []).map(function (question) {
				return {
					name: question._local || String(question.name || "").indexOf("new-") === 0 ? null : question.name,
					question_text: question.question_text,
					question_type: question.question_type,
					points: Number(question.points) || 1,
					topic: question.topic || "Общие вопросы",
					explanation: question.explanation || "",
					options: (question.options || []).map(function (option, index) {
						return {
							id: option.id || String.fromCharCode(65 + index),
							text: option.text || "",
							correct: Boolean(option.correct)
						};
					})
				};
			}),
			deleted_questions: (draft.deleted_questions || []).slice()
		};
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
						var payload = {
							name: isNew(lesson) ? null : lesson.name,
							lesson_name: lesson.lesson_name,
							content_type: lesson.content_type,
							duration_minutes: lesson.duration_minutes,
							minimum_time_seconds: lesson.minimum_time_seconds,
							is_mandatory: lesson.is_mandatory,
							video_url: lesson.video_url || "",
							body: lesson.body || ""
						};
						if (lesson.content_type === "Quiz") payload.quiz_draft = serializeQuizDraft(lesson.quiz_draft);
						return payload;
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
				if (action === "category-new") openCategoryForm();
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

	function openCategoryForm() {
		if (!frappe.set_route) return;
		frappe.set_route("Form", "ELMS Course Category", "new-elms-course-category");
	}

	function load() {
		state.root.innerHTML = '<div class="elms-course-studio-loading">Загрузка курса и структуры…</div>';
		var pending = { categories: null, editor: null };
		function showError() {
			state.root.innerHTML = '<div class="elms-course-studio-loading is-error"><h2>Не удалось загрузить курс</h2><p>Обновите страницу. Если ошибка повторится, проверьте доступ к курсу и структуру данных.</p><button class="elms-course-studio-button is-primary" data-action="reload">Повторить</button></div>';
			var retry = state.root.querySelector('[data-action="reload"]');
			if (retry) retry.addEventListener("click", load);
		}
		function finish() {
			if (pending.categories === null || pending.editor === null) return;
			if (!pending.categories || !pending.editor) {
				showError();
				return;
			}
			prepareData(pending.editor);
			render();
		}
		call("elms.lms.api.get_course_categories", {}, function (data) {
			pending.categories = Boolean(data);
			if (data) state.categories = (data.categories || []).map(function (category) { return category.category_name || category.name; }).filter(Boolean);
			finish();
		});
		call("elms.lms.api.get_course_editor_data", { course: routeCourse() }, function (data) {
			pending.editor = data || false;
			finish();
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

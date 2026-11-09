(function () {
	"use strict";

	var pageName = "elms-learning";
	var pageLabel = "Кабинет обучения";
	var state = {
		activeTab: "courses",
		root: null,
		timerInterval: null,
		heartbeatInterval: null,
		timeSpent: 0,
		pendingTimeSpent: 0,
		savingProgress: false,
		isPaused: false,
		currentEnrollment: null,
		currentLesson: null,
		currentStructure: null,
		quiz: null,
		quizAttempt: null,
		courses: [],
		catalog: [],
		programs: [],
		programDetail: null,
		relationshipGroups: [],
		relationshipSearch: "",
		relationshipType: "",
		activities: [],
		admin: { can_manage: false, courses: [], batches: [], subscriptions: [], enrollments: [], quizzes: [], programs: [], users: [] }
	};

	function esc(value) {
		return String(value === null || value === undefined ? "" : value)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;")
			.replace(/'/g, "&#039;");
	}

	function formatTime(seconds) {
		var mins = Math.floor((Number(seconds) || 0) / 60);
		var secs = (Number(seconds) || 0) % 60;
		return (mins < 10 ? "0" : "") + mins + ":" + (secs < 10 ? "0" : "") + secs;
	}

	function call(method, args, callback) {
		if (!window.frappe || !frappe.call) return;
		frappe.call({
			method: method,
			args: args || {},
			callback: function (response) {
				if (response && response.message) callback(response.message);
			},
			error: function () {
				if (callback) callback(null);
			}
		});
	}

	function registerPage() {
		if (!window.frappe || !frappe.container || !frappe.ui) return;
		frappe.provide("frappe.standard_pages");
		if (frappe.standard_pages[pageName]) return;

		frappe.standard_pages[pageName] = function () {
			var wrapper = frappe.container.add_page(pageName);
			var page = frappe.ui.make_app_page({
				parent: wrapper,
				title: pageLabel,
				single_column: true
			});

			$(wrapper).addClass("elms-learning-page-wrapper");
			state.root = page.main[0];
			renderLayout(state.root);
			loadData();
			startTimer();
			bindAntiCheat();
		};
	}

	window.elmsLearningPage = function (wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: pageLabel,
			single_column: true
		});

		$(wrapper).addClass("elms-learning-page-wrapper");
		state.root = page.main[0];
		renderLayout(state.root);
		loadData();
		startTimer();
		bindAntiCheat();
	};

	function loadData() {
		call("elms.lms.api.get_learner_dashboard", {}, function (dashboard) {
			if (!dashboard) return;
			state.courses = dashboard.courses || [];
			state.activities = dashboard.activities || [];
			if (!state.currentEnrollment && state.courses.length) state.currentEnrollment = state.courses[0].enrollment;
			renderAll();
		});
		call("elms.lms.api.get_learning_admin_data", {}, function (admin) {
			if (!admin) return;
			state.admin = admin;
			if (state.admin.can_manage) {
				var managerTab = state.root && state.root.querySelector(".elms-manager-tab");
				if (managerTab) managerTab.hidden = false;
			}
				renderAll();
			});
		call("elms.lms.api.get_learning_relationships", {}, function (relationships) {
			if (!relationships) return;
			state.relationshipGroups = relationships.groups || [];
			renderAll();
		});
		call("elms.lms.api.get_course_catalog", {}, function (catalog) {
			if (!catalog) return;
			state.catalog = catalog.courses || [];
			renderAll();
		});
		call("elms.lms.api.get_program_catalog", {}, function (programs) {
			if (!programs) return;
			state.programs = programs.programs || [];
			renderAll();
		});
	}

	function renderLayout(container) {
		container.innerHTML = [
			'<div class="elms-learning-shell">',
			'  <div class="elms-learning-header"><div><h1 class="elms-learning-title"><span>elms</span><span class="elms-learning-badge">Обучение</span></h1><div class="elms-learning-subtitle">Курсы, потоки, зачисления, прогресс и контроль освоения в одном рабочем месте</div></div><button class="elms-btn-secondary" id="elms-refresh-btn">Обновить данные</button></div>',
				'  <div class="elms-learning-tabs"><button class="elms-tab-btn active" data-tab="courses">Мои курсы</button><button class="elms-tab-btn" data-tab="catalog">Каталог курсов</button><button class="elms-tab-btn" data-tab="programs">Программы</button><button class="elms-tab-btn" data-tab="player">Учебный плеер</button><button class="elms-tab-btn" data-tab="progress">Прогресс и аттестация</button><button class="elms-tab-btn" data-tab="activity">Журнал активности</button><button class="elms-tab-btn elms-manager-tab" data-tab="manage" hidden>Управление обучением</button></div>',
				'  <div id="elms-tab-courses" class="elms-tab-pane active"></div><div id="elms-tab-catalog" class="elms-tab-pane"></div><div id="elms-tab-programs" class="elms-tab-pane"></div><div id="elms-tab-player" class="elms-tab-pane"></div><div id="elms-tab-progress" class="elms-tab-pane"></div><div id="elms-tab-activity" class="elms-tab-pane"></div><div id="elms-tab-manage" class="elms-tab-pane"></div>',
			'</div>'
		].join("");

		container.querySelectorAll(".elms-tab-btn").forEach(function (button) {
			button.addEventListener("click", function () { switchTab(button.getAttribute("data-tab")); });
		});
		var refresh = container.querySelector("#elms-refresh-btn");
		if (refresh) refresh.addEventListener("click", loadData);
		renderAll();
	}

	function renderAll() {
		if (!state.root) return;
		renderCoursesTab();
		renderCatalogTab();
		renderProgramsTab();
		renderPlayerTab();
		renderProgressTab();
		renderActivityTab();
		renderManageTab();
	}

	function switchTab(target) {
		state.activeTab = target;
		if (!state.root) return;
		state.root.querySelectorAll(".elms-tab-btn").forEach(function (button) {
			button.classList.toggle("active", button.getAttribute("data-tab") === target);
		});
		state.root.querySelectorAll(".elms-tab-pane").forEach(function (pane) {
			pane.classList.toggle("active", pane.id === "elms-tab-" + target);
		});
	}

	function renderCoursesTab() {
		var pane = state.root && state.root.querySelector("#elms-tab-courses");
		if (!pane) return;
		if (!state.courses.length) {
			pane.innerHTML = '<div class="elms-empty-state"><div class="elms-empty-icon">🎓</div><h3>Зачислений пока нет</h3><p>Откройте каталог и выберите активный курс. После записи он появится здесь автоматически.</p><button class="elms-btn-action" data-action="open-catalog">Открыть каталог курсов</button></div>';
			bindActions(pane);
			return;
		}
		var modeNote = state.admin.can_manage ? '' : '<div class="elms-role-note">Режим слушателя: создавать и редактировать программы могут пользователи с ролью ELMS Admin или ELMS Operations User.</div>';
		pane.innerHTML = '<div class="elms-section-intro"><div><div class="elms-kicker">ЛИЧНЫЙ КАБИНЕТ</div><h2>Мои программы обучения</h2><p>Выберите курс, чтобы продолжить обучение с последнего сохранённого урока.</p>' + modeNote + '</div><span class="elms-count-badge">' + state.courses.length + ' активн.</span></div><div class="elms-cards-grid">' + state.courses.map(courseCard).join("") + '</div>';
		pane.querySelectorAll(".elms-open-player-btn").forEach(function (button) {
			button.addEventListener("click", function () { openPlayer(button.getAttribute("data-enr")); });
		});
	}

	function renderCatalogTab() {
		var pane = state.root && state.root.querySelector("#elms-tab-catalog");
		if (!pane) return;
		var cards = state.catalog.map(catalogCard).join("");
		pane.innerHTML = '<div class="elms-section-intro"><div><div class="elms-kicker">ОТКРЫТЫЙ КАТАЛОГ</div><h2>Курсы по нефтегазовой отрасли</h2><p>Выберите активный поток и запишитесь самостоятельно. Материалы в демо-каталоге предназначены для проверки сценария обучения.</p></div><span class="elms-count-badge">' + state.catalog.length + ' доступн.</span></div><div class="elms-catalog-grid">' + (cards || '<div class="elms-empty-state"><h3>Активных курсов пока нет</h3><p>Методист ещё не открыл поток для записи.</p></div>') + '</div>';
		pane.querySelectorAll(".elms-catalog-enroll-btn").forEach(function (button) {
			button.addEventListener("click", function () { enrollInCatalog(button.getAttribute("data-batch")); });
		});
		bindActions(pane);
	}

	function catalogCard(course) {
		var enrolled = Boolean(course.enrollment);
		return ['<article class="elms-catalog-card"><div class="elms-course-batch">' + esc(course.category || "Нефтегаз") + '</div><h3>' + esc(course.course_name || "Курс без названия") + '</h3><p>' + esc(course.short_description || "Учебная программа ELMS") + '</p><div class="elms-catalog-meta"><span>' + esc(course.academic_hours || 0) + ' акад. ч.</span><span>' + esc(course.batch_name) + '</span></div>', enrolled ? '<span class="elms-status-pill success">Вы уже записаны</span><button class="elms-btn-secondary" data-action="open-catalog-course" data-enr="' + esc(course.enrollment) + '">Открыть обучение →</button>' : '<button class="elms-btn-action elms-catalog-enroll-btn" data-batch="' + esc(course.batch) + '">Записаться на курс</button>', '</article>'].join("");
	}

	function renderProgramsTab() {
		var pane = state.root && state.root.querySelector("#elms-tab-programs");
		if (!pane) return;
		if (state.programDetail) {
			renderProgramDetail(pane);
			return;
		}
		var cards = state.programs.map(function (program) {
			var enrolled = Boolean(program.program_enrollment);
			return '<article class="elms-program-card"><div class="elms-course-batch">' + esc(program.category || "Учебная программа") + '</div><h3>' + esc(program.program_name) + '</h3><p>' + esc(program.description || "Последовательный путь обучения ELMS") + '</p><div class="elms-catalog-meta"><span>' + esc(program.total_hours || 0) + ' акад. ч.</span><span>' + esc(program.course_count || 0) + ' курса</span></div><button class="elms-btn-action" data-action="program-open" data-program="' + esc(program.name) + '" data-enrollment="' + esc(program.program_enrollment || '') + '">' + (enrolled ? "Продолжить программу" : "Начать программу") + '</button></article>';
		}).join("");
		pane.innerHTML = '<div class="elms-section-intro"><div><div class="elms-kicker">LEARNING PATHS</div><h2>Программы обучения</h2><p>Программа объединяет несколько курсов в последовательный маршрут и считает общий прогресс.</p></div><span class="elms-count-badge">' + state.programs.length + ' доступн.</span></div><div class="elms-program-grid">' + (cards || '<div class="elms-empty-state"><h3>Программ пока нет</h3></div>') + '</div>';
		bindActions(pane);
	}

	function renderProgramDetail(pane) {
		var detail = state.programDetail;
		var progress = detail.progress;
		var courses = progress ? progress.courses : [];
		var rows = courses.map(function (course) {
			var done = Number(course.progress_percentage) >= 100;
			var action = course.enrollment ? '<button class="elms-btn-secondary" data-action="program-open-course" data-enr="' + esc(course.enrollment) + '">Открыть курс</button>' : '<button class="elms-btn-action" data-action="program-course-enroll" data-program-enrollment="' + esc(progress.program_enrollment) + '" data-course="' + esc(course.course) + '">Открыть курс</button>';
			return '<div class="elms-program-course-row"><div><span class="elms-course-batch">' + esc(course.sequence_id) + '. КУРС</span><h3>' + esc(course.course_name) + '</h3><div class="elms-progress-bar-container"><div class="elms-progress-bar-fill" style="width:' + Math.max(0, Math.min(100, Number(course.progress_percentage) || 0)) + '%"></div></div><span class="elms-muted">' + esc(course.progress_percentage || 0) + '% · ' + (done ? "завершён" : "в процессе") + '</span></div><div>' + action + '</div></div>';
		}).join("");
		pane.innerHTML = '<div class="elms-section-intro"><div><button class="elms-link-btn" data-action="program-back">← Все программы</button><div class="elms-kicker">LEARNING PATH</div><h2>' + esc(detail.program.program_name) + '</h2><p>' + esc(detail.program.description || "") + '</p></div><span class="elms-count-badge">' + esc(progress ? progress.progress_percentage : 0) + '%</span></div><div class="elms-program-course-list">' + (rows || '<div class="elms-empty-state">Курсы не добавлены.</div>') + '</div>';
		bindActions(pane);
	}

	function openProgram(program, enrollment) {
		call("elms.lms.api.get_program_detail", { program: program, program_enrollment: enrollment || null }, function (detail) {
			if (!detail) return;
			state.programDetail = detail;
			switchTab("programs");
			renderProgramsTab();
		});
	}

	function enrollInProgram(program) {
		call("elms.lms.api.enroll_program", { program: program }, function (detail) {
			if (!detail) return;
			frappe.show_alert({ message: "Вы записаны на программу", indicator: "green" });
			loadData();
			openProgram(program, detail.program_enrollment);
		});
	}

	function enrollProgramCourse(programEnrollment, course) {
		call("elms.lms.api.enroll_program_course", { program_enrollment: programEnrollment, course: course }, function () {
			frappe.show_alert({ message: "Курс открыт", indicator: "green" });
			loadData();
			openProgram(state.programDetail.program.name, programEnrollment);
		});
	}

	function enrollInCatalog(batch) {
		call("elms.lms.api.enroll_self", { batch: batch }, function (result) {
			if (!result) return;
			frappe.show_alert({ message: "Вы записаны на курс", indicator: "green" });
			state.activeTab = "courses";
			loadData();
			switchTab("courses");
		});
	}

	function courseCard(course) {
		var percentage = Number(course.progress_percentage) || 0;
		var eligible = Number(course.exam_eligible) === 1;
		return ['<div class="elms-course-card">', '<div class="elms-course-header"><div class="elms-course-batch">' + esc(course.batch_name || course.batch) + '</div><div class="elms-course-title">' + esc(course.course_name || "Курс без названия") + '</div><div class="elms-progress-bar-container"><div class="elms-progress-bar-fill" style="width:' + Math.max(0, Math.min(100, percentage)) + '%"></div></div><div class="elms-progress-meta"><span>Уроки: <b>' + esc(course.completed_lessons) + '/' + esc(course.total_lessons) + '</b></span><span>Прогресс: <b>' + esc(percentage) + '%</b></span></div></div>', '<div><div class="elms-status-row"><span class="elms-status-pill ' + (eligible ? 'success' : 'warning') + '">' + (eligible ? 'Допуск к аттестации открыт' : 'Обучение продолжается') + '</span></div><button class="elms-btn-action elms-open-player-btn" data-enr="' + esc(course.enrollment) + '">Открыть обучение →</button></div></div>'].join("");
	}

	function openPlayer(enrollment) {
		var course = state.courses.filter(function (item) { return item.enrollment === enrollment; })[0];
		state.currentEnrollment = enrollment;
		state.currentLesson = null;
		state.currentStructure = null;
		state.quiz = null;
		state.quizAttempt = null;
		switchTab("player");
		if (!course || !course.course) { renderPlayerTab(); return; }
		call("elms.lms.api.get_course_structure", { course: course.course, enrollment: enrollment }, function (structure) {
			if (!structure) return;
			state.currentStructure = structure;
			var lessons = flattenLessons(structure);
			var next = lessons.filter(function (lesson) { return !(lesson.progress && Number(lesson.progress.is_completed)); })[0] || lessons[0];
			state.currentLesson = next && next.name;
			state.timeSpent = next && next.progress ? Number(next.progress.time_spent_seconds) || 0 : 0;
			state.pendingTimeSpent = 0;
			renderPlayerTab();
		});
	}

	function flattenLessons(structure) {
		var result = [];
		(structure && structure.chapters || []).forEach(function (chapter) { (chapter.lessons || []).forEach(function (lesson) { result.push(lesson); }); });
		return result;
	}

	function renderPlayerTab() {
		var pane = state.root && state.root.querySelector("#elms-tab-player");
		if (!pane) return;
		if (!state.currentStructure) { pane.innerHTML = '<div class="elms-empty-state"><div class="elms-empty-icon">▶</div><h3>Выберите курс</h3><p>Откройте курс на вкладке «Мои курсы», чтобы загрузить его программу и начать обучение.</p></div>'; return; }
		var lessons = flattenLessons(state.currentStructure);
		if (!lessons.length) { pane.innerHTML = '<div class="elms-empty-state"><h3>Программа ещё не заполнена</h3><p>Методист должен добавить разделы и уроки курса.</p></div>'; return; }
		var selected = lessons.filter(function (lesson) { return lesson.name === state.currentLesson; })[0] || lessons[0];
		state.currentLesson = selected.name;
		var sidebar = lessons.map(function (lesson, index) {
			var done = lesson.progress && Number(lesson.progress.is_completed);
			return '<li class="elms-lesson-item ' + (lesson.name === selected.name ? 'active ' : '') + (done ? 'completed' : '') + '" data-lesson="' + esc(lesson.name) + '"><span>' + (done ? '✓ ' : (index + 1) + '. ') + esc(lesson.lesson_name) + '</span><span class="elms-lesson-duration">' + esc(lesson.duration_minutes || 0) + ' мин</span></li>';
		}).join("");
		var body = selected.body || '<p class="elms-muted">Материал урока пока не добавлен.</p>';
		var material = selected.video_url ? '<a class="elms-material-link" href="' + esc(selected.video_url) + '" target="_blank" rel="noopener">Открыть видеоматериал ↗</a>' : '';
		var quizPane = selected.content_type === "Quiz" ? '<div id="elms-quiz-pane" class="elms-quiz-pane"></div>' : '';
		var completeButton = selected.content_type === "Quiz" ? '' : '<button id="elms-complete-lesson-btn" class="elms-btn-action">Завершить урок</button>';
		pane.innerHTML = ['<div class="elms-player-container"><aside class="elms-player-sidebar"><div class="elms-sidebar-title">Программа курса</div><ul class="elms-lessons-list">' + sidebar + '</ul></aside>', '<main class="elms-player-main"><div class="elms-player-telemetry-bar"><div class="elms-telemetry-status"><div id="elms-pulse-indicator" class="elms-pulse-dot"></div><span id="elms-telemetry-label">Телеметрия активна · время фиксируется только при активном окне</span></div><span class="elms-timer-value" id="elms-study-timer">' + formatTime(state.timeSpent) + '</span></div>', '<article class="elms-player-content"><div class="elms-kicker">' + esc(selected.content_type || "Материал") + '</div><h2>' + esc(selected.lesson_name) + '</h2><div class="elms-lesson-body">' + body + '</div>' + material + quizPane + '<div class="elms-player-note"><b>Как засчитывается урок:</b> система сохраняет активное время и факт завершения. Переключение вкладки приостанавливает таймер.</div></article><div class="elms-player-footer"><span>Зачисление: <code>' + esc(state.currentEnrollment) + '</code></span>' + completeButton + '</div></main></div>'].join("");
		pane.querySelectorAll(".elms-lesson-item").forEach(function (item) {
			item.addEventListener("click", function () {
				state.currentLesson = item.getAttribute("data-lesson");
				var selectedProgress = lessons.filter(function (lesson) { return lesson.name === state.currentLesson; })[0];
				state.timeSpent = selectedProgress && selectedProgress.progress ? Number(selectedProgress.progress.time_spent_seconds) || 0 : 0;
				state.pendingTimeSpent = 0;
				renderPlayerTab();
			});
		});
		var complete = pane.querySelector("#elms-complete-lesson-btn");
		if (complete) complete.addEventListener("click", function () { sendLessonProgress(Math.min(300, state.pendingTimeSpent), true); });
		if (selected.content_type === "Quiz") renderQuizPane(pane, selected);
	}

	function renderQuizPane(pane, lesson) {
		var quizPane = pane.querySelector("#elms-quiz-pane");
		if (!quizPane) return;
		if (!state.quizAttempt) {
			quizPane.innerHTML = '<div class="elms-quiz-intro"><b>Контроль знаний</b><p>Результат проверяется сервером. Для прохождения теста нажмите кнопку ниже.</p><button id="elms-start-quiz-btn" class="elms-btn-action">Начать тест</button></div>';
			var start = quizPane.querySelector("#elms-start-quiz-btn");
			if (start) start.addEventListener("click", function () { startQuiz(lesson.name); });
			return;
		}
		var questions = state.quizAttempt.questions || [];
		var cards = questions.map(function (question, index) {
			var inputType = question.question_type === "Multiple Choice" ? "checkbox" : "radio";
			var options = (question.options || []).map(function (option) {
				return '<label class="elms-quiz-option"><input type="' + inputType + '" name="quiz-' + esc(question.name) + '" data-question="' + esc(question.name) + '" value="' + esc(option.id) + '"><span>' + esc(option.text) + '</span></label>';
			}).join("");
			return '<fieldset class="elms-quiz-question"><legend>' + (index + 1) + '. ' + esc(question.question_text) + '</legend><div class="elms-quiz-options">' + options + '</div></fieldset>';
		}).join("");
		quizPane.innerHTML = '<form id="elms-quiz-form"><div class="elms-quiz-meta">Проходной балл: <b>' + esc(state.quizAttempt.passing_percentage) + '%</b></div>' + cards + '<button class="elms-btn-action" type="submit">Отправить ответы</button></form>';
		var form = quizPane.querySelector("#elms-quiz-form");
		if (form) form.addEventListener("submit", function (event) { event.preventDefault(); submitQuiz(form); });
	}

	function startQuiz(lessonId) {
		call("elms.lms.api.get_lesson_quiz", { lesson_id: lessonId, enrollment: state.currentEnrollment }, function (quiz) {
			if (!quiz || !quiz.quiz) return;
			call("elms.lms.api.start_quiz", { quiz: quiz.quiz.name, enrollment: state.currentEnrollment }, function (attempt) {
				if (!attempt) return;
				state.quiz = quiz;
				state.quizAttempt = attempt;
				renderPlayerTab();
			});
		});
	}

	function submitQuiz(form) {
		var answers = {};
		form.querySelectorAll("input:checked").forEach(function (input) {
			var question = input.getAttribute("data-question");
			if (!answers[question]) answers[question] = [];
			answers[question].push(input.value);
		});
		call("elms.lms.api.submit_quiz", { attempt: state.quizAttempt.attempt, answers: JSON.stringify(answers) }, function (result) {
			if (!result) return;
			frappe.show_alert({ message: result.passed ? "Тест пройден" : "Тест не пройден", indicator: result.passed ? "green" : "orange" });
			state.quizAttempt = null;
			loadData();
			if (result.passed) openPlayer(state.currentEnrollment);
			else renderPlayerTab();
		});
	}

	function renderProgressTab() {
		var pane = state.root && state.root.querySelector("#elms-tab-progress");
		if (!pane) return;
		var rows = state.courses.map(function (course) { return '<tr><td><b>' + esc(course.course_name || "Курс") + '</b><div class="elms-table-subtitle">' + esc(course.batch_name || course.batch) + '</div></td><td>' + esc(course.completed_lessons) + '/' + esc(course.total_lessons) + '</td><td><b>' + esc(course.progress_percentage || 0) + '%</b></td><td><span class="elms-status-pill ' + (Number(course.exam_eligible) ? 'success' : 'warning') + '">' + (Number(course.exam_eligible) ? 'Допуск открыт' : 'Не завершено') + '</span></td></tr>'; }).join("");
		pane.innerHTML = '<div class="elms-table-container"><div class="elms-section-intro"><div><div class="elms-kicker">КОНТРОЛЬ ОСВОЕНИЯ</div><h2>Прогресс по программам</h2><p>Допуск рассчитывается сервером по обязательным урокам курса. Правила итоговой аттестации должны быть закреплены в программе и локальных документах организации.</p></div></div><table class="elms-audit-table"><thead><tr><th>Программа / поток</th><th>Уроки</th><th>Прогресс</th><th>Статус</th></tr></thead><tbody>' + (rows || '<tr><td colspan="4" class="elms-muted">Нет данных для отображения</td></tr>') + '</tbody></table></div>';
	}

	function renderActivityTab() {
		var pane = state.root && state.root.querySelector("#elms-tab-activity");
		if (!pane) return;
		var rows = state.activities.map(function (log) { return '<tr><td class="elms-mono">' + esc(log.timestamp) + '</td><td><b>' + esc(log.activity_type) + '</b></td><td>' + esc((log.reference_doctype || "") + (log.reference_name ? " · " + log.reference_name : "")) + '</td><td class="elms-mono">' + esc(log.ip_address) + '</td></tr>'; }).join("");
		pane.innerHTML = '<div class="elms-table-container"><div class="elms-section-intro"><div><div class="elms-kicker">АУДИТ УЧЕБНОГО ПРОЦЕССА</div><h2>Моя активность</h2><p>Журнал показывает сохранённые события текущего пользователя. Доступ к нему ограничен серверными правами.</p></div></div><table class="elms-audit-table"><thead><tr><th>Время</th><th>Событие</th><th>Объект</th><th>IP</th></tr></thead><tbody>' + (rows || '<tr><td colspan="4" class="elms-muted">Событий пока нет</td></tr>') + '</tbody></table></div>';
	}

	function renderManageTab() {
		var pane = state.root && state.root.querySelector("#elms-tab-manage");
		if (!pane || !state.admin.can_manage) return;
		pane.innerHTML = ['<div class="elms-section-intro"><div><div class="elms-kicker">МЕТОДИЧЕСКИЙ КОНТУР</div><h2>Управление обучением</h2><p>Ищите по названию потока, курса, урока, теста или слушателя. Результаты собраны вокруг курса и показывают все связи.</p></div><div class="elms-action-row"><button class="elms-btn-action" data-action="course-new">Создать курс</button><button class="elms-btn-secondary" data-action="program-new">Создать программу</button><button class="elms-btn-secondary" data-action="batch-new">Создать поток</button><button class="elms-btn-secondary" data-action="quiz-new">Создать тест</button><button class="elms-btn-secondary" data-action="enroll">Оформить зачисление</button></div></div>', relationshipSearchPanel(), renderRelationshipGroups(), '<div class="elms-admin-hint"><b>Поток</b> — это календарная группа слушателей одного курса с датами, куратором и организацией-заказчиком. Создайте курс, затем поток, после этого оформляйте зачисления. Программы остаются отдельным маршрутом из курсов.</div>'].join("");
		bindActions(pane);
		var search = pane.querySelector("[data-relationship-search]");
		if (search) search.addEventListener("keydown", function (event) { if (event.key === "Enter") searchRelationships(pane); });
	}

	function relationshipSearchPanel() {
		var options = [["", "Все типы"], ["course", "Курсы"], ["program", "Программы"], ["batch", "Потоки"], ["chapter", "Разделы"], ["lesson", "Уроки"], ["quiz", "Тесты"], ["enrollment", "Зачисления"], ["subscription", "Подписки"], ["user", "Слушатели"]];
		return '<section class="elms-relationship-search"><div class="elms-relationship-search-head"><div><h3>Поиск по связям</h3><p class="elms-muted">Например: Демо-поток 2026 · Стропальные работы</p></div><span class="elms-relationship-search-count">' + state.relationshipGroups.length + ' курсов в выдаче</span></div><div class="elms-relationship-search-controls"><input data-relationship-search type="search" value="' + esc(state.relationshipSearch) + '" placeholder="Курс, поток, урок, quiz, слушатель или ID"><select data-relationship-type>' + options.map(function (option) { return '<option value="' + esc(option[0]) + '"' + (option[0] === state.relationshipType ? ' selected' : '') + '>' + esc(option[1]) + '</option>'; }).join("") + '</select><button class="elms-btn-action" data-action="relationship-search">Найти</button><button class="elms-btn-secondary" data-action="relationship-clear">Сбросить</button></div></section>';
	}

	function relationshipEntityLabel(type) {
		return { course: "Курс", program: "Программа", batch: "Поток", subscription: "Подписка", enrollment: "Зачисление", chapter: "Раздел", lesson: "Урок", quiz: "Тест", user: "Слушатель" }[type] || type;
	}

	function relationshipEntityList(title, items) {
		if (!items.length) return '';
		return '<div class="elms-relationship-column"><h4>' + esc(title) + ' <span>' + items.length + '</span></h4>' + items.slice(0, 8).map(function (item) { return '<button class="elms-relationship-row" data-action="open-related" data-doctype="' + esc(item.doctype) + '" data-name="' + esc(item.name) + '"><span><b>' + esc(item.title) + '</b><small>' + esc(item.meta || item.name) + '</small></span><span class="elms-relationship-type">' + esc(relationshipEntityLabel(item.type)) + '</span></button>'; }).join("") + (items.length > 8 ? '<div class="elms-muted">Ещё ' + (items.length - 8) + '</div>' : '') + '</div>';
	}

	function relationshipOutline(outline) {
		if (!outline || !outline.length) {
			return '<section class="elms-relationship-outline"><div class="elms-relationship-outline-head"><h4>Структура курса</h4><span>Разделов пока нет</span></div><div class="elms-muted">Добавьте разделы и уроки в Course Studio.</div></section>';
		}
		return '<section class="elms-relationship-outline"><div class="elms-relationship-outline-head"><h4>Структура курса</h4><span>Курс → разделы → уроки</span></div><div class="elms-relationship-tree">' + outline.map(function (entry, chapterIndex) {
			var chapter = entry.chapter || {};
			var lessons = entry.lessons || [];
			var chapterLabel = '<span class="elms-relationship-tree-title">' + esc(chapter.title || 'Без раздела') + '</span><small>Раздел ' + (chapterIndex + 1) + ' · ' + lessons.length + ' ' + (lessons.length === 1 ? 'урок' : 'уроков') + '</small>';
			var chapterMarkup = chapter.doctype ? '<button class="elms-relationship-tree-chapter" data-action="open-related" data-doctype="' + esc(chapter.doctype) + '" data-name="' + esc(chapter.name) + '">' + chapterLabel + '</button>' : '<div class="elms-relationship-tree-chapter is-static">' + chapterLabel + '</div>';
			var lessonMarkup = lessons.length ? '<div class="elms-relationship-tree-lessons">' + lessons.map(function (lesson, lessonIndex) {
				return '<button class="elms-relationship-tree-lesson" data-action="open-related" data-doctype="' + esc(lesson.doctype) + '" data-name="' + esc(lesson.name) + '"><span><b>' + esc(lesson.title || lesson.name) + '</b><small>Урок ' + (lessonIndex + 1) + ' · ' + esc(lesson.meta || 'Без типа') + '</small></span><span class="elms-relationship-type">Урок</span></button>';
			}).join("") + '</div>' : '<div class="elms-relationship-tree-empty">Уроков нет</div>';
			return '<div class="elms-relationship-tree-chapter-group">' + chapterMarkup + lessonMarkup + '</div>';
		}).join("") + '</div></section>';
	}

	function renderRelationshipGroups() {
		if (!state.relationshipGroups.length) return '<div class="elms-empty-state elms-relationship-empty"><h3>Связей не найдено</h3><p>Измените запрос или сбросьте фильтр.</p></div>';
		return '<div class="elms-relationship-groups">' + state.relationshipGroups.map(function (group) {
			var course = group.course || {};
			var matches = (group.matches || []).map(function (item) { return '<span class="elms-relationship-match">' + esc(relationshipEntityLabel(item.type)) + ': ' + esc(item.title) + '</span>'; }).join("");
			return '<article class="elms-relationship-group"><div class="elms-relationship-root"><div><div class="elms-kicker">КУРС</div><button class="elms-relationship-course" data-action="open-related" data-doctype="ELMS Course" data-name="' + esc(course.name) + '">' + esc(course.course_name || course.name) + '</button><small>' + esc(course.course_code || course.category || course.name) + '</small></div><div class="elms-relationship-root-side"><button class="elms-btn-secondary elms-relationship-create-batch" data-action="batch-for-course" data-course="' + esc(course.name) + '">Создать поток для курса</button><div class="elms-relationship-counts"><span>' + esc(group.counts.program || 0) + ' программ</span><span>' + esc(group.counts.batch || 0) + ' потоков</span><span>' + esc(group.counts.chapter || 0) + ' раздела</span><span>' + esc(group.counts.lesson || 0) + ' уроков</span><span>' + esc(group.counts.quiz || 0) + ' тестов</span><span>' + esc(group.counts.enrollment || 0) + ' зачислений</span></div></div></div>' + (matches ? '<div class="elms-relationship-matches">Найдено: ' + matches + '</div>' : '') + '<div class="elms-relationship-context"><div class="elms-relationship-context-label">Маршрут и поток</div><div class="elms-relationship-columns">' + relationshipEntityList("Программы курса", group.programs || []) + relationshipEntityList("Потоки курса", group.batches || []) + '</div><p class="elms-relationship-help">Программа задаёт порядок курсов. Поток задаёт календарь и слушателей. Здесь показаны все программы, в состав которых входит курс этого потока.</p></div>' + relationshipOutline(group.outline || []) + '<div class="elms-relationship-columns elms-relationship-secondary"><div class="elms-relationship-secondary-group">' + relationshipEntityList("Тесты", group.quizzes || []) + relationshipEntityList("Подписки", group.subscriptions || []) + '</div><div class="elms-relationship-secondary-group">' + relationshipEntityList("Зачисления", group.enrollments || []) + '</div></div></article>';
		}).join("") + '</div>';
	}

	function searchRelationships(container) {
		var input = container.querySelector("[data-relationship-search]");
		var select = container.querySelector("[data-relationship-type]");
		state.relationshipSearch = input ? input.value : "";
		state.relationshipType = select ? select.value : "";
		call("elms.lms.api.get_learning_relationships", { search: state.relationshipSearch, entity_type: state.relationshipType }, function (result) {
			if (!result) return;
			state.relationshipGroups = result.groups || [];
			renderManageTab();
		});
	}

	function adminCard(title, subtitle, items, doctype, name, detail, status, addAction) {
		var rows = items.slice(0, 8).map(function (item) { return '<button class="elms-admin-list-row" data-action="open" data-doctype="' + esc(doctype) + '" data-name="' + esc(item.name) + '"><span><b>' + esc(name(item)) + '</b><small>' + esc(detail(item)) + '</small></span><span class="elms-row-status">' + esc(status(item)) + '</span></button>'; }).join("");
		return '<section class="elms-admin-card"><div class="elms-admin-card-head"><h3>' + esc(title) + '</h3><button class="elms-link-btn" data-action="' + addAction + '">+ Добавить</button></div><p class="elms-muted">' + esc(subtitle) + '</p><div class="elms-admin-list">' + (rows || '<div class="elms-muted">Записей нет.</div>') + '</div></section>';
	}

	function bindActions(container) {
		(container || state.root).querySelectorAll("[data-action]").forEach(function (element) {
			element.addEventListener("click", function () {
				var action = element.getAttribute("data-action");
				if (action === "open") {
					if (element.getAttribute("data-doctype") === "ELMS Course") openCourseStudio(element.getAttribute("data-name"));
					else openForm(element.getAttribute("data-doctype"), element.getAttribute("data-name"));
				}
				if (action === "open-related") {
					if (element.getAttribute("data-doctype") === "ELMS Course") openCourseStudio(element.getAttribute("data-name"));
					else openForm(element.getAttribute("data-doctype"), element.getAttribute("data-name"));
				}
				if (action === "relationship-search") searchRelationships(container || state.root);
				if (action === "relationship-clear") {
					state.relationshipSearch = "";
					state.relationshipType = "";
					call("elms.lms.api.get_learning_relationships", {}, function (result) {
						if (!result) return;
						state.relationshipGroups = result.groups || [];
						renderManageTab();
					});
				}
				if (action === "course-new") openCourseStudio();
				if (action === "quiz-new") openForm("ELMS Quiz");
				if (action === "program-new") openForm("ELMS Program");
				if (action === "batch-new") openForm("ELMS Batch");
				if (action === "batch-for-course") {
					frappe.route_options = { course: element.getAttribute("data-course") };
					openForm("ELMS Batch");
				}
				if (action === "subscription-new") openForm("ELMS Subscription");
				if (action === "enroll") openEnrollmentDialog();
				if (action === "open-catalog") switchTab("catalog");
				if (action === "open-catalog-course") openPlayer(element.getAttribute("data-enr"));
				if (action === "program-open") {
					var program = element.getAttribute("data-program");
					var enrollment = element.getAttribute("data-enrollment");
					if (enrollment) openProgram(program, enrollment); else enrollInProgram(program);
				}
				if (action === "program-back") { state.programDetail = null; renderProgramsTab(); }
				if (action === "program-course-enroll") enrollProgramCourse(element.getAttribute("data-program-enrollment"), element.getAttribute("data-course"));
				if (action === "program-open-course") openPlayer(element.getAttribute("data-enr"));
			});
		});
	}

	function openForm(doctype, name) {
		if (!frappe.set_route) return;
		frappe.set_route("Form", doctype, name || "new-" + doctype.toLowerCase().replace(/\s+/g, "-"));
	}

	function openCourseStudio(course) {
		if (!frappe.set_route) return;
		if (course) frappe.set_route("elms-course-studio", course);
		else frappe.set_route("elms-course-studio");
	}

	function openEnrollmentDialog() {
		if (!frappe.ui || !frappe.ui.Dialog) return;
		var dialog = new frappe.ui.Dialog({
			title: "Оформить зачисление",
			fields: [{ fieldname: "user", fieldtype: "Link", options: "User", label: "Слушатель", reqd: 1 }, { fieldname: "batch", fieldtype: "Link", options: "ELMS Batch", label: "Поток", reqd: 1 }, { fieldname: "subscription", fieldtype: "Link", options: "ELMS Subscription", label: "Подписка / квота" }],
			primary_action_label: "Зачислить",
			primary_action: function (values) {
				call("elms.lms.api.enroll_learner", values, function (result) {
					if (!result) return;
					dialog.hide();
					frappe.show_alert({ message: "Слушатель зачислен", indicator: "green" });
					loadData();
				});
			}
		});
		dialog.show();
	}

	function startTimer() {
		if (state.timerInterval) clearInterval(state.timerInterval);
		if (state.heartbeatInterval) clearInterval(state.heartbeatInterval);
		state.timerInterval = setInterval(function () {
			if (!state.isPaused && state.currentLesson) {
				state.timeSpent += 1;
				state.pendingTimeSpent += 1;
				var timer = state.root && state.root.querySelector("#elms-study-timer");
				if (timer) timer.textContent = formatTime(state.timeSpent);
			}
		}, 1000);
		state.heartbeatInterval = setInterval(function () {
			if (!state.isPaused && state.currentEnrollment && state.currentLesson && state.pendingTimeSpent > 0) sendLessonProgress(Math.min(300, state.pendingTimeSpent), false);
		}, 15000);
	}

	function sendLessonProgress(delta, isCompleted) {
		if (!state.currentEnrollment || !state.currentLesson) return;
		if (state.savingProgress) return;
		state.savingProgress = true;
		call("elms.lms.api.record_lesson_progress", { enrollment: state.currentEnrollment, lesson_id: state.currentLesson, time_spent_delta: delta, mark_completed: isCompleted ? 1 : 0 }, function (result) {
			state.savingProgress = false;
			if (!result) return;
			state.pendingTimeSpent = Math.max(0, state.pendingTimeSpent - delta);
			if (isCompleted) {
				frappe.show_alert({ message: "Урок завершён, прогресс сохранён", indicator: "green" });
				loadData();
				if (state.currentStructure) openPlayer(state.currentEnrollment);
			}
		});
	}

	function bindAntiCheat() {
		window.addEventListener("blur", function () {
			state.isPaused = true;
			var dot = state.root && state.root.querySelector("#elms-pulse-indicator");
			var label = state.root && state.root.querySelector("#elms-telemetry-label");
			if (dot) dot.classList.add("paused");
			if (label) label.textContent = "Пауза: окно неактивно";
		});
		window.addEventListener("focus", function () {
			state.isPaused = false;
			var dot = state.root && state.root.querySelector("#elms-pulse-indicator");
			var label = state.root && state.root.querySelector("#elms-telemetry-label");
			if (dot) dot.classList.remove("paused");
			if (label) label.textContent = "Телеметрия активна · время фиксируется только при активном окне";
		});
	}

	function redirectLegacyAuthoringRoute() {
		if (!frappe.get_route || !frappe.set_route) return;
		var route = frappe.get_route();
		if (route && route[0] === "Form" && (route[1] === "ELMS Course Chapter" || route[1] === "ELMS Course Lesson")) {
			frappe.set_route("elms-course-studio");
			if (frappe.show_alert) frappe.show_alert({ message: "Разделы и уроки редактируются в Конструкторе курсов", indicator: "blue" });
		}
	}

	registerPage();
	frappe.provide("frappe.standard_pages");
	if (!frappe.standard_pages["elms"]) {
		frappe.standard_pages["elms"] = function () {
			frappe.set_route("Workspaces", "LMS");
		};
	}
	if (window.frappe) {
		frappe.re_route = frappe.re_route || {};
		frappe.re_route["elms"] = "lms";
	}
	$(document).on("toolbar_setup page-change", registerPage);
	$(document).on("page-change", redirectLegacyAuthoringRoute);
})();

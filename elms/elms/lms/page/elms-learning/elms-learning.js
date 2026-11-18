frappe.pages["elms-learning"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Обучение"),
		single_column: true,
	});
	const root = $(frappe.render_template("elms-learning", {})).appendTo(page.body);
	const importInput = root.find("[data-admission-import]");
	const previewPanel = root.find("[data-admission-preview]");
	const resultPanel = root.find("[data-admission-result]");
	const previewButton = root.find("[data-admission-preview-action]");
	const confirmButton = root.find("[data-admission-confirm]");

	const callAdmission = (method) =>
		frappe.call({
			method,
			args: { payload: JSON.stringify({ import_id: importInput.val() }) },
		});

	const reportFromResponse = (response) => response.message || response;

	const renderFailure = (error) => {
		const message = error?.message || "Не удалось выполнить действие";
		resultPanel.html(`<p class="text-danger">${frappe.utils.escape_html(message)}</p>`);
		confirmButton.prop("disabled", true);
	};

	const renderErrors = (report) => {
		if (!report.errors || !report.errors.length) return "";
		return `<ul class="text-danger">${report.errors
			.map((error) => `<li>${frappe.utils.escape_html(error.message)}</li>`)
			.join("")}</ul>`;
	};

	const renderPreview = (report) => {
		const rows = (report.rows || [])
			.map(
				(row) =>
					`<li>${frappe.utils.escape_html(row.full_name || row.row_id || "Строка")}: ${frappe.utils.escape_html(
						row.program || "—"
					)}</li>`
			)
			.join("");
		previewPanel.html(
			`<p>Выбрано строк: <strong>${report.selected_count}</strong>. Осталось мест: <strong>${
				report.remaining_seats ?? "—"
			}</strong>.</p>${rows ? `<ul>${rows}</ul>` : ""}${renderErrors(report)}`
		);
		confirmButton.prop("disabled", !report.ok || !report.selected_count);
	};

	previewButton.on("click", () => {
		resultPanel.empty();
		callAdmission("elms.lms.api.admission.preview_admission_import")
			.then((response) => renderPreview(reportFromResponse(response)))
			.catch(renderFailure);
	});

	confirmButton.on("click", () => {
		confirmButton.prop("disabled", true);
		callAdmission("elms.lms.api.admission.confirm_admission_import")
			.then((response) => {
				const report = reportFromResponse(response);
				resultPanel.html(
					report.ok
						? `<p class="text-success">Зачислено: <strong>${report.enrolled_count}</strong>. Осталось мест: <strong>${report.remaining_seats}</strong>.</p>`
						: renderErrors(report)
				);
				if (!report.ok) confirmButton.prop("disabled", false);
			})
			.catch((error) => {
				renderFailure(error);
				confirmButton.prop("disabled", false);
			});
	});
};

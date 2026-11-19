(function () {
	"use strict";

	if (window.elmsCustomFields) return;

	var schemaVersion = 1;
	var targetDoctypes = ["ELMS Course", "ELMS Program", "ELMS Batch"];

	function responseMessage(response) {
		return response && response.message ? response.message : response || {};
	}

	function valuePresent(values, key) {
		return Object.prototype.hasOwnProperty.call(values || {}, key);
	}

	function isEmpty(value) {
		return value === null || value === undefined || (typeof value === "string" && !value.trim());
	}

	function setStoredValue(frm, state) {
		frm.set_value("custom_field_values", JSON.stringify(state.values));
		frm.set_value("custom_field_schema_version", schemaVersion);
	}

	function inputFor(definition, value, effectiveValue) {
		var input;
		if (definition.field_type === "select") {
			input = document.createElement("select");
			var inherited = document.createElement("option");
			inherited.value = "";
			inherited.textContent = isEmpty(effectiveValue) ? "—" : "Inherited: " + effectiveValue;
			input.appendChild(inherited);
			(definition.options || []).forEach(function (optionValue) {
				var option = document.createElement("option");
				option.value = optionValue;
				option.textContent = optionValue;
				input.appendChild(option);
			});
		} else {
			input = document.createElement("input");
			input.type = definition.field_type === "checkbox" ? "checkbox" : definition.field_type;
		}
		input.className = "elms-custom-field-control";
		input.dataset.fieldKey = definition.field_key;
		if (definition.field_type === "checkbox") {
			input.checked = value === true;
		} else if (!isEmpty(value)) {
			input.value = value;
		} else if (!isEmpty(effectiveValue)) {
			input.placeholder = String(effectiveValue);
		}
		return input;
	}

	function render(frm, data) {
		var field = frm.fields_dict && frm.fields_dict.section_break_custom_fields;
		if (!field || !field.wrapper) return;
		var wrapper = field.wrapper[0] || field.wrapper;
		var mount = field.body && (field.body[0] || field.body) || wrapper;
		var oldPanel = wrapper.querySelector(".elms-custom-fields-panel");
		if (oldPanel) oldPanel.remove();
		var panel = document.createElement("div");
		panel.className = "frappe-control elms-custom-fields-panel";
		var state = { values: Object.assign({}, data.stored_values || {}) };
		var definitions = data.definitions || [];

		if (!definitions.length) {
			var empty = document.createElement("p");
			empty.className = "elms-custom-fields-empty";
			empty.textContent = "Для этой формы дополнительные поля ещё не настроены.";
			panel.appendChild(empty);
			mount.appendChild(panel);
			if (frm.layout && typeof frm.layout.refresh_sections === "function") {
				frm.layout.refresh_sections();
			}
			return;
		}

		definitions.forEach(function (definition) {
			if (!definition.active) return;
			var row = document.createElement("div");
			row.className = "elms-custom-field-row";
			var label = document.createElement("label");
			label.className = "elms-custom-field-label";
			label.textContent = definition.label + (definition.required ? " *" : "");
			var hasStored = valuePresent(state.values, definition.field_key);
			var input = inputFor(
				definition,
				hasStored ? state.values[definition.field_key] : "",
				(data.effective_values || {})[definition.field_key]
			);
			input.addEventListener("change", function () {
				if (definition.field_type === "checkbox") {
					state.values[definition.field_key] = input.checked;
				} else {
					state.values[definition.field_key] = input.value;
				}
				setStoredValue(frm, state);
			});
			label.appendChild(input);
			row.appendChild(label);
			panel.appendChild(row);
		});
		mount.appendChild(panel);
		if (frm.layout && typeof frm.layout.refresh_sections === "function") {
			frm.layout.refresh_sections();
		}
	}

	function load(frm) {
		if (!frm || targetDoctypes.indexOf(frm.doctype) === -1) return;
		var organization = frm.doc && frm.doc.organization;
		if (!organization) return;
		frappe.call({
			method: "elms.lms.api.custom_fields.get_custom_field_form_data",
			args: {
				target_doctype: frm.doctype,
				target_name: frm.docname,
				organization: organization,
			},
		}).then(function (response) {
			render(frm, responseMessage(response));
		}).catch(function (error) {
			frappe.msgprint({
				title: "Дополнительные поля",
				message: (error && error.message) || "Не удалось загрузить схему полей.",
				indicator: "orange",
			});
		});
	}

	window.elmsCustomFields = { load: load, render: render };

	if (frappe.ui && frappe.ui.form && frappe.ui.form.on) {
		targetDoctypes.forEach(function (doctype) {
			frappe.ui.form.on(doctype, { refresh: load });
		});
	}
})();

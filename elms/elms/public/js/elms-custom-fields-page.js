(function () {
	"use strict";

	function message(response) {
		return response && response.message ? response.message : response || {};
	}

	function call(method, args) {
		return frappe.call({ method: method, args: args || {} }).then(message);
	}

	function control(labelText, type, options) {
		var label = document.createElement("label");
		label.className = "elms-custom-fields-form-label";
		label.textContent = labelText;
		var input = document.createElement(type === "select" ? "select" : type === "textarea" ? "textarea" : "input");
		input.className = "elms-custom-fields-form-control";
		if (type !== "select" && type !== "textarea") input.type = type;
		(options || []).forEach(function (optionValue) {
			var option = document.createElement("option");
			option.value = optionValue.value || optionValue;
			option.textContent = option.label || optionValue;
			input.appendChild(option);
		});
		label.appendChild(input);
		return { label: label, input: input };
	}

	function pageRoot(wrapper) {
		var page = frappe.ui.make_app_page({ parent: wrapper, title: "Дополнительные поля", single_column: true });
		var root = document.createElement("div");
		root.className = "elms-custom-fields-page";
		page.main[0].appendChild(root);
		return root;
	}

	function render(wrapper) {
		var root = pageRoot(wrapper);
		var heading = document.createElement("div");
		heading.className = "elms-custom-fields-page-heading";
		var title = document.createElement("h1");
		title.textContent = "Дополнительные поля";
		var hint = document.createElement("p");
		hint.textContent = "Единая схема для Course, Program и Batch. Значения проверяются сервером перед сохранением.";
		heading.appendChild(title);
		heading.appendChild(hint);
		root.appendChild(heading);

		var toolbar = document.createElement("div");
		toolbar.className = "elms-custom-fields-toolbar";
		var organization = control("Организация", "select");
		var target = control("Документ", "select", ["ELMS Course", "ELMS Program", "ELMS Batch"]);
		toolbar.appendChild(organization.label);
		toolbar.appendChild(target.label);
		root.appendChild(toolbar);

		var form = document.createElement("form");
		form.className = "elms-custom-fields-definition-form";
		var key = control("Ключ поля", "text");
		var label = control("Подпись", "text");
		var type = control("Тип", "select", ["text", "number", "date", "select", "checkbox"]);
		var options = control("Варианты select, по одному в строке", "textarea");
		var required = control("Обязательное поле", "checkbox");
		var save = document.createElement("button");
		save.type = "submit";
		save.className = "btn btn-primary elms-custom-fields-save";
		save.textContent = "Сохранить поле";
		[key, label, type, options, required].forEach(function (item) { form.appendChild(item.label); });
		form.appendChild(save);
		root.appendChild(form);

		var list = document.createElement("div");
		list.className = "elms-custom-fields-list";
		root.appendChild(list);

		function refreshList() {
			if (!organization.input.value) return;
			call("elms.lms.api.custom_fields.get_custom_field_schema", {
				target_doctype: target.input.value,
				organization: organization.input.value,
			}).then(function (data) {
				list.textContent = "";
			(data.definitions || []).forEach(function (definition) {
				var item = document.createElement("div");
				item.className = "elms-custom-fields-list-item";
				var description = document.createElement("span");
				description.textContent = definition.label + " (" + definition.field_key + ", " + definition.field_type + ")";
				item.appendChild(description);
				if (definition.name) {
					var remove = document.createElement("button");
					remove.type = "button";
					remove.className = "btn btn-link btn-sm elms-custom-fields-delete";
					remove.textContent = "Удалить";
					remove.addEventListener("click", function () {
						call("elms.lms.api.custom_fields.delete_custom_field_definition", {
							name: definition.name,
							organization: organization.input.value,
						}).then(refreshList);
					});
					item.appendChild(remove);
				}
				list.appendChild(item);
				});
			}).catch(function (error) {
				list.textContent = (error && error.message) || "Не удалось загрузить схему.";
			});
		}

		call("elms.access.api.get_company_access_context").then(function (data) {
			(data.organizations || []).forEach(function (organizationValue) {
				var option = document.createElement("option");
				option.value = organizationValue;
				option.textContent = organizationValue;
				organization.input.appendChild(option);
			});
			if (data.organization) organization.input.value = data.organization;
			refreshList();
		}).catch(function (error) {
			organization.input.disabled = true;
			list.textContent = (error && error.message) || "Не удалось определить организацию.";
		});

		organization.input.addEventListener("change", refreshList);
		target.input.addEventListener("change", refreshList);
		form.addEventListener("submit", function (event) {
			event.preventDefault();
			var optionValues = options.input.value.split("\n").map(function (item) { return item.trim(); }).filter(Boolean);
			call("elms.lms.api.custom_fields.save_custom_field_definition", {
				definition: JSON.stringify({
					organization: organization.input.value,
					applies_to: target.input.value,
					field_key: key.input.value,
					label: label.input.value,
					field_type: type.input.value,
					options: optionValues,
					required: required.input.checked,
					schema_version: 1,
				}),
			}).then(function () {
				frappe.show_alert({ message: "Поле сохранено", indicator: "green" });
				form.reset();
				refreshList();
			}).catch(function (error) {
				frappe.msgprint({
					title: "Дополнительные поля",
					message: (error && error.message) || "Не удалось сохранить поле.",
					indicator: "red",
				});
			});
		});
	}

	window.elmsCustomFieldsPage = render;
	frappe.pages["elms-custom-fields"] = frappe.pages["elms-custom-fields"] || {};
	frappe.pages["elms-custom-fields"].on_page_load = function (wrapper) {
		render(wrapper);
	};
})();

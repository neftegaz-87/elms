(function () {
	"use strict";

	frappe.pages["elms-admission"] = frappe.pages["elms-admission"] || {};
	frappe.pages["elms-admission"].on_page_load = function (wrapper) {
		var start = function () {
			if (window.elmsAdmissionPage) window.elmsAdmissionPage(wrapper);
		};
		if (window.elmsAdmissionPage) start();
		else frappe.require("/assets/elms/js/desk-admission.js", start);
	};
})();

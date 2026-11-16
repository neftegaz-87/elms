(function () {
	"use strict";

	frappe.pages["elms-cabinet"] = frappe.pages["elms-cabinet"] || {};
	frappe.pages["elms-cabinet"].on_page_load = function (wrapper) {
		var start = function () {
			if (window.elmsCabinetPage) window.elmsCabinetPage(wrapper);
		};
		if (window.elmsCabinetPage) start();
		else frappe.require("/assets/elms/js/desk-cabinet.js", start);
	};
})();

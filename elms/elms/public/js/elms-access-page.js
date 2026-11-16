(function () {
	"use strict";

	frappe.pages["elms-access"] = frappe.pages["elms-access"] || {};
	frappe.pages["elms-access"].on_page_load = function (wrapper) {
		var start = function () {
			if (window.elmsAccessPage) window.elmsAccessPage(wrapper);
		};
		if (window.elmsAccessPage) start();
		else frappe.require("/assets/elms/js/desk-access.js", start);
	};
})();

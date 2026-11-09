(function () {
	"use strict";

	frappe.pages["elms-course-studio"] = frappe.pages["elms-course-studio"] || {};
	frappe.pages["elms-course-studio"].on_page_load = function (wrapper) {
		var start = function () {
			if (window.elmsCourseStudio) window.elmsCourseStudio(wrapper);
		};
		if (window.elmsCourseStudio) start();
		else frappe.require("/assets/elms/js/course-studio.js", start);
	};
})();

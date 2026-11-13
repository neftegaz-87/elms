(function () {
	"use strict";

	frappe.pages["elms-learning"] = frappe.pages["elms-learning"] || {};
	frappe.pages["elms-learning"].on_page_load = function (wrapper) {
			var start = function () {
				if (window.elmsLearningPage) window.elmsLearningPage(wrapper);
			};

			if (window.elmsLearningPage) {
				start();
			} else {
				frappe.require("/assets/elms/js/desk-learning.js", start);
			}
		};
})();

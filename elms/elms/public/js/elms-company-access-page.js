(function () {
	"use strict";

	frappe.pages["elms-company-access"] = frappe.pages["elms-company-access"] || {};
	function start(wrapper) {
		var start = function () {
			if (window.elmsCompanyAccessPage) window.elmsCompanyAccessPage(wrapper);
		};
		if (window.elmsCompanyAccessPage) start();
		else frappe.require("/assets/elms/js/desk-company-access.js?v=4", start);
	}

	frappe.pages["elms-company-access"].on_page_load = function (wrapper) {
		start(wrapper);
	};
	frappe.pages["elms-company-access"].on_page_show = function (wrapper) {
		$(wrapper).addClass("elms-company-access-page-wrapper");
		if (!wrapper.querySelector(".elms-company-access-shell") && !wrapper._elms_company_access_loading) {
			start(wrapper);
		}
	};
})();

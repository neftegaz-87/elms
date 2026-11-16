(function () {
	"use strict";

	function register(pageName, type) {
		frappe.pages[pageName] = frappe.pages[pageName] || {};
		frappe.pages[pageName].on_page_load = function (wrapper) {
			var start = function () {
				if (window.elmsCompanyIntegrationsPage) window.elmsCompanyIntegrationsPage(wrapper, type);
			};
			if (window.elmsCompanyIntegrationsPage) start();
			else frappe.require("/assets/elms/js/desk-company-integrations.js", start);
		};
	}

	var pageTypes = {
		"elms-company-integrations": "",
		"elms-company-integration-llm": "LLM",
		"elms-company-integration-bitrix24": "Bitrix24",
		"elms-company-integration-custom-api": "Custom API"
	};
	var currentPage = (frappe.get_route_str && frappe.get_route_str()) || window.page_name;
	if (Object.prototype.hasOwnProperty.call(pageTypes, currentPage)) register(currentPage, pageTypes[currentPage]);
})();

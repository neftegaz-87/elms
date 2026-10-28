frappe.provide("frappe.ui");

frappe.ui.apply_layout_mode = function () {
	document.documentElement.setAttribute("data-ds-layout", "wide");
	document.body.setAttribute("data-ds-layout", "wide");
	localStorage.setItem("ds_layout_mode", "wide");
	localStorage.container_fullwidth = "true";
	$(document.body).addClass("full-width");
	$(".page-body").addClass("full-width");
	const collapsed = localStorage.getItem("ds_sidebar_collapsed") === "1";
	document.documentElement.classList.toggle("ds-sidebar-collapsed", collapsed);
	document.body.classList.toggle("ds-sidebar-collapsed", collapsed);
	if (frappe.ui.ensure_desk_sidebar_chrome) {
		frappe.ui.ensure_desk_sidebar_chrome();
	}
	return "wide";
};

frappe.ui.resolve_layout_mode = function () {
	return "wide";
};

$(document).on("page-change", () => {
	frappe.ui.apply_layout_mode();
});

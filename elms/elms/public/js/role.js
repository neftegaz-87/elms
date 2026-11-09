frappe.ui.form.on("Role", {
	refresh(frm) {
		if (frm.is_new() || !frm.doc.name || !frappe.user.has_role("ELMS Admin")) return;
		frm.add_custom_button(__("Открыть матрицу прав"), () => {
			frappe.route_options = { role: frm.doc.name };
			frappe.set_route("permission-manager");
		});
	},
});

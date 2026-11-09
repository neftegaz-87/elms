frappe.ui.form.on("User Group", {
	refresh(frm) {
		if (!frm.doc.name || !frappe.user.has_role("ELMS Admin")) return;
		frappe.call({
			method: "elms.permissions.get_group_policy",
			args: { group: frm.doc.name },
		}).then((response) => {
			const policy = response.message || {};
			const escape = frappe.utils.escape_html;
			const wrapper = frm.fields_dict.user_group_members?.wrapper;
			if (!wrapper) return;
			frm.$wrapper.find(".elms-group-policy").remove();
			$(wrapper).before(`<div class="elms-group-policy alert alert-info"><b>${__("Назначение группы")}</b>: ${escape(policy.purpose || "")}<br><b>${__("Ограничение")}</b>: ${escape(policy.limitation || "")}</div>`);
		});
	},
});

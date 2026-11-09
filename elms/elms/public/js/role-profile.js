frappe.ui.form.on("Role Profile", {
	refresh(frm) {
		if (!frm.fields_dict.roles_html) return;
		frappe.call({
			method: "elms.permissions.get_role_profile_summary",
			args: { role_profile: frm.doc.name },
		}).then((response) => {
			const summary = response.message || {};
			const escape = frappe.utils.escape_html;
			const roleRows = (summary.roles || [])
				.map((role) => `<li><b>${escape(role.name)}</b><span class="text-muted"> — ${escape(role.description)}</span></li>`)
				.join("");
			const permissionRows = (summary.permissions || [])
				.map((permission) => `<tr><td>${escape(permission.doctype)}</td><td>${escape(permission.rights.join(", "))}</td></tr>`)
				.join("");
			const users = (summary.users || []).map((user) => escape(user.full_name || user.name)).join(", ");
			frm.$wrapper.find(".elms-access-summary").remove();
			$(frm.fields_dict.roles_html.wrapper).after(`
				<div class="elms-access-summary mt-4">
					<p><b>${__("Что делает профиль")}</b></p>
					<ul>${roleRows || `<li class="text-muted">${__("Роли не назначены")}</li>`}</ul>
					<p><b>${__("Эффективные действия")}</b></p>
					<table class="table table-bordered"><thead><tr><th>${__("Сущность")}</th><th>${__("Действия")}</th></tr></thead><tbody>${permissionRows}</tbody></table>
					<p class="text-muted">${__("Профиль назначается пользователю. Группа пользователей не меняет состав профиля.")}</p>
					<p><b>${__("Пользователи")}</b>: ${users || __("Пока никто не назначен")}</p>
				</div>
			`);
		});
	},
});

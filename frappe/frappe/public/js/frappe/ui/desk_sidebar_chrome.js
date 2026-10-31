frappe.provide("frappe.ui");

frappe.ui.get_desk_display_label = function (value) {
	if (value == null) return value;

	return String(value)
		.replace(/\bFrappe CRM\b/g, "CRM")
	.replace(/\bERPNext Settings\b/g, "Настройки учёта")
	.replace(/\bERPNext\b/g, "Учёт")
		.replace(/\bFrappe Cloud\b/g, "Cloud")
		.replace(/\bFrappe Mail\b/g, "Mail")
	.replace(/\bFrappe Framework\b/g, "Рабочая платформа")
	.replace(/\bFrappe\b/g, "Платформа");
};

frappe.ui.apply_desk_display_labels = function ($root) {
	$root = $root && $root.length ? $root : $(document);

	$root.find(".sidebar-item-label").each(function () {
		$(this).text(__(frappe.ui.get_desk_display_label($(this).text())));
	});
	$root.find(".item-anchor").each(function () {
		const title = $(this).attr("title");
		if (title) {
			$(this).attr("title", __(frappe.ui.get_desk_display_label(title)));
		}
	});
};

frappe.ui.sync_desk_workspace_surface = function () {
	const route = frappe.get_route?.() || [];
	const is_workspace_route = route[0] === "Workspaces";
	const $workspace = $(".page-container").filter(function () {
		return $(this).find(".editor-js-container, #editorjs").length > 0;
	});

	$(".page-container").removeClass("ds-workspace");
	$workspace.toggleClass("ds-workspace", is_workspace_route);
};

frappe.ui.ensure_desk_sidebar_chrome = function (opts) {
	opts = opts || {};
	if (!document.documentElement.getAttribute("data-ds-layout")) {
		return;
	}

	let $rail = $("#ds-app-rail");
	if (!$rail.length) {
		$rail = $(`
			<aside id="ds-app-rail" class="ds-app-rail" aria-label="${__("Navigation")}">
				<div class="ds-desk-sidebar-shell">
					<div class="ds-sidebar-body"></div>
				</div>
			</aside>
		`);
		$("body").prepend($rail);
	}

	const $shell = $rail.children(".ds-desk-sidebar-shell");
	if (!$shell.children(".ds-sidebar-user").length) {
		$shell.prepend(frappe.ui.build_desk_sidebar_user());
	} else {
		frappe.ui.refresh_desk_sidebar_user($shell.children(".ds-sidebar-user"));
	}

	if (!$shell.children(".ds-sidebar-footer").length) {
		$shell.append(frappe.ui.build_desk_sidebar_collapse());
	}

	frappe.ui.bind_desk_sidebar_collapse($shell);
	frappe.ui.sync_desk_app_rail_nav($shell, opts.force_nav);
	frappe.ui.apply_desk_display_labels($shell);
	frappe.ui.sync_desk_workspace_surface();
	frappe.ui.sync_desk_rail_selected();
	$(".dropdown-navbar-user").addClass("ds-navbar-user-hidden");
};

frappe.ui.rail_nav_signature = function ($page_desk) {
	return (
		$page_desk.find(".sidebar-item-container").length +
		":" +
		$page_desk
			.find(".sidebar-item-container")
			.map(function () {
				return this.getAttribute("item-name") || "";
			})
			.get()
			.join("|")
	);
};

frappe.ui.build_boot_desk_sidebar = function () {
	const pages = Array.isArray(frappe.boot?.allowed_workspaces)
		? frappe.boot.allowed_workspaces.filter((item) => item.title !== "CRM")
		: [];
	if (!pages.length) return $();

	const $nav = $('<div class="desk-sidebar list-unstyled sidebar-menu ds-rail-nav"></div>');
	const $section = $('<div class="standard-sidebar-section nested-container" data-title="Public"></div>');

	const append_item = (item, $container) => {
		const slug = frappe.router.slug(item.title);
		const href =
			item.title === "Frappe CRM"
				? "/app/frappe-crm"
				: `/app/${item.public ? slug : `private/${slug}`}`;
		const label = frappe.ui.get_desk_display_label(item.title);
		const $item_container = $("<div>")
			.addClass("sidebar-item-container")
			.attr({
				"item-parent": item.parent_page || "",
				"item-name": item.title,
				"item-public": item.public || 0,
				"item-is-hidden": item.is_hidden || 0,
			});
		const $item = $("<div>").addClass("desk-sidebar-item standard-sidebar-item");
		const $anchor = $("<a>")
			.addClass("item-anchor")
			.attr({ href, title: __(label) });
		const $icon = $("<span>")
			.addClass("sidebar-item-icon")
			.attr("item-icon", item.icon || "folder-normal")
			.html(frappe.utils.icon(item.icon || "folder-normal", "md"));

		$anchor.append($icon, $("<span>").addClass("sidebar-item-label").text(__(label)));
		$item.append($anchor, $("<div>").addClass("sidebar-item-control"));
		const $children = $("<div>").addClass("sidebar-child-item nested-container hidden");
		$item_container.append($item, $children).appendTo($container);

		pages
			.filter((child) => child.parent_page === item.title)
			.forEach((child) => append_item(child, $children));
		if ($children.children().length) {
			$item
				.find(".sidebar-item-control")
				.append(
					$("<button>")
						.addClass("btn-reset drop-icon")
						.html(frappe.utils.icon("es-line-down", "sm"))
				);
		}
	};

	pages.filter((item) => !item.parent_page).forEach((item) => append_item(item, $section));
	return $nav.append($section);
};

frappe.ui.sync_desk_app_rail_nav = function ($shell, force_nav) {
	const $body = $shell.children(".ds-sidebar-body");
	const $page_desk = $(".layout-side-section .desk-sidebar").not(".ds-rail-nav").first();
	let $rail_nav = $body.children(".desk-sidebar.ds-rail-nav").first();

	frappe.ui.bind_desk_rail_nav($body);

	if ($page_desk.length) {
		$page_desk.closest(".layout-side-section").addClass("ds-side-hosted");
		const signature = frappe.ui.rail_nav_signature($page_desk);

		if (
			$rail_nav.length &&
			frappe.ui._ds_rail_nav_sig === signature &&
			!force_nav
		) {
			return;
		}

		if (
			frappe.ui._ds_rail_nav_sig === signature &&
			frappe.ui._ds_rail_nav &&
			frappe.ui._ds_rail_nav.length
		) {
			if (!$rail_nav.length) {
				$body.append(frappe.ui._ds_rail_nav);
			}
			return;
		}

		const $clone = $page_desk.clone(false, false).addClass("ds-rail-nav");
		$clone.find('.sidebar-item-container[item-name="CRM"]').remove();
		$clone
			.find('.sidebar-item-container[item-name="Frappe CRM"] > .desk-sidebar-item a.item-anchor')
			.attr("href", "/app/frappe-crm");
		$clone.find(".sidebar-item-control").each(function () {
			$(this).children().not(".drop-icon").remove();
		});
		$clone.find(".item-anchor").removeClass("disable-click");
		$clone.find(".desk-sidebar-item.selected").removeClass("selected");
		frappe.ui._ds_rail_nav = $clone;
		frappe.ui._ds_rail_nav_sig = signature;
		frappe.ui.apply_desk_display_labels($clone);
		$body.empty().append($clone);
		return;
	}

	if (!$rail_nav.length && !frappe.ui._ds_rail_nav) {
		const $boot_nav = frappe.ui.build_boot_desk_sidebar();
		if ($boot_nav.length) {
			frappe.ui._ds_rail_nav = $boot_nav;
			frappe.ui._ds_rail_nav_sig = `boot:${frappe.ui.rail_nav_signature($boot_nav)}`;
			$body.append($boot_nav);
		}
	}

	if (!$rail_nav.length && frappe.ui._ds_rail_nav && frappe.ui._ds_rail_nav.length) {
		$body.append(frappe.ui._ds_rail_nav);
	}
};

frappe.ui.sync_desk_rail_selected = function () {
	const $nav = $("#ds-app-rail .desk-sidebar.ds-rail-nav");
	if (!$nav.length) {
		return;
	}

	$nav.find(".desk-sidebar-item.selected").removeClass("selected");
	$nav.find(".item-anchor").removeClass("disable-click");

	const route = frappe.get_route() || [];
	let page_name = null;

	if (route[0] === "Workspaces") {
		page_name = route[1] === "private" ? route[2] : route[1];
	} else if (route[0] && frappe.workspaces) {
		const key = frappe.router.slug(route[0]);
		if (frappe.workspaces[key]) {
			page_name = frappe.workspaces[key].title;
		}
	}

	const slug = page_name ? frappe.router.slug(page_name) : null;
	$nav.find(".sidebar-item-container").each(function () {
		const name = this.getAttribute("item-name");
		const href = this.querySelector(":scope > .desk-sidebar-item a.item-anchor")?.getAttribute("href");
		const is_current =
			name && slug && frappe.router.slug(name) === slug
				? true
				: href && new URL(href, window.location.origin).pathname === window.location.pathname;
		if (is_current) {
			$(this).children(".desk-sidebar-item").first().addClass("selected");
		}
	});
};

frappe.ui.get_desk_app_title = function () {
	const apps = frappe.boot?.apps_data?.apps || [];
	const elms_app = apps.find((app) => app.name === "elms");
	return elms_app?.title || apps[0]?.title || __("Frappe");
};

frappe.ui.bind_desk_rail_nav = function ($body) {
	if ($body.data("ds-rail-nav-bound")) return;
	$body.data("ds-rail-nav-bound", 1);

	$body.on("click.dsRailNav", ".desk-sidebar-item", function (e) {
		if ($(e.target).closest(".drop-icon").length) {
			return;
		}

		const anchor = this.querySelector("a.item-anchor");
		if (!anchor) {
			return;
		}

		const href = anchor.getAttribute("href");
		if (!href || href === "#") {
			e.preventDefault();
			return;
		}

		e.preventDefault();
		e.stopPropagation();

		$("#ds-app-rail .desk-sidebar-item.selected").removeClass("selected");
		$(this).addClass("selected");

		if (frappe.router.is_app_route(anchor.pathname)) {
			frappe.set_route(anchor.pathname);
			return;
		}

		const path = href.replace(/^\/app\/?/, "").replace(/\/+$/, "");
		frappe.set_route(path ? path.split("/") : "/app");
	});

	$body.on("click.dsRailNav", ".drop-icon", function (e) {
		e.preventDefault();
		e.stopPropagation();
		const $btn = $(this);
		const $item = $btn.closest(".sidebar-item-container");
		const $child = $item.children(".sidebar-child-item");
		const $use = $btn.find("use");
		const next = $use.attr("href") === "#es-line-down" ? "#es-line-up" : "#es-line-down";
		$use.attr("href", next);
		$child.toggleClass("hidden");
	});
};

frappe.ui.build_desk_sidebar_user = function () {
	const logo = frappe.boot.app_logo_url || "/assets/frappe/images/platform-logo.svg";
	const app_name = frappe.ui.get_desk_app_title();
	const full_name =
		(frappe.boot.user && frappe.boot.user.full_name) || frappe.session.user || "";

	const $user = $(`
		<div class="ds-sidebar-user dropdown">
			<button type="button" class="btn-reset ds-sidebar-user-btn" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
				<img class="ds-sidebar-user-logo" src="${frappe.utils.escape_html(logo)}" alt="" />
				<span class="ds-sidebar-user-text">
					<span class="ds-sidebar-user-app">${frappe.utils.escape_html(__(app_name))}</span>
					<span class="ds-sidebar-user-name">${frappe.utils.escape_html(full_name)}</span>
				</span>
				<span class="ds-sidebar-user-chevron">${frappe.utils.icon("es-line-down", "sm")}</span>
			</button>
			<div class="dropdown-menu ds-sidebar-user-menu" role="menu"></div>
		</div>
	`);

	frappe.ui.fill_desk_sidebar_user_menu($user.find(".ds-sidebar-user-menu"));
	return $user;
};

frappe.ui.refresh_desk_sidebar_user = function ($user) {
	const logo = frappe.boot.app_logo_url || "/assets/frappe/images/platform-logo.svg";
	const app_name = frappe.ui.get_desk_app_title();
	const full_name =
		(frappe.boot.user && frappe.boot.user.full_name) || frappe.session.user || "";
	$user.find(".ds-sidebar-user-logo").attr("src", logo);
	$user.find(".ds-sidebar-user-app").text(__(app_name));
	$user.find(".ds-sidebar-user-name").text(full_name);
};

frappe.ui.fill_desk_sidebar_user_menu = function ($menu) {
	$menu.empty();
	const items = (frappe.boot.navbar_settings && frappe.boot.navbar_settings.settings_dropdown) || [];

	items.forEach((item) => {
		if (item.hidden) return;
		let condition = true;
		if (item.condition) {
			try {
				condition = eval(item.condition);
			} catch (e) {
				condition = true;
			}
		}
		if (!condition) return;

		if (item.item_type === "Separator" || (!item.route && !item.action && !item.item_label)) {
			$menu.append(`<div class="dropdown-divider"></div>`);
			return;
		}

		if ((item.action || "").includes("toggle_full_width")) {
			return;
		}

		if (item.route) {
			$menu.append(
				`<a class="dropdown-item ds-sidebar-user-item" href="${frappe.utils.escape_html(
					item.route
				)}">${__(frappe.ui.get_desk_display_label(item.item_label))}</a>`
			);
			return;
		}

		if (item.action) {
			const $btn = $(
				`<button type="button" class="btn-reset dropdown-item ds-sidebar-user-item">${__(
					frappe.ui.get_desk_display_label(item.item_label)
				)}</button>`
			);
			$btn.attr("onclick", `return ${item.action}`);
			$menu.append($btn);
		}
	});
};

frappe.ui.build_desk_sidebar_collapse = function () {
	return $(`
		<div class="ds-sidebar-footer">
			<button type="button" class="btn-reset ds-sidebar-collapse-btn">
				<span class="sidebar-item-icon ds-sidebar-collapse-icon"></span>
				<span class="sidebar-item-label ds-sidebar-collapse-label"></span>
			</button>
		</div>
	`);
};

frappe.ui.bind_desk_sidebar_collapse = function ($shell) {
	const $btn = $shell.find(".ds-sidebar-collapse-btn");
	if (!$btn.length || $btn.data("ds-bound")) return;
	$btn.data("ds-bound", 1);

	const refresh = (collapsed) => {
		$btn.find(".ds-sidebar-collapse-icon").html(
			frappe.utils.icon("es-line-sidebar-collapse", "md")
		);
		$btn.find(".ds-sidebar-collapse-label").text(collapsed ? __("Expand") : __("Collapse"));
		$btn.attr("title", collapsed ? __("Expand Sidebar") : __("Collapse Sidebar"));
		$btn.attr("aria-expanded", String(!collapsed));
		$btn.toggleClass("is-collapsed", collapsed);
	};

	const apply = (collapsed) => {
		document.documentElement.classList.toggle("ds-sidebar-collapsed", collapsed);
		document.body.classList.toggle("ds-sidebar-collapsed", collapsed);
		localStorage.setItem("ds_sidebar_collapsed", collapsed ? "1" : "0");
		refresh(collapsed);
		$(document).trigger("ds-sidebar-collapse", [collapsed]);
		$(document.body).trigger("toggleSidebar");
	};

	$btn.on("click", () => {
		apply(!document.documentElement.classList.contains("ds-sidebar-collapsed"));
	});

	refresh(document.documentElement.classList.contains("ds-sidebar-collapsed"));
};

$(document).on("toolbar_setup page-change", () => {
	frappe.ui.ensure_desk_sidebar_chrome();
});

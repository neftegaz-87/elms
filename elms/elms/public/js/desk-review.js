(function () {
	"use strict";

	var reviewPageName = "elms-review";
	var reviewHref = "/app/" + reviewPageName;
	var reviewEndpoint = "/api/method/elms.sso.review.open_review";
	var reviewLabel = "Сверка заявки";
	var reviewRoles = ["ELMS Admin", "ELMS Operations User", "System Manager"];

	function registerReviewPage() {
		if (!window.frappe || !frappe.container || !frappe.ui) return;
		frappe.provide("frappe.standard_pages");
		if (frappe.standard_pages[reviewPageName]) return;

		frappe.standard_pages[reviewPageName] = function () {
			var wrapper = frappe.container.add_page(reviewPageName);
			var page = frappe.ui.make_app_page({
				parent: wrapper,
				title: reviewLabel,
				single_column: true,
			});

			$(wrapper).addClass("elms-review-page");
			page.main.addClass("elms-review-page-main");

			var shell = document.createElement("div");
			shell.className = "elms-review-shell";

			var frame = document.createElement("iframe");
			frame.className = "elms-review-frame";
			frame.title = reviewLabel;
			frame.src = reviewEndpoint;
			frame.loading = "eager";
			frame.referrerPolicy = "no-referrer";
			frame.setAttribute("scrolling", "no");
			shell.append(frame);
			wrapper.append(shell);
		};
	}

	function canOpenReview() {
		var roles = (window.frappe && (frappe.user_roles || (frappe.boot && frappe.boot.user && frappe.boot.user.roles))) || [];
		return Array.isArray(roles) && reviewRoles.some(function (role) {
			return roles.indexOf(role) !== -1;
		});
	}

	function addReviewLink() {
		var rail = document.querySelector("#ds-app-rail .ds-rail-nav");
		if (!rail) return;
		var existing = rail.querySelector('[data-elms-review-link="1"]');
		if (!canOpenReview()) {
			if (existing) existing.remove();
			return;
		}
		if (existing) return;

		var section = rail.querySelector('.standard-sidebar-section[data-title="Public"]');
		if (!section) section = rail.querySelector(".standard-sidebar-section:not(.hidden)");
		if (!section) return;

		var container = document.createElement("div");
		container.className = "sidebar-item-container";
		container.setAttribute("item-parent", "");
		container.setAttribute("item-name", reviewLabel);
		container.setAttribute("item-public", "1");
		container.setAttribute("item-is-hidden", "0");
		container.setAttribute("data-elms-review-link", "1");

		var item = document.createElement("div");
		item.className = "desk-sidebar-item standard-sidebar-item";
		var anchor = document.createElement("a");
		anchor.className = "item-anchor";
		anchor.href = reviewHref;
		anchor.title = reviewLabel;
		anchor.addEventListener(
			"click",
			function (event) {
				event.preventDefault();
				event.stopPropagation();
				frappe.set_route(reviewPageName);
			},
			true
		);

		var icon = document.createElement("span");
		icon.className = "sidebar-item-icon";
		icon.setAttribute("item-icon", "check-circle");
		if (window.frappe && frappe.utils && frappe.utils.icon) {
			icon.innerHTML = frappe.utils.icon("check-circle", "md");
		}

		var label = document.createElement("span");
		label.className = "sidebar-item-label";
		label.textContent = reviewLabel;
		anchor.appendChild(icon);
		anchor.appendChild(label);
		item.appendChild(anchor);
		var control = document.createElement("div");
		control.className = "sidebar-item-control";
		item.appendChild(control);
		container.appendChild(item);
		section.appendChild(container);
	}

	function install() {
		registerReviewPage();
		if (!window.frappe || !frappe.ui || !frappe.ui.ensure_desk_sidebar_chrome) return;
		if (!frappe.ui._elms_review_sidebar_installed) {
			var ensure = frappe.ui.ensure_desk_sidebar_chrome;
			frappe.ui.ensure_desk_sidebar_chrome = function () {
				var result = ensure.apply(this, arguments);
				addReviewLink();
				return result;
			};
			frappe.ui._elms_review_sidebar_installed = true;
		}
		addReviewLink();
	}

	registerReviewPage();
	$(document).on("toolbar_setup page-change", install);
	new MutationObserver(install).observe(document.body, { childList: true, subtree: true });
	install();
})();

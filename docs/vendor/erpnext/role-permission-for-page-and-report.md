---
title: "Role Permission for Page and Report\n"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/role-permission-for-page-and-report"
updated: "2026-03-02"
---

**Access to different pages and reports can be controlled in Role Permission for Page and Report.**

Document types are Sales Order, Customer, Supplier, etc. They are a **document type** meaning they can contain multiple documents of that type. A Page is a single page like [Selling Settings](/erpnext/selling-settings). You cannot create multiple Selling Settings, but you can create multiple Sales Orders.

In ERPNext, user can make a custom user interface using Page and a custom report using [Report Builder](/framework/user/en/desk/reports/report-builder) or [Query Report](/framework/user/en/desk/reports/query-report). ERPNext has a [role-based permission system](/erpnext/role-based-permissions) where you can assign roles to the user. The same role can be assigned to the page and report to access them.

If the user has enabled developer mode, then they can add the roles directly in the page and report record. In that case, the permissions will also be reflected in the JSON file for the page/report. Consider you want to restrict the roles that can access certain pages and reports in ERPNext, this can be done via the Role Permission for Page and Report.

To access Role Permission for Page and Report, go to:

> Home > Users and Permissions > Role Permission for Page and Report

## 1. How to use Role Permission for Page and Report Tool

If developer mode is disabled, the user can assign the roles to the page and report, using "Role Permission for Page and Report" page.

![Tools to assign custom roles to the page](/files/role-permission-for-page-and-report.png)

### 1.1 Reset to defaults

Using the "Reset to Defaults" button, the user can remove the custom permissions applied on a page or report. Then default permissions will be applicable on that page or report.

![Reset the default roles](/files/reset-roles-permission-for-page-report.png)

## Setting Role Permissions from the Page/Report as a Developer

### Role Permissions For Page

1. Go to: Home > Developer > Page.
2. Add a row and select which other roles can access the Page.
  [Assign roles to the page](/files/roles-for-page.png)

### Role Permissions For Report

1. Go to: Home > Developer > Report.
2. Add rows with roles who can access the Report.
  [Assign roles to the report](/files/roles-for-report.png)


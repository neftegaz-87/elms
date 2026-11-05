---
title: "Fiscal Year | ERPNext Documentation"
description: "Create, assign, and manage fiscal years in ERPNext and understand how they differ from accounting periods and year-end closing."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/fiscal-year"
updated: "2026-08-14"
---

A financial report is meaningful only when ERPNext knows where one reporting year ends and the next begins. A Fiscal Year defines that period for transactions, budgets, opening balances, and year-end closing.



For Nova Industries, the finance team may report from January to December while another company on the same site follows April to March. Separate Fiscal Year records let both companies post and compare transactions using the periods required by their owners, auditors, and local regulations.



This page shows how to create the period, assign it to the right companies, control posting dates, and avoid gaps or overlaps that can make transactions fail validation.

## Create a Fiscal Year

1. Go to **Home &gt; Accounting &gt; Accounting Masters &gt; Fiscal Year**.
2. Click **Add Fiscal Year**.
3. Enter a name, start date, and end date.
4. Add the companies that use it.
5. Enable **Is Short Year** only for a genuine transition period shorter than twelve months.
6. Save.

![Fiscal Year dates and company](/files/fiscal-year-dates.webp)

## Set the default Fiscal Year

Open the Fiscal Year and use the action to set it as default. ERPNext uses the default year when it initializes posting dates and report filters.

The posting date still determines the actual fiscal year. A transaction cannot be posted outside a valid Fiscal Year for its company.

## Create the next year

ERPNext can create the next Fiscal Year shortly before the current year ends. Confirm the dates and company assignment before users begin posting in it.

## Fiscal Year, Accounting Period, and closing

These records serve different purposes:


| Record                 | Purpose                                               |
| ---------------------- | ----------------------------------------------------- |
| Fiscal Year            | Defines the accounting year and reporting period      |
| Accounting Period      | Restricts selected transaction types for a date range |
| Period Closing Voucher | Transfers profit or loss to a closing account         |


Creating a new Fiscal Year does not close the previous one. Complete reconciliation, adjustments, reporting, and the closing voucher as separate activities.

## Troubleshooting

**The posting date is outside the Fiscal Year**

Create or assign the correct Fiscal Year to the company. Do not alter historical dates to bypass the validation.

**A report opens in the wrong year**

Change the report filter or set the intended Fiscal Year as default.

## Related topics

- [Accounting Period](https://docs.frappe.io/erpnext/accounting-period)
- [Period Closing Voucher](https://docs.frappe.io/erpnext/period-closing-voucher)
- [Company accounting defaults](https://docs.frappe.io/erpnext/company-accounting-defaults)
- [Accounting Setup Checklist](https://docs.frappe.io/erpnext/accounting-setup-checklist)
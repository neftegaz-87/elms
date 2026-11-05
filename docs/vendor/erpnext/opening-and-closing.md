---
title: "Opening and Closing During Migration | ERPNext Documentation"
description: "Close the legacy accounting period, load ERPNext opening data in sequence, reconcile it, freeze the accepted period, and control later corrections."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/opening-and-closing"
updated: "2026-07-31"
---

Opening activities establish the first reliable ERPNext balances. Closing activities finalize the legacy period and prevent changes after reconciliation.

## Close the legacy system

Before extracting final balances:

1. Enter all approved transactions through the cutover date.
2. Reconcile bank and cash.
3. Complete stock count and valuation.
4. Post depreciation, payroll, tax, accruals, prepayments, and exchange adjustments.
5. Reconcile Customer and Supplier control accounts.
6. Run final Trial Balance and supporting schedules.
7. Lock the legacy period and restrict new entries.

Record late invoices or payments in a cutover log and decide which system will receive them.

## Open ERPNext

Use the opening tools in this order:

1. Chart of Accounts Importer
2. Opening Invoice Creation Tool
3. Opening payments and advances
4. Stock Reconciliation
5. Asset opening records
6. Opening Journal Entry for remaining balances

Run the Trial Balance after each stage so errors are isolated to the current batch.

## Opening Invoice Creation Tool

This tool creates outstanding Customer and Supplier invoices without historical Item detail. It is appropriate for opening ageing but not for historical sales analytics or stock.

## Chart of Accounts Importer

Use it before balances are loaded. Review account types and Company defaults after import.

## Period Closing Voucher

The Period Closing Voucher transfers the net balance of income and expense accounts to a closing account. It is not an opening-balance import tool.

Use it only when the ERPNext period itself needs to be closed. If ERPNext starts at the beginning of a new fiscal year, the legacy system may already contain the year-end closing.

## Freeze the accepted opening

After reconciliation and sign-off:

- save the approved reports;
- restrict the migration user;
- freeze accounts through the cutover date;
- create an Accounting Period if selected transactions must be blocked;
- document authorized correction procedures.

Do not freeze before reconciliation is complete because correction then requires privileged overrides.

## Reopen only with approval

If an accepted opening period must be corrected:

1. document the error and financial impact;
2. obtain finance approval;
3. temporarily permit the authorized role;
4. cancel and amend or post a referenced correction;
5. rerun all affected reconciliations;
6. restore the freeze;
7. update sign-off evidence.

## Related topics

- [Opening Balance in Accounts](https://docs.frappe.io/erpnext/opening-balance)
- [Period Closing Voucher](https://docs.frappe.io/erpnext/period-closing-voucher)
- [Accounting Period](https://docs.frappe.io/erpnext/accounting-period)
- [Accounts Settings](https://docs.frappe.io/erpnext/accounts-settings)
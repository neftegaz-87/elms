---
title: "Asset Value Adjustment | ERPNext Documentation"
description: "Adjust an ERPNext Asset's carrying value for a selected Finance Book and verify the resulting accounting entry."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/asset-value-adjustment"
updated: "2026-08-15"
---

Imagine an independent valuation shows that a Nova Industries machine is worth $8,000 less than its current book value. If the accountant changes the value only in a spreadsheet, the Asset record and General Ledger will no longer agree.



Asset Value Adjustment records the new value on a specific date and posts the accounting effect through the configured accounts. This keeps the revised carrying value, future depreciation, and ledger history connected.

## Before you begin

Obtain an approved valuation, confirm the effective date, select the correct [Finance Book](https://docs.frappe.io/erpnext/using-finance-book-for-asset-depreciation), and identify the difference account and cost center.

## Create the adjustment

1. Select the Asset and date.
2. Select the Finance Book when the change applies to one reporting basis.
3. Review the Current Asset Value.
4. Enter the New Asset Value.
5. Select the Difference Account and cost center.
6. Submit and open the linked Journal Entry.

![Asset Value Adjustment from 36000 to 39000](https://novacompanies.m.frappe.cloud/files/18-asset-value-adjustment.png)

## Verify the result

Confirm the Asset's carrying value and future depreciation schedule changed only for the intended Finance Book. Use Asset Depreciations and Balances to reconcile the result.

![Asset report used to verify an adjusted value](https://novacompanies.m.frappe.cloud/files/23-asset-depreciations-balances-v2.png)

## Troubleshooting

### Current value is not what the valuation expected

Check the Finance Book, effective date, booked depreciation, and earlier value adjustments.

### The difference posts to the wrong account

Cancel or reverse according to policy, then correct the category or selected Difference Account before reposting.

## Frequently asked questions

### Is this the same as depreciation?

In ERPNext, no. Depreciation follows a schedule; value adjustment records a separate approved change in carrying value.

### Can I adjust only one Finance Book?

In ERPNext, yes. Select it explicitly and verify reports using the same filter.

### Does the adjustment create a Journal Entry?

A submitted adjustment creates or links the accounting entry for the difference.

## Related topics

- [Asset Category](https://docs.frappe.io/erpnext/asset-category)
- [Asset Location](https://docs.frappe.io/erpnext/asset-location)
- [Asset](https://docs.frappe.io/erpnext/asset)
- [Purchasing an Asset](https://docs.frappe.io/erpnext/purchasing-an-asset)
- [Depreciation](https://docs.frappe.io/erpnext/asset-depreciation)
- [Asset Movement](https://docs.frappe.io/erpnext/asset-movement)
- [Asset Repair](https://docs.frappe.io/erpnext/asset-repair)
- [Asset Reports](https://docs.frappe.io/erpnext/asset-reports)
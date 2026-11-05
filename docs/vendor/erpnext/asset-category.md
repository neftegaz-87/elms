---
title: "Asset Category | ERPNext Documentation"
description: "Configure ERPNext Asset Categories with depreciation defaults, Finance Books, and company-specific fixed-asset accounts."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/asset-category"
updated: "2026-08-15"
---

Imagine Nova Industries buys 100 employee laptops over the next two years. If the accountant has to choose the useful life, depreciation method, and ledger accounts separately for every laptop, the records may become inconsistent and mistakes will be hard to find.



An Asset Category solves this by storing one reusable accounting policy for similar assets. Nova Industries can create an **IT Equipment** category once, then use the same depreciation and account defaults for every laptop added later.

## Before you begin

Confirm the company [Chart of Accounts](https://docs.frappe.io/erpnext/chart-of-accounts) contains a fixed-asset account, accumulated depreciation account, depreciation expense account, and capital work in progress account when CWIP is used. Create any required [Finance Books](https://docs.frappe.io/erpnext/finance-book) first.

## Create an Asset Category

1. Open **Asset Category** and select **Add Asset Category**.
2. Enter a clear name such as **IT Equipment** or **Production Equipment**.
3. Enable **Capital Work in Progress Accounting** when purchases should remain in CWIP until the asset becomes available for use.
4. Enable **Non Depreciable Category** only for categories such as land where depreciation does not apply.

![Asset Category depreciation options for IT Equipment](https://novacompanies.m.frappe.cloud/files/02-asset-category-overview.png)

## Set depreciation defaults by Finance Book

Add one row for every reporting basis you need. Nova Industries uses Straight Line for Statutory Reporting and Double Declining Balance for Management Reporting. Open the row editor with the pencil icon when you need fields that are not visible in the grid.

![Finance Book depreciation defaults in an ERPNext Asset Category](https://novacompanies.m.frappe.cloud/files/03-asset-category-finance-books.png)


| Field                             | What it means                                                              |
| --------------------------------- | -------------------------------------------------------------------------- |
| **Finance Book**                  | The reporting basis that owns this depreciation policy.                    |
| **Depreciation Method**           | How ERPNext spreads the depreciable value.                                 |
| **Frequency**                     | Months between scheduled depreciation entries.                             |
| **Total Number of Depreciations** | Number of scheduled postings across the useful life.                       |
| **Salvage Value Percentage**      | Expected residual value at the end of useful life.                         |
| **Daily Pro Rata**                | Calculates depreciation by actual days rather than equal periodic amounts. |
| **Shift Based**                   | Allows the depreciation amount to follow machine utilization by shift.     |


## Set company accounts

Each company row determines where acquisition, depreciation, and CWIP entries post. Do not use an inventory account as the Fixed Asset Account.

![Company accounting defaults for an ERPNext Asset Category](https://novacompanies.m.frappe.cloud/files/04-asset-category-accounts.png)


| Field                                | What it means                                                 |
| ------------------------------------ | ------------------------------------------------------------- |
| **Fixed Asset Account**              | Balance Sheet account that holds the capitalized asset value. |
| **Accumulated Depreciation Account** | Contra-asset account that accumulates depreciation.           |
| **Depreciation Expense Account**     | Profit and Loss account charged when depreciation is booked.  |
| **Capital Work in Progress Account** | Temporary asset account used before capitalization.           |


## Troubleshooting

### The Asset has the wrong depreciation defaults

Correct the category for future assets. For an existing draft Asset, reload or update the Finance Book rows before submission.

### ERPNext asks for an account during purchase or capitalization

Check that the category contains an Accounts row for the transaction company and that every linked account belongs to that company.

## Frequently asked questions

### Can two categories use the same accounts?

In ERPNext, yes. Categories may share accounts while keeping different useful lives or depreciation methods.

### Can the same category have two Finance Books?

In ERPNext, yes. Add one row per Finance Book when statutory and management depreciation differ.

### Does changing a category rewrite submitted Asset schedules?

Do not assume it will. Review affected Asset and Asset Depreciation Schedule records explicitly before relying on new defaults.

## Related topics

- [Asset Category](https://docs.frappe.io/erpnext/asset-category)
- [Asset Location](https://docs.frappe.io/erpnext/asset-location)
- [Asset](https://docs.frappe.io/erpnext/asset)
- [Purchasing an Asset](https://docs.frappe.io/erpnext/purchasing-an-asset)
- [Depreciation](https://docs.frappe.io/erpnext/asset-depreciation)
- [Asset Movement](https://docs.frappe.io/erpnext/asset-movement)
- [Asset Repair](https://docs.frappe.io/erpnext/asset-repair)
- [Asset Reports](https://docs.frappe.io/erpnext/asset-reports)
---
title: "Asset Capitalization | ERPNext Documentation"
description: "Combine stock, existing assets, and service costs into a new or composite ERPNext Asset."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/asset-capitalization"
updated: "2026-08-15"
---

Imagine Nova Industries builds a testing machine using purchased components, technician time, and installation services. During construction, those costs are collected separately. Once the machine is ready, the company needs to combine the qualifying costs into one fixed asset.



Asset Capitalization gathers those costs and transfers them to the completed Asset. It shows how the final value was built and prevents the company from treating a long-term asset as an immediate operating expense.

## Before you begin

Confirm the target fixed-asset Item and category, source assets, available stock, service expense accounts, Finance Book, posting date, and capitalization policy.

## Define the target

1. Create an Asset Capitalization.
2. Select the company and posting date.
3. Choose a target Item and enter a recognizable target Asset Name, or select an eligible composite target Asset.
4. Select the Finance Book when required.

![Target Asset details in ERPNext Asset Capitalization](https://novacompanies.m.frappe.cloud/files/19-asset-capitalization-target.png)

## Add source costs

Add stock items, consumed assets, and service expenses. The example combines an existing conveyor with setup services. Use the pencil icon whenever a child row needs account, warehouse, quantity, rate, or cost-center detail.

![Consumed asset and service cost tables in Asset Capitalization](https://novacompanies.m.frappe.cloud/files/20-asset-capitalization-costs.png)

## Submit and verify

ERPNext reduces or updates the source values according to the transaction and capitalizes the total into the target. Verify the target Asset, source Asset statuses, stock impact, Journal Entry or Stock Ledger effect, and future depreciation schedule.

![Asset report used to verify capitalized value](https://novacompanies.m.frappe.cloud/files/23-asset-depreciations-balances-v2.png)

## Troubleshooting

### The target Asset is not eligible

A selected existing target may need to be a Composite Asset. Otherwise create a new target from the fixed-asset Item.

### A service row cannot be saved

Provide the Item, expense account, quantity, rate, UOM, and cost center required by the row.

### Total value is zero

Add valid source rows and allow ERPNext to calculate their amounts before submission.

## Frequently asked questions

### Can I capitalize only services?

A valid capitalization can include qualifying services, but the target and accounting treatment must still satisfy the organization's policy.

### Can an existing Asset be consumed?

In ERPNext, yes, through the consumed-assets table when the workflow and target asset type permit it.

### Does capitalization immediately start depreciation?

Depreciation follows the target Asset's available-for-use date and Finance Book schedule.

## Related topics

- [Asset Category](https://docs.frappe.io/erpnext/asset-category)
- [Asset Location](https://docs.frappe.io/erpnext/asset-location)
- [Asset](https://docs.frappe.io/erpnext/asset)
- [Purchasing an Asset](https://docs.frappe.io/erpnext/purchasing-an-asset)
- [Depreciation](https://docs.frappe.io/erpnext/asset-depreciation)
- [Asset Movement](https://docs.frappe.io/erpnext/asset-movement)
- [Asset Repair](https://docs.frappe.io/erpnext/asset-repair)
- [Asset Reports](https://docs.frappe.io/erpnext/asset-reports)
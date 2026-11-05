---
title: "Overview | ERPNext Documentation"
description: "Understand the ERPNext Assets lifecycle, from purchase and capitalization through depreciation, maintenance, transfer, sale, or scrapping."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/assets/introduction"
updated: "2026-08-15"
---

Imagine you are helping the accounts team at Nova Industries, an electronics manufacturing and distribution company. The company buys phones to sell, laptops for employees, and machines for its packaging floor. The phones are inventory because customers will buy them. The laptops and machines are assets because Nova Industries will use them for several years.



The ERPNext Assets module keeps the complete story of those assets in one place. It records what the company owns, where each asset is, who uses it, how its value reduces over time, what it costs to maintain, and whether it is eventually sold or scrapped.

## Understand the asset lifecycle

1. Define an [Asset Category](https://docs.frappe.io/erpnext/asset-category) with the correct asset, accumulated depreciation, expense, and capital work in progress accounts.
2. Organize physical places in the [Asset Location](https://docs.frappe.io/erpnext/asset-location) tree.
3. Mark an Item as a fixed asset, then buy it or create an existing Asset record.
4. Place the asset in service and review its depreciation schedule.
5. Record assignment, [movement](https://docs.frappe.io/erpnext/asset-movement), [maintenance](https://docs.frappe.io/erpnext/asset-maintenance), [repair](https://docs.frappe.io/erpnext/asset-repair), and value adjustments during its life.
6. Finish the lifecycle by [selling](https://docs.frappe.io/erpnext/selling-an-asset) or [scrapping](https://docs.frappe.io/erpnext/scrapping-an-asset) the asset.

![ERPNext Asset list for Nova Industries showing laptops and production equipment](https://novacompanies.m.frappe.cloud/files/01-assets-overview-list.png)

## What the module records


| Field                | What it means                                                                                                          |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **Identity**         | Item, asset name, category, company, owner, and status.                                                                |
| **Physical control** | Current location, custodian, department, transfers, issues, and receipts.                                              |
| **Accounting**       | Purchase value, capitalization, Finance Books, depreciation schedules, accumulated depreciation, and disposal entries. |
| **Operations**       | Preventive maintenance plans, maintenance logs, failures, repairs, downtime, and repair cost.                          |
| **Lifecycle result** | Whether the asset remains in use, is out of order, has been sold, or has been scrapped.                                |


## Stock item versus fixed asset

Use a stock item when the company intends to sell or consume the item. Use a fixed-asset Item when the company will use the item to run the business for more than one accounting period. The same laptop model can therefore be inventory in an electronics store and a fixed asset when issued to the store manager.

## Accounting impact at a glance

An Asset record by itself is the operational register. Accounting entries arise from submitted acquisition, depreciation, value adjustment, capitalization, sale, or scrap transactions. Locations and maintenance logs change the operational history but do not normally post to the General Ledger.

## Frequently asked questions

### Can ERPNext manage non-depreciable assets?

In ERPNext, yes. Enable **Non Depreciable Category** when an asset category should not create depreciation schedules.

### Can one asset have different depreciation schedules?

In ERPNext, yes. Finance Books can maintain different methods or useful lives for statutory and management reporting.

### Does moving an asset create a ledger entry?

In ERPNext, no. Asset Movement changes custody or location. It does not change the asset's accounting value.

### Where can I see the complete asset register?

Use the [Fixed Asset Register](https://docs.frappe.io/erpnext/asset-reports) and related Asset reports.

## Related topics

- [Asset Category](https://docs.frappe.io/erpnext/asset-category)
- [Asset Location](https://docs.frappe.io/erpnext/asset-location)
- [Asset](https://docs.frappe.io/erpnext/asset)
- [Purchasing an Asset](https://docs.frappe.io/erpnext/purchasing-an-asset)
- [Depreciation](https://docs.frappe.io/erpnext/asset-depreciation)
- [Asset Movement](https://docs.frappe.io/erpnext/asset-movement)
- [Asset Repair](https://docs.frappe.io/erpnext/asset-repair)
- [Asset Reports](https://docs.frappe.io/erpnext/asset-reports)
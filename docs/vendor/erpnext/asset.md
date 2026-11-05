---
title: "Asset | ERPNext Documentation"
description: "Create and manage an ERPNext Asset record, including value, location, ownership, depreciation, insurance, and lifecycle status."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/asset"
updated: "2026-08-15"
---

An Asset record is the operating history of something the company uses. For Nova Industries' staff laptop, it connects the Item and purchase value to a current location, maintenance plan, depreciation schedule, and eventual disposal.



Create one only after deciding whether the item is company equipment rather than inventory held for sale.

## Before you begin

Prepare the fixed-asset Item, [Asset Category](https://docs.frappe.io/erpnext/asset-category), company accounts, and [Asset Location](https://docs.frappe.io/erpnext/asset-location). Use [Purchasing an Asset](https://docs.frappe.io/erpnext/purchasing-an-asset) when the record originates from a new purchase.

## Create an Asset

1. Open **Asset** and select **Add Asset**.
2. Select the Item and company.
3. Enter a recognizable Asset Name and current Location.
4. Select **Existing Asset** only when bringing an already-owned asset into ERPNext. Use **Composite Asset** when the asset is assembled by capitalization.
5. Enter purchase and available-for-use dates, value, and quantity.
6. Enable maintenance and depreciation only when they apply.

![Core ERPNext Asset fields for a Nova Industries laptop](https://novacompanies.m.frappe.cloud/files/07-asset-core-details.png)

## Important fields and what they mean


| Field                                | What it means                                                             |
| ------------------------------------ | ------------------------------------------------------------------------- |
| **Item Code**                        | The reusable Item definition for this asset model.                        |
| **Asset Name**                       | The human-readable identity, such as an internal tag or serial reference. |
| **Location**                         | Current physical position.                                                |
| **Asset Type**                       | Existing, Composite Asset, or Composite Component.                        |
| **Purchase Date**                    | Date the company acquired the asset.                                      |
| **Available for Use Date**           | Date capitalization and depreciation can begin.                           |
| **Net Purchase Amount**              | Capitalized acquisition value before later adjustments.                   |
| **Maintenance Required**             | Allows maintenance planning and logs.                                     |
| **Calculate Depreciation**           | Creates depreciation schedules from Finance Book settings.                |
| **Opening Accumulated Depreciation** | Depreciation already booked before migration to ERPNext.                  |
| **Custodian and Department**         | Operational responsibility and reporting ownership.                       |


## Review depreciation

Each Finance Book may have a different method, useful life, residual value, and posting frequency.

![Finance Book configuration on an ERPNext Asset](https://novacompanies.m.frappe.cloud/files/08-asset-finance-books.png)

## Status and downstream actions


| Field                              | What it means                                                  |
| ---------------------------------- | -------------------------------------------------------------- |
| **Submitted**                      | The asset is active in the register.                           |
| **Partially Depreciated**          | At least one depreciation is booked and value remains.         |
| **Fully Depreciated**              | The scheduled depreciable value has been booked.               |
| **In Maintenance or Out of Order** | Operational condition is restricted.                           |
| **Sold**                           | A disposal sale has completed.                                 |
| **Scrapped**                       | The asset was written off through the scrap workflow.          |
| **Capitalized**                    | The asset was created or updated through Asset Capitalization. |


![Asset statuses in the ERPNext list view](https://novacompanies.m.frappe.cloud/files/01-assets-overview-list.png)

## Troubleshooting

### The Asset value or account is wrong

Trace the source purchase, category account defaults, and any capitalization or value-adjustment entries. Do not correct only the visible total without understanding the ledger source.

### The Asset cannot be cancelled

Cancel or reverse linked submitted depreciation and disposal documents in the required order first.

## Frequently asked questions

### Can I change the location directly?

Use Asset Movement for a controlled transfer and an auditable history.

### Can I store insurance information?

In ERPNext, yes. Use the insurance fields for insurer, policy dates, insured value, and coverage details.

### Can one Asset contain multiple units?

Grouped assets support quantity-based use cases, but individual assets are clearer when each unit needs its own custodian, maintenance, or disposal history.

## Related topics

- [Asset Category](https://docs.frappe.io/erpnext/asset-category)
- [Asset Location](https://docs.frappe.io/erpnext/asset-location)
- [Asset](https://docs.frappe.io/erpnext/asset)
- [Purchasing an Asset](https://docs.frappe.io/erpnext/purchasing-an-asset)
- [Depreciation](https://docs.frappe.io/erpnext/asset-depreciation)
- [Asset Movement](https://docs.frappe.io/erpnext/asset-movement)
- [Asset Repair](https://docs.frappe.io/erpnext/asset-repair)
- [Asset Reports](https://docs.frappe.io/erpnext/asset-reports)
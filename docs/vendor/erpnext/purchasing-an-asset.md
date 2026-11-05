---
title: "Purchasing an Asset | ERPNext Documentation"
description: "Purchase and capitalize fixed assets in ERPNext using correctly configured Items, Purchase Receipts, and Purchase Invoices."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/purchasing-an-asset"
updated: "2026-08-15"
---

Let's say you're recording two purchases for Nova Industries: 50 phones that will be sold to customers and one packaging machine that the company will use for five years. The phones should increase inventory. The machine should become a fixed asset and its cost should be spread across the years in which it is used.



ERPNext handles this difference from the Item setup onward. When the machine is marked as a fixed asset and purchased correctly, ERPNext can create its Asset record, place its cost in the right account, and prepare its depreciation schedule.

## Before you begin

Create the [Asset Category](https://docs.frappe.io/erpnext/asset-category), its accounts, the [Asset Location](https://docs.frappe.io/erpnext/asset-location), the supplier, and a fixed-asset Item.

## Mark the Item as a fixed asset

1. Open or create the Item.
2. Enable **Is Fixed Asset**.
3. Select the Asset Category.
4. Enable **Auto Create Assets on Purchase** when every purchased unit should create an Asset automatically. Leave it disabled when the asset must be created or grouped manually.

![ERPNext Item marked as a fixed asset with an Asset Category](https://novacompanies.m.frappe.cloud/files/06-fixed-asset-item.png)

## Record the purchase

1. Create a [Purchase Invoice](https://docs.frappe.io/erpnext/purchase-invoice) or a [Purchase Receipt](https://docs.frappe.io/erpnext/purchase-receipt) for the fixed-asset Item.
2. Select the correct company and supplier.
3. Enter quantity, rate, and the intended asset location.
4. Submit the document. If auto creation is enabled, open the created Asset from the document links.
5. If auto creation is disabled, create the Asset and link the source purchase document.

## Review the Asset before submission

Check the location, purchase date, available-for-use date, quantity, net purchase amount, and depreciation settings. The Available for Use Date determines when depreciation can start.

![Purchased Asset details and depreciation controls in ERPNext](https://novacompanies.m.frappe.cloud/files/07-asset-core-details.png)

Review each Finance Book row before submission. The row is the source of the schedule for that reporting basis.

![Finance Book rows on an ERPNext Asset](https://novacompanies.m.frappe.cloud/files/08-asset-finance-books.png)

## What happens after submission

The Asset becomes part of the fixed-asset register. When CWIP accounting is enabled, ERPNext can move value from Capital Work in Progress to the Fixed Asset Account when the asset is capitalized or becomes available for use. Depreciation entries follow the active schedule rather than the purchase date alone.

## Troubleshooting

### The purchase posts to an expense or inventory account

Check **Is Fixed Asset**, the selected Asset Category, and the category's company accounts before submission.

### No Asset was created from the purchase

Check **Auto Create Assets on Purchase** on the Item. If it was intentionally disabled, create the Asset manually and preserve the purchase link.

### The depreciation schedule starts on the wrong date

Correct the Available for Use Date and Finance Book start date while the relevant records are still editable.

## Frequently asked questions

### Should I use Purchase Receipt or Purchase Invoice?

Use the document that matches your control flow. A Purchase Receipt proves physical receipt; a Purchase Invoice records the supplier liability. Some organizations use both.

### Can one purchase create multiple Assets?

In ERPNext, yes. Quantity and grouped-asset settings determine whether ERPNext creates individual assets or a grouped asset.

### Can I enter an asset already owned before ERPNext?

In ERPNext, yes. Create an [existing Asset](https://docs.frappe.io/erpnext/asset) and provide purchase value, opening accumulated depreciation, and booked depreciation count.

## Related topics

- [Asset Category](https://docs.frappe.io/erpnext/asset-category)
- [Asset Location](https://docs.frappe.io/erpnext/asset-location)
- [Asset](https://docs.frappe.io/erpnext/asset)
- [Purchasing an Asset](https://docs.frappe.io/erpnext/purchasing-an-asset)
- [Depreciation](https://docs.frappe.io/erpnext/asset-depreciation)
- [Asset Movement](https://docs.frappe.io/erpnext/asset-movement)
- [Asset Repair](https://docs.frappe.io/erpnext/asset-repair)
- [Asset Reports](https://docs.frappe.io/erpnext/asset-reports)
---
title: "Selling an Asset | ERPNext Documentation"
description: "Sell an ERPNext Asset, calculate gain or loss, and verify its disposal and ledger impact."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/selling-an-asset"
updated: "2026-08-15"
---

Imagine Nova Industries sells an old inspection camera for $1,500. The camera originally cost more, but part of that cost has already been recorded as depreciation. The accountant cannot treat the $1,500 like an ordinary product sale because the remaining asset value must also be removed.



Selling an Asset records the customer amount, removes the asset's cost and accumulated depreciation, and calculates the gain or loss. The Asset remains in the register with a **Sold** status so its history is not lost.

## Before you begin

Confirm the Asset is submitted, not already sold or scrapped, and that depreciation is posted up to the disposal date according to policy. Prepare the customer and disposal accounts.

## Create the sale

1. Open the Asset and use **Create &gt; Sales Invoice**, or create a [Sales Invoice](https://docs.frappe.io/erpnext/sales-invoice) and select the fixed-asset Item and Asset.
2. Enter the customer, posting date, Asset, quantity, and sale rate.
3. Review taxes and disposal accounts.
4. Submit the Sales Invoice.

![Asset selected before disposal through a Sales Invoice](https://novacompanies.m.frappe.cloud/files/07-asset-core-details.png)

## Verify the disposal

The Asset status becomes **Sold** and its disposal date is recorded. Review the Sales Invoice, Journal Entry or General Ledger to confirm receivable, asset cost, accumulated depreciation, and gain or loss.

![ERPNext Asset disposal status fields](https://novacompanies.m.frappe.cloud/files/21-asset-disposal-state.png)

Use the Fixed Asset Register to confirm the asset no longer appears as an active existing asset for the relevant date.

![Fixed Asset Register used to verify disposal](https://novacompanies.m.frappe.cloud/files/24-fixed-asset-register.png)

## Troubleshooting

### The Asset cannot be selected on the Sales Invoice

Confirm the Item is a fixed asset, the Asset is submitted and available, and the company matches.

### Gain or loss looks wrong

Check sale proceeds, disposal date, net book value, booked depreciation, taxes, and selected accounts.

## Frequently asked questions

### Should I create a normal sales item for the asset?

Use the fixed-asset Item and link the specific Asset so ERPNext can perform disposal accounting.

### Does selling cancel the Asset?

In ERPNext, no. It changes lifecycle status to Sold and preserves the history.

### Can I sell a partially depreciated asset?

In ERPNext, yes. Gain or loss is based on sale proceeds versus carrying value at disposal.

## Related topics

- [Asset Category](https://docs.frappe.io/erpnext/asset-category)
- [Asset Location](https://docs.frappe.io/erpnext/asset-location)
- [Asset](https://docs.frappe.io/erpnext/asset)
- [Purchasing an Asset](https://docs.frappe.io/erpnext/purchasing-an-asset)
- [Depreciation](https://docs.frappe.io/erpnext/asset-depreciation)
- [Asset Movement](https://docs.frappe.io/erpnext/asset-movement)
- [Asset Repair](https://docs.frappe.io/erpnext/asset-repair)
- [Asset Reports](https://docs.frappe.io/erpnext/asset-reports)
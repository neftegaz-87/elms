---
title: "Scrapping an Asset | ERPNext Documentation"
description: "Scrap an unusable ERPNext Asset and verify the write-off, status, and remaining book value."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/scrapping-an-asset"
updated: "2026-08-15"
---

Imagine a Nova Industries machine is damaged beyond repair and has no resale value. It is still shown in the accounts with some remaining value, so simply throwing it away would leave the books saying the company owns something that no longer exists.



Scrapping an Asset closes that gap. ERPNext marks the asset as scrapped, removes its remaining carrying value through the correct accounts, and keeps the disposal history for audit.

## Before you begin

Confirm the Asset is physically retired, approvals are complete, depreciation is current, and the correct loss or disposal account is configured. Scrapping is an accounting action, not a way to hide a missing asset.

## Scrap the Asset

1. Open the submitted Asset.
2. Use the **Scrap Asset** action.
3. Confirm the posting or disposal date.
4. Review the generated Journal Entry before final submission where the workflow allows.
5. Complete the action.

![Asset status and scrap Journal Entry fields](https://novacompanies.m.frappe.cloud/files/21-asset-disposal-state.png)

## Verify the write-off

The Asset status becomes **Scrapped**. The entry removes the remaining carrying value using the fixed-asset, accumulated depreciation, and loss accounts.

![Asset balances used to check carrying value before scrapping](https://novacompanies.m.frappe.cloud/files/23-asset-depreciations-balances-v2.png)

Confirm the Fixed Asset Register no longer treats the asset as active after the disposal date.

![Fixed Asset Register used after scrapping](https://novacompanies.m.frappe.cloud/files/24-fixed-asset-register.png)

## Troubleshooting

### The Scrap action is unavailable

Confirm the Asset is submitted, not already disposed, and has no blocking draft or submitted lifecycle documents.

### The write-off amount is unexpected

Reconcile capitalized value, booked depreciation, value adjustments, and the disposal date before proceeding.

## Frequently asked questions

### Is scrapping the same as selling for zero?

In ERPNext, no. Scrapping is a write-off workflow without customer proceeds.

### Can a fully depreciated asset be scrapped?

In ERPNext, yes. The remaining carrying value may be only the residual value, but status and disposal history still need to be closed correctly.

### Can a scrapped asset be used again?

Treat scrapping as a final disposal. Reverse only through the supported accounting correction process when the original action was genuinely wrong.

## Related topics

- [Asset Category](https://docs.frappe.io/erpnext/asset-category)
- [Asset Location](https://docs.frappe.io/erpnext/asset-location)
- [Asset](https://docs.frappe.io/erpnext/asset)
- [Purchasing an Asset](https://docs.frappe.io/erpnext/purchasing-an-asset)
- [Depreciation](https://docs.frappe.io/erpnext/asset-depreciation)
- [Asset Movement](https://docs.frappe.io/erpnext/asset-movement)
- [Asset Repair](https://docs.frappe.io/erpnext/asset-repair)
- [Asset Reports](https://docs.frappe.io/erpnext/asset-reports)
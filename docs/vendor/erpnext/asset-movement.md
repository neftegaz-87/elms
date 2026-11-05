---
title: "Asset Movement | ERPNext Documentation"
description: "Transfer, issue, or receive ERPNext Assets while preserving location and custody history."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/asset-movement"
updated: "2026-08-15"
---

Imagine a laptop moves from Nova Industries' head office to the service workshop, then is issued to a new employee. The problem with editing the location directly is that it would show only where the laptop is now. It would not explain who moved it or where it was before.



Asset Movement records every transfer, issue, and receipt as a separate event. The latest submitted movement updates the asset's location or custodian while keeping the earlier movements available as history.

## Choose the purpose


| Field                  | What it means                                                     |
| ---------------------- | ----------------------------------------------------------------- |
| **Transfer**           | Moves an asset from one location to another.                      |
| **Issue**              | Assigns custody to an employee.                                   |
| **Receipt**            | Returns an issued asset from an employee.                         |
| **Transfer and Issue** | Moves the asset and assigns it to an employee in one transaction. |


## Create an Asset Movement

1. Select the company and purpose.
2. Set the transaction date and time.
3. Add the Asset and its source details.
4. Enter the target location or employee required by the purpose.
5. Submit the movement.

![Asset transfer from Nova Headquarters to Service Workshop](https://novacompanies.m.frappe.cloud/files/14-asset-movement-transfer.png)

Use the pencil icon to review all source, target, employee, and department fields in the child row.

![Asset Movement child-row pencil icon](https://novacompanies.m.frappe.cloud/files/15-asset-movement-pencil.png)

## Verify the result

Open the Asset or Asset list and confirm the current location and status reflect the submitted movement.

![Asset list used to verify current locations](https://novacompanies.m.frappe.cloud/files/01-assets-overview-list.png)

## Troubleshooting

### The target location did not change

Confirm the Asset Movement was submitted and the correct Asset row was used.

### The movement asks for an employee

The selected purpose includes custody. Use Transfer when only the physical location changes.

## Frequently asked questions

### Can one movement contain several assets?

In ERPNext, yes. Add multiple rows when the assets share the same movement context.

### Does an Asset Movement affect the ledger?

In ERPNext, no. It changes custody and location, not asset value.

### Can I move an out-of-order asset?

Check the operational policy and linked repair state. The system record should match the real handoff.

## Related topics

- [Asset Category](https://docs.frappe.io/erpnext/asset-category)
- [Asset Location](https://docs.frappe.io/erpnext/asset-location)
- [Asset](https://docs.frappe.io/erpnext/asset)
- [Purchasing an Asset](https://docs.frappe.io/erpnext/purchasing-an-asset)
- [Depreciation](https://docs.frappe.io/erpnext/asset-depreciation)
- [Asset Movement](https://docs.frappe.io/erpnext/asset-movement)
- [Asset Repair](https://docs.frappe.io/erpnext/asset-repair)
- [Asset Reports](https://docs.frappe.io/erpnext/asset-reports)
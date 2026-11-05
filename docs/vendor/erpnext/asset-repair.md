---
title: "Asset Repair | ERPNext Documentation"
description: "Record ERPNext Asset failures, repair work, downtime, costs, consumed items, and capitalization decisions."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/asset-repair"
updated: "2026-08-15"
---

Imagine a Nova Industries inspection camera stops working. The team sends it to a repair vendor, pays for replacement parts, and receives it back three days later. The company needs to track the downtime and cost, and it must decide whether the repair is an expense or increases the asset's value.



Asset Repair records the failure, repair work, cost, and completion. It also connects qualifying capital repair costs to the asset when they extend its useful life or improve its capacity.

## Create an Asset Repair

1. Select the Asset and failure date.
2. Enter a clear description of the failure.
3. Save with status **Pending** while work is in progress.
4. Add supplier invoices or consumed stock items where applicable.
5. Record actions performed and completion date.

![Pending Asset Repair for a Nova Industries laptop](https://novacompanies.m.frappe.cloud/files/16-asset-repair-details.png)

## Record cost and capitalization

Routine repair is normally an expense. Enable **Capitalize Repair Cost** only when the cost meets the organization's capitalization policy and increases future economic benefit. If the repair extends useful life, enter the increase in asset life and review the depreciation schedule.

![Repair cost and capitalization fields in ERPNext](https://novacompanies.m.frappe.cloud/files/17-asset-repair-cost.png)

## Complete and verify

Set the repair to **Completed**, confirm downtime, and open the Asset. A pending failure can place the asset out of order; completion should restore the correct operating state.

![Asset status after repair workflow activity](https://novacompanies.m.frappe.cloud/files/01-assets-overview-list.png)

## Troubleshooting

### Repair cost remains zero

Link the relevant Purchase Invoices or consumed items and confirm their rates and amounts.

### The Asset remains Out of Order

Complete the repair and verify no other active repair keeps the asset unavailable.

### Capitalization did not update the schedule

Confirm the repair was submitted with capitalization enabled and review the linked value and schedule documents.

## Frequently asked questions

### Should every repair be capitalized?

In ERPNext, no. Capitalize only costs that meet the accounting policy. Routine repairs are usually expenses.

### Can repair consume stock items?

In ERPNext, yes. Add consumed parts so their cost is included and inventory is reduced through the supported workflow.

### Does Asset Repair replace maintenance logs?

In ERPNext, no. Maintenance logs record planned work. Repair records a failure and its financial or operational recovery.

## Related topics

- [Asset Category](https://docs.frappe.io/erpnext/asset-category)
- [Asset Location](https://docs.frappe.io/erpnext/asset-location)
- [Asset](https://docs.frappe.io/erpnext/asset)
- [Purchasing an Asset](https://docs.frappe.io/erpnext/purchasing-an-asset)
- [Depreciation](https://docs.frappe.io/erpnext/asset-depreciation)
- [Asset Movement](https://docs.frappe.io/erpnext/asset-movement)
- [Asset Repair](https://docs.frappe.io/erpnext/asset-repair)
- [Asset Reports](https://docs.frappe.io/erpnext/asset-reports)
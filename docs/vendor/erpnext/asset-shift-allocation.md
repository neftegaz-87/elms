---
title: "Asset Shift Allocation | ERPNext Documentation"
description: "Allocate ERPNext asset depreciation by machine shifts when utilization changes across periods."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/asset-shift-allocation"
updated: "2026-08-15"
---

Imagine a Nova Industries packaging machine runs one shift in January, three shifts in February, and two shifts in March. If the machine works harder in February, equal depreciation every month may not match how quickly the machine is being used up.



Asset Shift Allocation records the shifts worked during each period. ERPNext uses those allocations with shift-based depreciation so heavier use can produce more depreciation and lighter use can produce less.

## Before you begin

Enable **Shift Based** in the Asset's Finance Book row and confirm the configured shift factors follow the approved accounting policy.

![Asset Finance Book used for shift-based depreciation](https://novacompanies.m.frappe.cloud/files/09-production-asset-depreciation.png)

## Allocate a shift

1. Open **Asset Shift Allocation**.
2. Select the Asset and Finance Book.
3. Choose the shift and effective date range.
4. Save and submit the allocation.
5. Review the regenerated or affected schedule before depreciation is posted.

## Understand the result

The shift factor changes how much depreciation is assigned to the relevant period. It does not change the acquisition cost. The total schedule must still respect the residual value.

![Report used to verify depreciation after shift allocation](https://novacompanies.m.frappe.cloud/files/23-asset-depreciations-balances-v2.png)

## Troubleshooting

### The depreciation amount did not change

Confirm the Finance Book is shift based, the allocation covers the schedule date, and depreciation has not already been posted for that period.

### The asset is allocated to overlapping shifts

Correct the dates so only the intended shift applies to a given period.

## Frequently asked questions

### Should office laptops use shift allocation?

Usually no. It is most useful for production equipment whose usage is measured by shifts.

### Does a shift allocation create a ledger entry?

The allocation changes the depreciation basis. The ledger entry occurs when depreciation is posted.

### Can future shifts be planned?

In ERPNext, yes, but review them when operational schedules change.

## Related topics

- [Asset Category](https://docs.frappe.io/erpnext/asset-category)
- [Asset Location](https://docs.frappe.io/erpnext/asset-location)
- [Asset](https://docs.frappe.io/erpnext/asset)
- [Purchasing an Asset](https://docs.frappe.io/erpnext/purchasing-an-asset)
- [Depreciation](https://docs.frappe.io/erpnext/asset-depreciation)
- [Asset Movement](https://docs.frappe.io/erpnext/asset-movement)
- [Asset Repair](https://docs.frappe.io/erpnext/asset-repair)
- [Asset Reports](https://docs.frappe.io/erpnext/asset-reports)
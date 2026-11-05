---
title: "Asset Location | ERPNext Documentation"
description: "Build an ERPNext Asset Location tree and use it to track the physical position of company assets."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/asset-location"
updated: "2026-08-15"
---

Imagine a Nova Industries employee reports that a company laptop is missing. The Asset record proves that the company owns it, but the support team still needs to know whether it was last kept at Nova Headquarters, sent to the Service Workshop, or assigned to another office.



Asset Locations create a simple map of where company assets are kept. When the location is updated through an Asset Movement, the team can find equipment faster and can also see where it was kept earlier.

## Create the location tree

1. Open **Asset Location** in Tree view.
2. Create a group such as **Nova Facilities**.
3. Add operational locations such as **Nova Headquarters**, **Packaging Floor**, and **Service Workshop** below it.
4. Use [Asset Movement](https://docs.frappe.io/erpnext/asset-movement) when an asset changes location so the history remains auditable.

![ERPNext Asset Location tree for Nova Industries facilities](https://novacompanies.m.frappe.cloud/files/05-asset-location-tree.png)


| Field                      | What it means                                                                                                               |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **Location Name**          | The name users will select on Asset and Asset Movement records.                                                             |
| **Parent Location**        | The group under which the location appears.                                                                                 |
| **Is Group**               | Allows the location to contain child locations. Do not assign an asset to a broad group when a usable leaf location exists. |
| **Area and UOM**           | Optional physical area information.                                                                                         |
| **Latitude and Longitude** | Optional coordinates for map-based identification.                                                                          |


## Keep locations useful

Choose one consistent level of detail. For office assets, a site or floor may be enough. For production equipment, a line or work area may be more useful. When a site closes, move its assets first, then stop using the old location rather than erasing history.

## Troubleshooting

### A new location does not appear in the Link field

Confirm it is saved as a usable location and not only as an unintended group. Reload the form after changing the tree.

### The Asset still shows the old location

Submit the Asset Movement. Saving a draft movement does not complete the transfer.

## Frequently asked questions

### Is Asset Location the same as Warehouse?

In ERPNext, no. Warehouse tracks inventory quantities. Asset Location tracks the physical position of fixed assets.

### Can an asset be assigned to an employee and a location?

In ERPNext, yes. Asset Movement can track custody and location together, depending on the selected purpose.

### Does a location change affect the ledger?

In ERPNext, no. A location transfer is operational and does not change asset value.

## Related topics

- [Asset Category](https://docs.frappe.io/erpnext/asset-category)
- [Asset Location](https://docs.frappe.io/erpnext/asset-location)
- [Asset](https://docs.frappe.io/erpnext/asset)
- [Purchasing an Asset](https://docs.frappe.io/erpnext/purchasing-an-asset)
- [Depreciation](https://docs.frappe.io/erpnext/asset-depreciation)
- [Asset Movement](https://docs.frappe.io/erpnext/asset-movement)
- [Asset Repair](https://docs.frappe.io/erpnext/asset-repair)
- [Asset Reports](https://docs.frappe.io/erpnext/asset-reports)
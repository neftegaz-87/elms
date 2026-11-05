---
title: "Workstation Type"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/workstation_type"
updated: "2026-02-26"
---

If users have the same types of multiple Workstations (Machines) and users want to auto-assign jobs to the available workstation based on workstation type then this feature is the good option for them. A Workstation Type document will allow you to set the same operating cost to multiple operations by just setting the Workstation Type in the Operations table in [BOM](https://docs.frappe.io/erpnext/user/manual/en/bill-of-materials) or [Routing](https://docs.frappe.io/erpnext/user/manual/en/routing).

![](/files/CleanShot 2026-02-19 at 12.10.36@2x.png)

After adding Workstation Type, users has to assign the Workstation Type to the respective Workstation and set the Workstation Type to the respective Operation in the BOM.

![](/files/CleanShot 2026-02-19 at 12.11.38@2x.png)

After setting up Workstation Type when user make the Work Order with Operations system will create Job Cards against the Operation and set the available Workstation based on the Workstation Type set in the BOM.

![](/files/CleanShot 2026-02-19 at 12.13.04@2x.png)


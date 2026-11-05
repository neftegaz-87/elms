---
title: "Asset Maintenance Team | ERPNext Documentation"
description: "Create an ERPNext Asset Maintenance Team with a manager, members, and roles."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/asset-maintenance-team"
updated: "2026-08-15"
---

Imagine Nova Industries has electricians, IT technicians, and machine specialists. When a laptop or production machine needs work, assigning the wrong person wastes time and may leave the real problem unresolved.



An Asset Maintenance Team groups the people who can perform a type of maintenance. The team can then be selected on a maintenance plan so everyone knows who is responsible for each scheduled task.

## Create a team

1. Open **Asset Maintenance Team** and select **Add**.
2. Enter a team name and company.
3. Select a Maintenance Manager.
4. Add members and their maintenance roles.
5. Save, then use the team in [Asset Maintenance](https://docs.frappe.io/erpnext/asset-maintenance) plans.

![Nova Facilities Team in ERPNext Asset Maintenance](https://novacompanies.m.frappe.cloud/files/10-maintenance-team.png)


| Field                   | What it means                                                   |
| ----------------------- | --------------------------------------------------------------- |
| **Maintenance Manager** | User who supervises the plan.                                   |
| **Team Member**         | User who can be assigned maintenance work.                      |
| **Maintenance Role**    | Role used to describe or authorize the member's responsibility. |
| **Company**             | Company whose assets the team maintains.                        |


## Troubleshooting

### A user cannot be selected as a member

Confirm the User is enabled and has access to the relevant company and Assets records.

### Tasks are assigned to the wrong person

Correct the task's Assign To field. The team defines available ownership but each task controls its assignee.

## Frequently asked questions

### Can the same user be in more than one team?

In ERPNext, yes, when that reflects operational responsibility.

### Does the team itself create tasks?

In ERPNext, no. The Asset Maintenance plan creates scheduled tasks and logs using the selected team.

### Can teams be company specific?

In ERPNext, yes. Keep the selected company aligned with the Assets the team will maintain.

## Related topics

- [Asset Category](https://docs.frappe.io/erpnext/asset-category)
- [Asset Location](https://docs.frappe.io/erpnext/asset-location)
- [Asset](https://docs.frappe.io/erpnext/asset)
- [Purchasing an Asset](https://docs.frappe.io/erpnext/purchasing-an-asset)
- [Depreciation](https://docs.frappe.io/erpnext/asset-depreciation)
- [Asset Movement](https://docs.frappe.io/erpnext/asset-movement)
- [Asset Repair](https://docs.frappe.io/erpnext/asset-repair)
- [Asset Reports](https://docs.frappe.io/erpnext/asset-reports)
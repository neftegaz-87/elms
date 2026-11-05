---
title: "Asset Maintenance | ERPNext Documentation"
description: "Plan recurring preventive maintenance and calibration for ERPNext Assets."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/asset-maintenance"
updated: "2026-08-15"
---

Imagine a Nova Industries packaging machine needs inspection every month and a belt replacement every six months. If the team depends on memory, a missed service could stop production and cost much more than the maintenance itself.



Asset Maintenance turns those recurring jobs into a planned schedule. It records what must be done, how often it should happen, and who is responsible, helping the team service equipment before it fails.

## Before you begin

Enable **Maintenance Required** on the Asset and create an [Asset Maintenance Team](https://docs.frappe.io/erpnext/asset-maintenance-team).

## Create a maintenance plan

1. Select the Asset and Maintenance Team.
2. Add a task with its type, start date, periodicity, assignee, and description.
3. Mark whether a certificate is required.
4. Save the plan. ERPNext creates planned [Asset Maintenance Logs](https://docs.frappe.io/erpnext/asset-maintenance-log) for the schedule.

![Preventive maintenance plan for a Nova Industries laptop](https://novacompanies.m.frappe.cloud/files/11-asset-maintenance-plan.png)

Use the pencil icon to open the complete child-row editor when the grid hides task fields.

![Pencil icon for the Asset Maintenance task row](https://novacompanies.m.frappe.cloud/files/12-maintenance-task-pencil.png)

## Follow the work

Open the generated log, record actions performed, add a certificate when required, and mark the work completed.

![ERPNext Asset Maintenance Log list](https://novacompanies.m.frappe.cloud/files/13-maintenance-log-list.png)

## Troubleshooting

### No maintenance logs were created

Check the start date, end date, periodicity, and assignee, then save the maintenance plan again.

### The task is overdue

Complete or cancel the correct log. Do not only change the plan because the historical occurrence still needs a result.

## Frequently asked questions

### Is preventive maintenance the same as repair?

In ERPNext, no. Maintenance is planned work. Asset Repair records a failure, downtime, repair cost, and possible capitalization.

### Can one Asset have several tasks?

In ERPNext, yes. Add separate rows for checks, calibration, cleaning, or certification.

### Does maintenance affect asset value?

Routine maintenance normally does not. A qualifying repair cost can be capitalized through the repair workflow.

## Related topics

- [Asset Category](https://docs.frappe.io/erpnext/asset-category)
- [Asset Location](https://docs.frappe.io/erpnext/asset-location)
- [Asset](https://docs.frappe.io/erpnext/asset)
- [Purchasing an Asset](https://docs.frappe.io/erpnext/purchasing-an-asset)
- [Depreciation](https://docs.frappe.io/erpnext/asset-depreciation)
- [Asset Movement](https://docs.frappe.io/erpnext/asset-movement)
- [Asset Repair](https://docs.frappe.io/erpnext/asset-repair)
- [Asset Reports](https://docs.frappe.io/erpnext/asset-reports)
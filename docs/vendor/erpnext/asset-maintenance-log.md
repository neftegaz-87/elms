---
title: "Asset Maintenance Log | ERPNext Documentation"
description: "Complete ERPNext Asset Maintenance Logs with work performed, dates, status, and certificates."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/asset-maintenance-log"
updated: "2026-08-15"
---

Imagine a technician completes the monthly inspection of a Nova Industries packaging machine. The schedule says the work was due, but the company still needs proof of what was done, when it was completed, and whether the machine had a problem.



An Asset Maintenance Log records the actual maintenance event. It turns a planned task into a dated service history that the operations and audit teams can check later.

## Open the planned log

Use the Maintenance Log section of the [Asset Maintenance](https://docs.frappe.io/erpnext/asset-maintenance) record or open the Asset Maintenance Log list.

![Planned Asset Maintenance Logs in ERPNext](https://novacompanies.m.frappe.cloud/files/13-maintenance-log-list.png)

## Complete the log

1. Confirm the Asset, task, due date, and assignee.
2. Change status to **Completed** after the work is actually finished.
3. Enter the completion date and actions performed.
4. Attach the certificate when the task requires one.
5. Save the log and review the next due date on the maintenance plan.

![Maintenance plan linked to its recurring logs](https://novacompanies.m.frappe.cloud/files/11-asset-maintenance-plan.png)


| Field         | What it means                                                        |
| ------------- | -------------------------------------------------------------------- |
| **Planned**   | Work is scheduled but not complete.                                  |
| **Completed** | Work and required evidence have been recorded.                       |
| **Overdue**   | The due date passed without completion.                              |
| **Cancelled** | The occurrence will not be performed and the reason should be clear. |


## Troubleshooting

### The log cannot be marked complete

Check required completion date, certificate, and actions fields for the task.

### The next due date is wrong

Review the parent maintenance task's periodicity and the last completion date.

## Frequently asked questions

### Should I create logs manually?

Scheduled plans normally create them. Manual logs can be used for exceptional maintenance when the relationship remains clear.

### Can a completed log be edited?

Follow the document's edit rules and retain audit history. Do not overwrite evidence casually.

### Does a log post to the ledger?

In ERPNext, no. It is an operational record. Repair invoices or capitalized repair costs create accounting effects.

## Related topics

- [Asset Category](https://docs.frappe.io/erpnext/asset-category)
- [Asset Location](https://docs.frappe.io/erpnext/asset-location)
- [Asset](https://docs.frappe.io/erpnext/asset)
- [Purchasing an Asset](https://docs.frappe.io/erpnext/purchasing-an-asset)
- [Depreciation](https://docs.frappe.io/erpnext/asset-depreciation)
- [Asset Movement](https://docs.frappe.io/erpnext/asset-movement)
- [Asset Repair](https://docs.frappe.io/erpnext/asset-repair)
- [Asset Reports](https://docs.frappe.io/erpnext/asset-reports)
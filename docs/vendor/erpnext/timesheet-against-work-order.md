---
title: "Timesheet against Work Order"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/timesheet-against-work-order"
updated: "2026-07-05"
---

In ERPNext manufacturing, time spent on a Work Order is normally tracked through **Job Cards**. A Job Card is created for a Work Order operation and is used to record the employee, workstation, start time, end time, completed quantity, and operation time.

Timesheets are generally used for recording employee working hours against activities, projects, tasks, or billable work. They are useful for service and project-based tracking. For production operations, Job Cards are the standard document because they are directly connected to Work Orders and manufacturing operations.

## Recommended Flow

Use this flow when you want to record time against a Work Order:

1. Create and submit the **Work Order**.
2. Make sure the Work Order has operations defined in its routing or operations table.
3. Create **Job Cards** for the operations.
4. In the Job Card, record the employee, workstation, start time, end time, and completed quantity.
5. Submit the Job Card after the operation is completed.

The recorded time in the Job Card helps track actual manufacturing time against the planned operation time.

## When To Use Job Card

Use Job Cards when:

- Time is being recorded for a manufacturing operation.
- The work is linked to a Work Order.
- You want to track workstation time, operation time, and completed quantity.
- You want production progress to be reflected against the Work Order.

Job Cards are designed for manufacturing and are the best fit for Work Order execution.

## When To Use Timesheet

Use Timesheet when:

- Employees need to record general working hours.
- Work is tracked against a Project or Task.
- Hours are billable to a customer.
- The activity is service-oriented rather than a manufacturing operation.

If you need to track employee hours for production but do not need operation-level manufacturing tracking, Timesheet can still be used as an internal time record. However, it does not replace Job Card for Work Order operation tracking.

## Important Difference

The key difference is:

- **Work Order + Job Card** tracks manufacturing execution.
- **Timesheet** tracks employee time and billable or costing hours.

For manufacturing, use Job Cards to keep production data accurate. Use Timesheets only when the business also needs a separate employee time-tracking record.

## Common Checks

If you expected to create a Timesheet directly from a Work Order, check the following:

- Whether the requirement is actually to track operation time. If yes, use Job Card.
- Whether the Work Order has operations defined.
- Whether Job Cards have been created for the Work Order operations.
- Whether employees and workstations are selected on the Job Card.
- Whether the Job Card is submitted after work is completed.

## Summary

For Work Orders in ERPNext, use **Job Cards** to record manufacturing time. Use **Timesheets** when the purpose is employee time tracking, billing, or project/task-based work.

## Related Topics

- [Work Order](https://docs.frappe.io/erpnext/work-order)
- [Job Card](https://docs.frappe.io/erpnext/job-card)
- [Timesheet](https://docs.frappe.io/erpnext/timesheet)
- [BOM](https://docs.frappe.io/erpnext/bill-of-materials)
- [Routing](https://docs.frappe.io/erpnext/routing)
- [Workstation](https://docs.frappe.io/erpnext/workstation)
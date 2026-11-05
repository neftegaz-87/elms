---
title: "Timer in Timesheets"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/timer-in-timesheets"
updated: "2026-07-05"
---

The Timer in Timesheet helps users record actual working time without manually entering start and end times.

It is useful when employees work on project tasks, support work, consulting, internal activities, or any activity where the exact time spent needs to be captured.

## How The Timer Works

In a Timesheet, click **Start Timer** to open the Timer dialog.

The dialog lets you select:

- Activity Type
- Project
- Task
- Expected Hrs

When you start the timer, ERPNext creates a row in the Timesheet table with the current time as the **From Time**. The timer continues to count the elapsed time.

When you click **Complete**, ERPNext sets the **To Time**, calculates the total hours, and marks the row as completed.

## Starting A New Timer

To start a timer:

1. Create or open a draft Timesheet.
2. Click **Start Timer**.
3. Select the Activity Type.
4. Optionally select the Project and Task.
5. Enter Expected Hrs if you want ERPNext to alert you when the expected time is exceeded.
6. Click **Start**.

ERPNext adds the time log row and starts recording time.

## Completing The Timer

When the work is done, open the Timer and click **Complete**.

ERPNext will:

- Set the To Time.
- Calculate Hours.
- Mark the time log row as completed.
- Save the Timesheet.

You can then submit the Timesheet after reviewing the time logs.

## Resuming A Timer

If a Timesheet has an incomplete time log, ERPNext shows **Resume Timer** instead of Start Timer.

Use this when work was started earlier but not completed. ERPNext resumes the timer from the existing From Time and continues counting elapsed time.

## Expected Hours

Expected Hrs is optional. If it is entered, ERPNext can alert the user when the timer exceeds the expected duration.

This is helpful when work is planned for a fixed amount of time and users need a reminder when the planned time is exceeded.

## Billing And Costing

The timer records working hours. Billing and costing are handled through Timesheet fields such as:

- Is Billable
- Billing Hours
- Billing Rate
- Costing Rate

After the timer is completed, review these fields before submitting or billing the Timesheet.

## Common Checks

If the timer is not working as expected, check the following:

- The Timesheet is still in Draft state.
- An Activity Type is selected.
- The time log is not already completed.
- From Time and To Time are not overlapping with another Timesheet for the same user or employee.
- Project and Task are selected when the time needs to be tracked against a project.

## Summary

Use the Timesheet Timer when users need a simple start-and-stop way to record actual working time. It reduces manual entry, improves accuracy, and keeps time logs connected to the right Activity Type, Project, and Task.

## Related Topics

- [Timesheet](https://docs.frappe.io/erpnext/timesheet)
- [Project](https://docs.frappe.io/erpnext/project)
- [Task](https://docs.frappe.io/erpnext/task)
- [Activity Type](https://docs.frappe.io/erpnext/activity-type)
- [Sales Invoice](https://docs.frappe.io/erpnext/sales-invoice)
---
title: "Project Costing"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/project-costing"
updated: "2026-02-26"
---

Each project has multiple tasks associated with it. To track the actual cost of a Project, primarily in terms of services, a User has to create a Timesheet based on the time spent on a Task within a Project. You can track the service cost against a Project in the following ways.

## Activity Type

Activity Type is a master of services offered by your personnel. You can add a new Activity type from:

> Home > Projects > Activity Type > New

![Screenshot 2024-06-21 at 3.13.26 PM](/files/Screenshot 2024-06-21 at 3.13.26 PM.png)

## Activity Cost

Activity Cost is a master where you can track billing and costing rate for each Employee, for each Activity Type.

![](/files/Screenshot 2026-01-09 at 11.59.23 AM.png)

## Timesheet

Based on the time spent on the Project-Task, an Employee will create a Timesheet.

![](/files/Screenshot 2026-01-09 at 12.04.13 PM.png)

On selection of the Activity Type in the Time Log, Billing and Costing Rate will be fetched for that Employee from the respective Activity Cost.

Multiplying these rates with total no. of hours in the Time Log gives Costing Amount and Billing Amount for the specific Time Log.

## Costing in Project and Task

Based on all the Timesheets created for specific Tasks, its costing will be updated in the respective Task.

![](/files/Screenshot 2026-01-09 at 12.12.15 PM.png)

Same way, the Project cost will be updated based on Timesheets created against each of its associated tasks and the cost of the Project gets updated simultaneously.

![](/files/Screenshot 2026-01-09 at 12.49.27 PM.png)


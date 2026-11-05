---
title: "Material Requirements Planning (MRP)"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/material-requirements-planning-mrp"
updated: "2026-04-29"
---

The ERPNext currently have the MRP inside the production plan which is difficult for new users to understand and also it only uses sales order or material request data to generate the MRP.

## Purpose

The main purpose of MRP is to ensure that the right materials are available at the right time, helping the company to avoid the overproduction and delays in delivery. To know how MRP works first needs to understand how demand planning works.

## Demand Planning

We already had sales orders and material requests to generate demand planning. However, this only works for short-term MRP requirements and does not cover longer periods of time. To address this, we have added sales forecasting and delivery schedules to generate demand.

## Sales Forecast

The users has to manually enter the forecasting data by calculating it outside the system.

![](/files/sales%20forcast%20(1)

## Delivery Schedules

Some customers do not prefer a one time delivery against a sales order and they require multiple deliveries. The delivery schedules are very helpful for MRP because they provide visibility of when materials are actually needed, instead of assuming everything must be delivered at once.  
To make Delivery Schedules, users has to click on Add Schedule button in the sales order item table

![](/files/delivery_schedules.png)



## Master Production Schedule

To capture the demand for finished items, the Master Production Schedule (MPS) document was introduced. The system collects data from various sources such as sales orders, material requests, sales forecasts, and delivery schedules to generate the demand in the MPS.

![](/files/mps.png)

## Material Requirements Planning Report

The Material Requirements Planning (MRP) report calculates the required quantities of raw materials and components, along with the dates when they are needed, based on the demand for finished items.



![](/files/mrp_report.png)

Users can see the MRP report in the bucket view

![](/files/mrp-bucket.png)

## Item Lead Time

To calculate the dates of when to release the purchase order for raw materials and work order for components, the system needs to be aware of the lead time for manufacturing and the lead time for material procurement. For this purpose, a new document Item Lead Time was added.



![](/files/item-lead-time.png)


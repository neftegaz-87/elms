---
title: "Stock Reservation for Production Plan"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/stock-reservation-for-production-plan"
updated: "2026-02-19"
---


> Note: This feature will be available in the ERPNext version 16
> 
> 

Stock reservation in a production plan is important because it ensures that the required raw materials and sub-assemblies are available to start the manufacturing process. It also ensures that the purchased raw materials against the production plan are used exclusively for the respective production plan.

## How it Works in ERPNext 

The user activity diagram for the production plan reservation is shown below.


![](/files/Screenshot%202025-05-11%20at%203.58.41%20PM.png)


The user must enable the checkbox "Enable Stock Reservation" in the stock settings to use this feature. After enabling it, the checkbox "Reserve Stock" will appear in the Production Plan.

If the 'Reserve Stock' checkbox is selected, the system will automatically create a stock reservation entry for the sub-assembly items and raw materials if the stock exists.

If stock does not exist for the sub-assemblies or raw materials, the user must create work orders for the sub-assemblies and raise material requests (purchase) for the raw materials. Once the raw materials are purchased through these material requests, they will be automatically reserved against the respective production plan.

The materials reserved against the production plan will then be used for the work orders linked to that specific production plan.
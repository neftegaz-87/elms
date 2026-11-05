---
title: "Stock Reservation for Work Order\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/stock-reservation-for-work-order"
updated: "2026-02-19"
---


> Note: This feature will be available in the ERPNext version 16
> 
> 

Stock reservation for a work order is essential as it ensures that materials are available, enabling the manufacturing process to begin and produce finished goods.

It also helps to improve inventory management and ensures timely fulfillment of customer orders.

## How it Works in ERPNext

The user must enable the checkbox "Enable Stock Reservation" in the stock settings to use this feature. After enabling it, the checkbox "Reserve Stock" will appear in the work order.

If the "Reserve Stock" checkbox is selected, the system will automatically create a stock reservation entry against the source warehouse for the available stock upon submission of the work order.


![](/files/Screenshot%202025-01-28%20at%202.46.07%20PM.png)

The reserved stock can only be used for the respective work order and cannot be used in any other transactions.

## Unreserve Stock

If the reserved stock needs to be assigned to another work order, unreserve it from the current work order and assign it to the work order that does not have stock reserved.

![](/files/Screenshot%202025-01-28%20at%202.47.58%20PM.png)


## Reservation for WIP

Once the user transfers the materials from the source warehouse to the WIP warehouse using a stock entry with the type "Material Transfer for Manufacture", the system unreserves the stock from the source warehouse and reserves it against the WIP warehouse.

## Finished Goods Reservation

If the sales order is linked to the work order, the system reserves the finished goods against the respective sales order upon completion of the work order.
---
title: "Stock Closing Entry"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/stock-closing-entry"
updated: "2026-02-25"
---

The purpose of the stock closing entry is to generate the stock closing balance, which includes 
the consolidated stock quantity and consolidated stock value for the selected period. This information will be used to generate the stock reports such as Stock Balance and Batch-Wise Balance History in a short span of time.

## How it Works

The user is required to create a stock closing entry for the desired period, which can span one month, half a month, or an entire year. Upon submission of the stock closing entry, the system generates the stock closing balance for the selected period, including item, batch, inventory dimensions and warehouse wise consolidated closing stock quantities and stock values.

Stock Closing Entry

![](/files/stock-closing-entry.png)

Stock reports, such as Stock Balance and Batch-Wise Balance History, use the Stock Closing Balance data to calculate the opening stock, which is significantly faster than calculating the closing stock using the Stock Ledger Entry.


Note: Will be available in v16
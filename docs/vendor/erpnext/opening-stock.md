---
title: "Opening Stock"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/opening-stock"
updated: "2026-03-06"
---

**Opening Stock is the amount and value of materials that a company has available for sale or use at the beginning of an accounting period.**

The closing Stock of the previous accounting period becomes the opening Stock of the current accounting period.

## 1. Prerequisites

- Create [Warehouses](/erpnext/warehouse).
- Link Warehouse to the appropriate accounting ledgers.

## 2. Opening Stock for Non-serialised Items

To post opening stock, visit the [Stock Reconciliation](/erpnext/stock-reconciliation) page.

## 3. Opening Stock for Serialised and Batched Items

Create the [Batch](/erpnext/batch) and [Serial No](/erpnext/serial-no) records beforehand. To post opening stock for serialised and batched items:

1. Go to **Stock > Stock Transactions > Stock Entry > New**.
2. Select 'Material Receipt' in 'Stock Entry Type'.
3. Set `Is Opening`as `Yes`.
4. Select the Warehouse in 'Default Target Warehouse'.
5. In the Items table, select Item Code, Qty and Basic rate.
6. For batched items, select Batch No.
7. For serialised items, select Serial No.
8. Save and Submit.



### 5. Related Topics

1. [Accounting Of Inventory Stock](/erpnext/accounting-of-inventory-stock)
2. [Stock Entry](/erpnext/stock-entry)
3. [Stock Reconciliation](/erpnext/stock-reconciliation)


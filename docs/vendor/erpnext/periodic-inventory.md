---
title: "Periodic Inventory"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/periodic-inventory"
updated: "2026-02-20"
---

If you enable Perpetual Inventory in the Company master, the system will automatically create the GL entries for stock transactions. However, if Perpetual Inventory is disabled for your company, you will need to manually create periodic accounting entries.

To make a periodic accounting entry, you must create a Journal Entry manually. For the calculations, you need to compare the closing balance in the Stock Balance Report with the Trial Balance report for stock asset accounts. This process takes time, as it requires verifying and matching the differences in closing balances.

To address this in Version 16, we introduced a new Journal Entry type called 'Periodic Accounting Entry'. With this, users don’t need to perform manual calculations. The system will automatically fetch the difference in balance when the user clicks the 'Get Balance' button.



![](/files/periodic_accounting_entry5adb27.png)
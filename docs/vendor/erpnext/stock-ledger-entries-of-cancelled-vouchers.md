---
title: "Stock Ledger Entries of Cancelled Vouchers"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/stock-ledger-entries-of-cancelled-vouchers"
updated: "2026-10-06"
---

![](/files/Screenshot 2026-10-05 at 11.32.14 PM (1).webp)

Sometimes, a voucher is cancelled, but its Stock Ledger Entries are still not cancelled. This can happen because of a customization or an old issue in the core system.

This report shows all such Stock Ledger Entries where the voucher is already cancelled, but the Stock Ledger Entry is still active.

You can use this report to fix these entries.

Select the entries you want to fix and click **“Cancel Stock Ledger Entries”**. The system will cancel the selected Stock Ledger Entries and create reposting entries for the same item and warehouse.

After the cancellation and reposting are complete, your stock balance may change.

### Example

Suppose you have **50 Water Bottles** in stock.

You find one incorrect Stock Ledger Entry for **5 Water Bottles** and fix it using **“Cancel Stock Ledger Entries”**.

After the fix and reposting are complete, your stock will show **45 Water Bottles** instead of 50.
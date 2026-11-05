---
title: "Purpose of Stock Delivered But Not Billed"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/purpose-of-stock-delivered-but-not-billed"
updated: "2026-07-02"
---

## Stock Delivered but Not Billed

The **Stock Delivered but Not Billed** account is an adjustment account used to record the value of delivered items before a bill has been raised. Rather than debiting an expense account directly at the time of delivery, the system routes the entry through this intermediate account to keep the sales cycle accounting clean and consistent.

The balance in this account at any point represents the value of items for which Delivery Notes have been submitted, but Sales Invoices have not yet been raised.

### How It Works

![](/files/Delivery Note to Sales Invoice.mp4)



**On Delivery Note submission:** The warehouse's **Stock In Hand** account is credited, and the full stock value is debited to the **Stock Delivered but Not Billed** account.

*Example: A Delivery Note worth ₹400 → Stock In Hand credited ₹400, Stock Delivered but Not Billed debited ₹400.*

**On Sales Invoice submission:** The **Stock Delivered but Not Billed** account is credited as a reversal, and the **Cost of Goods Sold (COGS)** account is debited for the same amount.

*Example: Sales Invoice raised for ₹400 → Stock Delivered but Not Billed credited ₹400, COGS debited ₹400.*

![](/files/Screenshot 2026-07-02 at 12.30.00 PM.webp)

### Configuration

- The Stock Delivered but Not Billed account can be configured at the **Company** level using **Enable Stock Delivered But Not Billed** check.
- To exclude this account from Sales Return entries, enable the **Disable Stock Delivered but Not Billed in Sales Return** checkbox in the Company.

### Backdated Entries and Reposting

If a backdated entry changes the valuation rate on a Delivery Note, the system automatically updates the billed value on the corresponding Sales Invoice through reposting. This ensures that the accounting entries across the Delivery Note and Sales Invoice remain consistent throughout the entire sales cycle.
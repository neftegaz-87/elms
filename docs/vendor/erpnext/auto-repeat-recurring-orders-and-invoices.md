---
title: "Auto Repeat Recurring Orders and Invoices | ERPNext Documentation"
description: "Schedule ERPNext to create recurring orders, invoices, journals, and other enabled documents from a reference transaction."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/auto-repeat-recurring-orders-and-invoices"
updated: "2026-08-14"
---

Nova Industries bills Northstar Retail, a customer with a monthly device-support contract, on the first day of every month. Recreating the same Sales Invoice by hand risks missed billing and inconsistent terms. Auto Repeat uses an approved source document as a template and creates new orders or invoices on a schedule.



Use Auto Repeat for stable recurring transactions. Use [Subscription](/erpnext/subscription) when the agreement is plan-driven and needs subscription dates, plan quantities, trials, or subscription lifecycle controls.

## Before you begin

- Review the source party, company, items, rates, taxes, payment terms, dimensions, and addresses.
- Decide whether generated documents should stay in Draft for review or submit automatically.
- Confirm who should receive email and which print format should be attached.

## Create the Auto Repeat

1. Open **Auto Repeat** and create a new record.
2. Select the Reference Document Type and the exact order or invoice to repeat.
3. Set the start date and, when the agreement ends, an end date.
4. Enable Submit on Creation only when the generated transaction needs no manual review.

![Auto Repeat reference document and creation settings](https://novacompanies.m.frappe.cloud/files/sales-receivables-auto-repeat-recurring-orders-and-invoices-auto-repeat-details.png)



## Set the schedule

Choose the frequency and the relevant schedule options. For monthly billing, set the expected day or use the last day of the month when that matches the contract.

![Auto Repeat schedule for a recurring invoice](https://novacompanies.m.frappe.cloud/files/sales-receivables-auto-repeat-recurring-orders-and-invoices-auto-repeat-schedule.png)



## Monitor generated documents

Review the next scheduled date and the generated documents. Prices, taxes, addresses, and contract terms can change after the source was approved, so keep a review owner even when creation is automated.

## Troubleshooting

### No document was generated

Check that Auto Repeat is enabled, the start and end dates include today, the schedule is complete, the reference document is valid, and background jobs are running.

### The generated document has old commercial terms

Update the reference document or create a new approved source and point Auto Repeat to it. Do not assume changes in related masters will safely update every copied field.

## Frequently asked questions

### Can it repeat both orders and invoices?

Use supported Sales Orders, Purchase Orders, Sales Invoices, and Purchase Invoices as reference documents. Verify the current DocType’s Auto Repeat support before relying on it.

### Should I enable automatic submission?

Use it only for stable, low-risk transactions with tested taxes and controls. Draft creation is safer when a person must review each cycle.

## Related topics

- [Accounting overview](/erpnext/accounting/introduction)
- [Chart of Accounts](/erpnext/chart-of-accounts)
- [General Ledger](/erpnext/general-ledger)
- [Fiscal Year](/erpnext/fiscal-year)
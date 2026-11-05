---
title: "Post Dated Cheque Entry | ERPNext Documentation"
description: "Record and clear post-dated checks without recognizing bank settlement too early in ERPNext."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/post-dated-cheque-entry"
updated: "2026-08-01"
---

A post-dated check is received or issued before the date on which it can be deposited. Record it with its reference date and use a clearing account when your accounting policy requires settlement to be recognized only after the bank clears it.

## Before you begin

Confirm the correct Company, currency, receivable or payable account, and bank or cash ledger. Use submitted source documents and keep the bank reference or remittance advice available.

## Use Post Dated Cheque Entry

1. Create the Payment Entry with the check number and future reference date.
2. Use the configured post-dated check or clearing account when required.
3. Submit only according to your approval and accounting policy.
4. After the bank clears the check, transfer or reconcile the amount to the bank account.
5. If it is returned or becomes stale, reverse it through the approved process.

![Post Dated Cheque Entry in ERPNext](https://novacompanies.m.frappe.cloud/files/payments-04-payment-entry-party-amount.png)

## Important fields and what they mean


| Field                 | What it controls                                   |
| --------------------- | -------------------------------------------------- |
| Reference No          | Check number.                                      |
| Reference Date        | Date printed on the check.                         |
| Posting Date          | Accounting date of the entry.                      |
| Paid From and Paid To | Party and clearing or bank accounts.               |
| Clearance Date        | Actual settlement date used during reconciliation. |


## What happens after you submit or process

ERPNext updates the relevant accounting records and, where applicable, the outstanding or unallocated amounts. Review the General Ledger, party ledger, and source document status before treating the workflow as complete. A saved draft does not affect the ledger.

## Troubleshooting

### The cheque affects the ledger earlier than expected

Posting Date controls the General Ledger date. Reference Date records the cheque date but does not move the accounting entry. Follow the documented clearing-account workflow when recognition and bank clearance occur at different times.

### The cheque is missing from Bank Reconciliation

Confirm that the submitted entry uses the selected bank account and has not already been cleared. Check the reconciliation date range and bank clearance status.

### A post-dated cheque was dishonoured

Reverse or cancel it using the approved workflow so the invoice becomes outstanding again, and record bank charges separately when applicable. Preserve the cheque reference and dishonour evidence.

## Frequently asked questions

### What is the difference between Posting Date, Reference Date, and Clearance Date?

Posting Date determines the ledger period. Reference Date records the cheque or bank reference date. Clearance Date records when the bank actually cleared it.

### Can a post-dated cheque remain in draft until it clears?

A draft does not affect the ledger or invoice outstanding amount. Use this only when it matches your accounting policy; otherwise use a clearing account workflow that records receipt without treating the bank as cleared.

### Does setting a Clearance Date change the original ledger date?

It does not. The clearance date supports bank reconciliation while the original posting remains on its Posting Date.

### How can future cheque obligations be reported?

Use consistent cheque references, dates, clearing accounts, and reports. Add a controlled custom report only when standard views do not meet the operational requirement.

## Related topics

- [Payment Entry](/erpnext/payment-entry)
- [Payment Reconciliation](/erpnext/payment-reconciliation)
- [Bank Reconciliation](/erpnext/bank-reconciliation)
- [Bank Transaction](/erpnext/bank-transaction)
- [Journal Entry](/erpnext/journal-entry)
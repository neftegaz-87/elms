---
title: "Invoice Discount in Payment Entry | ERPNext Documentation"
description: "Record a settlement discount while clearing an ERPNext invoice."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/managing-invoice-discount-in-the-payment-entry"
updated: "2026-08-01"
---

When a Customer pays less because an approved settlement discount applies, allocate the amount received and record the discount in the Deductions or Loss table. This clears the invoice without hiding the difference.

## Before you begin

Confirm the correct Company, currency, receivable or payable account, and bank or cash ledger. Use submitted source documents and keep the bank reference or remittance advice available.

## Use Invoice Discount in Payment Entry

1. Create a Receive Payment Entry and fetch the invoice.
2. Enter the amount received in the bank.
3. Allocate the full amount being settled against the invoice.
4. Add the discount difference with the approved discount account and Cost Center.
5. Confirm that the Difference Amount is zero, then submit.

![Invoice Discount in Payment Entry in ERPNext](https://novacompanies.m.frappe.cloud/files/payments-05-payment-entry-references.png)

## Important fields and what they mean


| Field              | What it controls                              |
| ------------------ | --------------------------------------------- |
| Allocated Amount   | Invoice amount cleared by the payment.        |
| Paid Amount        | Cash actually received.                       |
| Deductions or Loss | Accounting rows explaining the shortfall.     |
| Account            | Approved discount allowed account.            |
| Cost Center        | Business unit receiving the discount expense. |


## What happens after you submit or process

ERPNext updates the relevant accounting records and, where applicable, the outstanding or unallocated amounts. Review the General Ledger, party ledger, and source document status before treating the workflow as complete. A saved draft does not affect the ledger.

## Troubleshooting

### The invoice remains outstanding after recording a discount

The cash received plus the approved discount must equal the amount being settled. Allocate the full settlement and post the discount to the configured discount allowed or received account.

### Difference Amount increases when the discount is entered

Check whether the discount should be added or deducted for the Payment Type. Verify the paid amount, received amount, and allocated amount before changing the sign.

### The discount posts to the wrong profit and loss account

Select the correct account for discount allowed or discount received and include the required Cost Center. Do not use a generic write-off account when separate reporting is required.

## Frequently asked questions

### Is a settlement discount the same as changing the invoice price?

It is not the same. The original invoice remains the commercial and tax document; the settlement difference is recorded when payment is received or made.

### Should tax be recalculated when a payment discount is granted?

Tax treatment varies by jurisdiction and discount type. Use the appropriate credit note or regional process when tax must change instead of relying only on a Payment Entry deduction.

### Can only part of an invoice receive a discount?

A partial settlement can include a supported discount, but the remaining invoice balance must be intentional and explainable. Verify the outstanding amount after submission.

### Can discounts allowed and received use different accounts?

Separate accounts are recommended when financial reporting distinguishes customer discounts from supplier discounts.

## Related topics

- [Payment Entry](/erpnext/payment-entry)
- [Payment Reconciliation](/erpnext/payment-reconciliation)
- [Bank Reconciliation](/erpnext/bank-reconciliation)
- [Bank Transaction](/erpnext/bank-transaction)
- [Journal Entry](/erpnext/journal-entry)
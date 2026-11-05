---
title: "Additional Charges in Payment | ERPNext Documentation"
description: "Record bank fees, withholding, write-offs, and other payment differences in ERPNext."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/handing-deductions-in-payment-entry"
updated: "2026-08-01"
---

A payment can differ from an invoice because of bank charges, withholding, exchange differences, or an approved write-off. Record each difference explicitly in the Deductions or Loss table instead of changing the invoice value.

## Before you begin

Confirm the correct Company, currency, receivable or payable account, and bank or cash ledger. Use submitted source documents and keep the bank reference or remittance advice available.

## Use Additional Charges in Payment

1. Enter the actual amount paid or received.
2. Allocate the intended amount against the invoice references.
3. Open **Deductions or Loss** and add one row for each difference.
4. Select the correct ledger, amount, Cost Center, and explanation.
5. Confirm that the Difference Amount is zero and submit.

![Additional Charges in Payment in ERPNext](https://novacompanies.m.frappe.cloud/files/payments-05-payment-entry-references.png)

## Important fields and what they mean


| Field                 | What it controls                                          |
| --------------------- | --------------------------------------------------------- |
| Account               | Ledger that explains the charge or deduction.             |
| Cost Center           | Required reporting dimension for the amount.              |
| Amount                | Signed value needed to balance the Payment Entry.         |
| Difference Amount     | Balance still unexplained.                                |
| Exchange Gain or Loss | Difference caused by currency conversion when applicable. |


## What happens after you submit or process

ERPNext updates the relevant accounting records and, where applicable, the outstanding or unallocated amounts. Review the General Ledger, party ledger, and source document status before treating the workflow as complete. A saved draft does not affect the ledger.

## Troubleshooting

### Difference Amount is not zero after adding a deduction

Confirm the actual bank amount, invoice allocation, and whether the deduction should be added or subtracted. The allocated amount commonly represents the amount clearing the invoice, while the bank amount reflects cash movement.

### A bank charge was posted as a tax

Use **Deductions or Losses** with the bank charges account. Taxes and Charges is for amounts connected to the party transaction, not a fee retained by the bank.

### A deduction unexpectedly changes the customer or supplier balance

Review the account head and whether it is a party receivable or payable account. Deductions such as fees, withholding, discounts, and exchange differences require different ledger accounts.

## Frequently asked questions

### Which differences belong in Deductions or Losses?

Common examples include bank charges, exchange gains or losses, write-offs, withholding, and approved settlement differences. Each line should have an explicit account and business explanation.

### Should the source invoice be edited to match the payment?

Keep a valid submitted invoice unchanged. Record the actual payment and account for the legitimate difference in the Payment Entry or another supported adjustment.

### Can several deductions be recorded in one Payment Entry?

Several lines can be used when the settlement contains distinct components. Use separate accounts so the ledger and audit trail remain clear.

### Can deductions be negative?

Use signs and Add or Deduct behavior only according to the field's accounting logic. Preview the ledger impact because a negative amount can reverse the intended account effect.

## Related topics

- [Payment Entry](/erpnext/payment-entry)
- [Payment Reconciliation](/erpnext/payment-reconciliation)
- [Bank Reconciliation](/erpnext/bank-reconciliation)
- [Bank Transaction](/erpnext/bank-transaction)
- [Journal Entry](/erpnext/journal-entry)
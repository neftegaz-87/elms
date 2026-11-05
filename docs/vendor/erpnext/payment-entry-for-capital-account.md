---
title: "Payment Entry for Capital Account | ERPNext Documentation"
description: "Record owner or shareholder capital introduced into ERPNext bank or cash accounts."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/payment-entry-for-capital-account"
updated: "2026-08-01"
---

Use an internal transfer or a suitable accounting entry when an owner or shareholder contributes capital. The correct method depends on whether the contributor is maintained as a party and how the equity account is configured.

## Before you begin

Confirm the correct Company, currency, receivable or payable account, and bank or cash ledger. Use submitted source documents and keep the bank reference or remittance advice available.

## Use Payment Entry for Capital Account

1. Confirm the equity or capital ledger with your accountant.
2. Create a Payment Entry when the transfer fits the supported party or internal-transfer flow.
3. Set the bank or cash account receiving the money and the capital account as the counterpart.
4. Enter the bank reference and posting date.
5. Submit and verify the General Ledger.

![Payment Entry for Capital Account in ERPNext](https://novacompanies.m.frappe.cloud/files/payments-04-payment-entry-party-amount.png)

## Important fields and what they mean


| Field                 | What it controls                                |
| --------------------- | ----------------------------------------------- |
| Paid From             | Capital or source account.                      |
| Paid To               | Company bank or cash account receiving funds.   |
| Party                 | Shareholder or other supported party when used. |
| Amount                | Capital introduced.                             |
| Reference No and Date | Bank evidence for the contribution.             |


## What happens after you submit or process

ERPNext updates the relevant accounting records and, where applicable, the outstanding or unallocated amounts. Review the General Ledger, party ledger, and source document status before treating the workflow as complete. A saved draft does not affect the ledger.

## Troubleshooting

### The shareholder or partner is not available as a party

Create the supported party master and confirm the user's permissions. Do not substitute a Supplier or Customer merely to make the transaction selectable.

### The contribution was posted as sales income

Use the correct equity or capital account. Owner contributions and withdrawals are financing transactions, not customer revenue or supplier expense.

### The Payment Entry does not balance

Check the bank or cash account, capital account, party type, amount, and currency. Obtain accounting advice before using a temporary receivable or payable account as a workaround.

## Frequently asked questions

### Is owner capital recorded with a Receive Payment Entry?

A cash contribution commonly debits bank and credits the appropriate capital or equity account. Configure the exact accounts according to the legal entity and accounting policy.

### How is an owner's withdrawal recorded?

Use an approved payment or Journal Entry against the owner's drawings or capital account. Do not record it as an operating expense unless it genuinely is one.

### Can capital contributions be allocated to invoices?

Capital is not normally a customer or supplier settlement. Keep it separate from receivable and payable allocations.

### Should every shareholder have a separate capital account?

Use the account structure required for ownership reporting and local compliance. Separate ledgers can improve traceability, but confirm the design with your accountant.

## Related topics

- [Payment Entry](/erpnext/payment-entry)
- [Payment Reconciliation](/erpnext/payment-reconciliation)
- [Bank Reconciliation](/erpnext/bank-reconciliation)
- [Bank Transaction](/erpnext/bank-transaction)
- [Journal Entry](/erpnext/journal-entry)
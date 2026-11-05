---
title: "Single Payment Against Multiple Invoices | ERPNext Documentation"
description: "Allocate one ERPNext payment across several customer or supplier invoices."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/single-payment-multiple-invoices"
updated: "2026-08-01"
---

A single bank receipt or payment can settle several invoices. Keep it as one Payment Entry and use the References table to show exactly how the amount is distributed.

## Before you begin

Confirm the correct Company, currency, receivable or payable account, and bank or cash ledger. Use submitted source documents and keep the bank reference or remittance advice available.

## Use Single Payment Against Multiple Invoices

1. Create the Payment Entry for the correct party.
2. Enter the actual bank amount and reference.
3. Fetch outstanding invoices.
4. Select the invoices included in the remittance and set each allocation.
5. Record any discount, fee, withholding, or exchange difference explicitly.
6. Confirm totals and submit.

![One ERPNext Payment Entry allocated across two Sales Invoices](https://novacompanies.m.frappe.cloud/files/docs-single-payment-multiple-invoices-v2.png)

## Important fields and what they mean


| Field                  | What it controls                                 |
| ---------------------- | ------------------------------------------------ |
| Outstanding Amount     | Balance available to clear on each invoice.      |
| Allocated Amount       | Portion of this payment assigned to the invoice. |
| Total Allocated Amount | Sum across references.                           |
| Unallocated Amount     | Payment balance left for later allocation.       |
| Difference Amount      | Amount that requires an accounting explanation.  |


## What happens after you submit or process

ERPNext updates the relevant accounting records and, where applicable, the outstanding or unallocated amounts. Review the General Ledger, party ledger, and source document status before treating the workflow as complete. A saved draft does not affect the ledger.

## Troubleshooting

### Selecting rows does not update the Paid Amount

Enter the actual payment amount, retain the intended invoice references, and set each Allocated Amount. Row selection alone is not a request to recalculate the bank amount.

### The total allocation exceeds the payment

Reduce one or more allocations so the total does not exceed the amount available. Leave unpaid invoice balances outstanding rather than changing their totals.

### One invoice is missing

Check that all references belong to the same party, Company, receivable or payable account, and compatible currency. Confirm submission status and remaining outstanding amount.

## Frequently asked questions

### Can one payment settle both Sales Invoices and credit notes?

Use only reference types supported by the current allocation dialog and confirm the net effect. Reconcile complex credit scenarios carefully and verify the party ledger.

### Can invoices for different customers share one Payment Entry?

A standard Payment Entry has one party. Record separate entries per Customer and reconcile them to a combined bank deposit if necessary.

### Can the payment partially settle every selected invoice?

Enter a partial Allocated Amount for each reference. ERPNext leaves the remaining balances outstanding.

### Which invoice should be allocated first?

Follow remittance advice. Without it, apply the company's documented policy, such as oldest due first, and retain evidence of the decision.

## Related topics

- [Payment Entry](/erpnext/payment-entry)
- [Payment Reconciliation](/erpnext/payment-reconciliation)
- [Bank Reconciliation](/erpnext/bank-reconciliation)
- [Bank Transaction](/erpnext/bank-transaction)
- [Journal Entry](/erpnext/journal-entry)
---
title: "Reconcile Advance Payment Made to the Supplier | ERPNext Documentation"
description: "Allocate a supplier advance to later Purchase Invoices in ERPNext."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/reconcile-advance-payment-made-to-the-supplier"
updated: "2026-08-01"
---

A Supplier advance remains unallocated until the Purchase Invoice is posted. Reconcile the advance against the invoice so the Supplier balance and outstanding amount are correct.

## Before you begin

Confirm the correct Company, currency, receivable or payable account, and bank or cash ledger. Use submitted source documents and keep the bank reference or remittance advice available.

## Use Reconcile Advance Payment Made to the Supplier

1. Confirm that the advance Payment Entry is submitted and still unallocated.
2. Open Payment Reconciliation and select Supplier and the relevant Supplier.
3. Load the unallocated advance and outstanding Purchase Invoice.
4. Enter the amount to allocate and reconcile.
5. Verify the Purchase Invoice outstanding amount and Supplier ledger.

![Reconcile Advance Payment Made to the Supplier in ERPNext](https://novacompanies.m.frappe.cloud/files/payments-11-payment-reconciliation.png)

## Important fields and what they mean


| Field               | What it controls                         |
| ------------------- | ---------------------------------------- |
| Unallocated Payment | Advance available for allocation.        |
| Purchase Invoice    | Supplier invoice receiving the advance.  |
| Allocated Amount    | Amount linked during reconciliation.     |
| Posting Date        | Date used for the reconciliation effect. |
| Difference          | Balance remaining after allocation.      |


## What happens after you submit or process

ERPNext updates the relevant accounting records and, where applicable, the outstanding or unallocated amounts. Review the General Ledger, party ledger, and source document status before treating the workflow as complete. A saved draft does not affect the ledger.

## Troubleshooting

### The supplier advance is not available

Confirm that the Payment Entry is submitted, belongs to the same Supplier and Company, uses a compatible payable or configured advance account, and still has an unallocated balance.

### The Purchase Invoice does not fetch the advance

Check whether the invoice was created from the Purchase Order referenced by the advance. For an already submitted invoice, use Payment Reconciliation instead of the draft invoice's advance table.

### The supplier has several advances and the wrong one was selected

Compare reference numbers, dates, Orders, currencies, and unallocated amounts before processing. Unreconcile and reallocate through the supported workflow when necessary.

## Frequently asked questions

### Must a supplier advance be linked to a Purchase Order?

It can remain unallocated against the Supplier, but linking the relevant Purchase Order improves traceability and downstream matching.

### Can one supplier advance settle several invoices?

It can be allocated in parts across eligible invoices for the same Supplier and compatible account.

### What happens when the final invoice is smaller than the advance?

Allocate only the invoiced amount. The remainder stays as supplier credit until it is applied to another invoice or refunded.

### Can an advance posted to a separate asset account be reconciled?

Use the supported separate party account configuration. A manual entry to an unrelated asset account will not automatically appear in standard payment reconciliation.

## Related topics

- [Payment Entry](/erpnext/payment-entry)
- [Payment Reconciliation](/erpnext/payment-reconciliation)
- [Bank Reconciliation](/erpnext/bank-reconciliation)
- [Bank Transaction](/erpnext/bank-transaction)
- [Journal Entry](/erpnext/journal-entry)
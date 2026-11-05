---
title: "Stale Cheque Accounting | ERPNext Documentation"
description: "Reverse or replace an expired check while preserving the ERPNext audit trail."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/stale-cheque-accounting"
updated: "2026-08-01"
---

A stale check has passed the validity period and is no longer expected to clear. Do not delete the original entry. Reverse or cancel it according to its status, then issue a replacement when required.

## Before you begin

Confirm the correct Company, currency, receivable or payable account, and bank or cash ledger. Use submitted source documents and keep the bank reference or remittance advice available.

## Use Stale Cheque Accounting

1. Confirm with the bank that the check is stale and has not cleared.
2. Locate the original Payment Entry and its ledger impact.
3. Cancel it when ERPNext permits and your control policy allows cancellation.
4. If cancellation is not appropriate, post an authorized reversing Journal Entry with a clear reference.
5. Create a new Payment Entry for the replacement check and reconcile only when it clears.

![Stale Cheque Accounting in ERPNext](https://novacompanies.m.frappe.cloud/files/payments-14-journal-entry-list.png)

## Important fields and what they mean


| Field                  | What it controls                                    |
| ---------------------- | --------------------------------------------------- |
| Cheque or Reference No | Identifies the original instrument.                 |
| Reference Date         | Issue date of the check.                            |
| Posting Date           | Accounting date of the original or reversal entry.  |
| Remarks                | Reason for reversal and replacement reference.      |
| Clearance Date         | Date the bank confirms settlement, when applicable. |


## What happens after you submit or process

ERPNext updates the relevant accounting records and, where applicable, the outstanding or unallocated amounts. Review the General Ledger, party ledger, and source document status before treating the workflow as complete. A saved draft does not affect the ledger.

## Troubleshooting

### The stale cheque belongs to a closed accounting period

Do not cancel or backdate into a locked period without approval. Record the reversal or reclassification in the current permitted period using the workflow approved by your accountant.

### Reissuing the cheque would pay the invoice twice

First reverse or clear the stale cheque's payment effect, verify that the supplier balance is outstanding, and only then issue the replacement.

### The cheque was actually dishonoured, not merely stale

Record the correct event and supporting evidence. A dishonoured cheque can include bank charges and an immediate restoration of the invoice balance, while a stale cheque has expired without clearing.

## Frequently asked questions

### When does a cheque become stale?

The validity period depends on the bank and jurisdiction. Confirm the date with the bank rather than assuming a universal number of months.

### Should the original Payment Entry be deleted?

Keep the audit trail. Use cancellation, reversal, or a current-period adjustment according to the document status and accounting-period controls.

### Can a replacement cheque reuse the same reference number?

Use the new cheque's actual reference and link it to the reversal or stale cheque explanation. Reusing the old number weakens traceability.

### Does marking a cheque stale automatically reopen the invoice?

The invoice is restored only when the accounting effect of the original payment is properly reversed or unallocated. Verify Accounts Payable afterward.

## Related topics

- [Payment Entry](/erpnext/payment-entry)
- [Payment Reconciliation](/erpnext/payment-reconciliation)
- [Bank Reconciliation](/erpnext/bank-reconciliation)
- [Bank Transaction](/erpnext/bank-transaction)
- [Journal Entry](/erpnext/journal-entry)
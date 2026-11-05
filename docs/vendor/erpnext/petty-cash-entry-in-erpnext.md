---
title: "Book Petty Cash Entry | ERPNext Documentation"
description: "Record petty cash funding and expenses with a clear ERPNext audit trail."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/petty-cash-entry-in-erpnext"
updated: "2026-08-01"
---

Petty cash should use a dedicated cash ledger and a controlled custodian process. Record replenishment separately from the expenses paid from the float.

## Before you begin

Confirm the correct Company, currency, receivable or payable account, and bank or cash ledger. Use submitted source documents and keep the bank reference or remittance advice available.

## Use Book Petty Cash Entry

1. Create a dedicated Petty Cash account and assign responsibility for it.
2. Transfer money from the bank or main cash account into Petty Cash.
3. Record each expense with its date, expense account, amount, Cost Center, and receipt.
4. Reconcile the physical cash plus receipts to the ledger balance.
5. Post an approved adjustment only when the difference is explained.

![Book Petty Cash Entry in ERPNext](https://novacompanies.m.frappe.cloud/files/payments-14-journal-entry-list.png)

## Important fields and what they mean


| Field              | What it controls                                    |
| ------------------ | --------------------------------------------------- |
| Petty Cash Account | Asset ledger holding the float.                     |
| Expense Account    | Nature of the expense.                              |
| Cost Center        | Team, branch, or function responsible for the cost. |
| Reference          | Receipt or voucher number.                          |
| User Remark        | Business purpose and supporting explanation.        |


## What happens after you submit or process

ERPNext updates the relevant accounting records and, where applicable, the outstanding or unallocated amounts. Review the General Ledger, party ledger, and source document status before treating the workflow as complete. A saved draft does not affect the ledger.

## Troubleshooting

### Petty cash shows a negative balance

Check whether the fund was replenished before expenses were posted and whether all entries use the correct petty cash account. Investigate duplicate or backdated expenses rather than forcing the balance.

### An expense was posted without a Cost Center

Correct the draft or amend the submitted transaction through the supported workflow. Configure mandatory dimensions when departmental reporting is required.

### The receipt total does not match the cash issued

Record the actual expense and return or advance balance explicitly. Attach receipts and explain small approved differences according to company policy.

## Frequently asked questions

### Should petty cash use Payment Entry or Journal Entry?

Use the document that best represents the controlled workflow and permissions. Payment Entry suits cash movement, while expense claims or Journal Entries may be appropriate for reimbursement or adjustment scenarios.

### How should the petty cash fund be replenished?

Transfer the approved amount from bank or main cash to the petty cash account and retain the supporting authorization.

### Should every small purchase be entered separately?

Preserve enough detail for receipts, tax, Cost Centers, and audit. A summarized entry should be used only when company policy and local requirements permit it.

### Can employees receive a petty cash advance?

Use Employee Advance and Expense Claim when the money is accountable to a specific employee. That workflow provides clearer settlement than treating it as an ordinary expense immediately.

## Related topics

- [Payment Entry](/erpnext/payment-entry)
- [Payment Reconciliation](/erpnext/payment-reconciliation)
- [Bank Reconciliation](/erpnext/bank-reconciliation)
- [Bank Transaction](/erpnext/bank-transaction)
- [Journal Entry](/erpnext/journal-entry)
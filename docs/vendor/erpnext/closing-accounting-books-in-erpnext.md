---
title: "Closing Accounting Books in ERPNext in v15"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/closing-accounting-books-in-erpnext"
updated: "2026-08-14"
---

Closing the books is not one button. It is a controlled review that turns a year of operational documents into reliable financial statements. For Nova Industries, that means confirming what customers owe, what the company owes suppliers, whether bank and stock balances agree, whether depreciation and taxes are complete, and only then transferring the year’s profit or loss.

## Year-end sequence

1. Stop routine backdated changes and communicate the close timetable.
2. Review unbilled orders, receivables, payables, advances, credit notes, and debit notes.
3. Reconcile bank accounts with [Bank Reconciliation](/erpnext/bank-reconciliation) and allocate standalone payments with [Payment Reconciliation](/erpnext/payment-reconciliation).
4. Reconcile physical stock, stock valuation, fixed assets, depreciation, loans, payroll, taxes, and deferred balances.
5. Post approved accruals, provisions, write-offs, exchange adjustments, and audit corrections.
6. Validate Trial Balance, General Ledger, Balance Sheet, Profit and Loss, and Cash Flow.
7. Submit the [Period Closing Voucher](/erpnext/period-closing-voucher).
8. Protect the finished dates with an Accounting Period or frozen-accounts date.
9. Confirm the new Fiscal Year and defaults before routine posting resumes.

![Period-end ledger entries after closing](https://novacompanies.m.frappe.cloud/files/accounting-entries-20260802-accounting-entries-period-closing.png)



## What each control does


| Control                | Purpose                                                           | What it does not do                                   |
| ---------------------- | ----------------------------------------------------------------- | ----------------------------------------------------- |
| Period Closing Voucher | Transfers net income or loss to equity.                           | Does not lock later entries.                          |
| Accounting Period      | Blocks selected document types in a finished range.               | Does not transfer profit or loss.                     |
| Accounts Frozen Upto   | Applies a broad posting cut-off with a controlled role exception. | Does not replace reconciliation or closing entries.   |
| Fiscal Year            | Defines valid accounting dates and report periods.                | Does not by itself prove that the books are complete. |


![Fiscal Year dates used for the new accounting year](https://novacompanies.m.frappe.cloud/files/final-accounting-20260814-fiscal-year-dates.png)



## Troubleshooting

### Reports changed after the close

Find transactions posted or cancelled after the review date, compare the latest General Ledger with the approved export, post any required correction, submit another Period Closing Voucher for residual Profit and Loss balances, and then apply the appropriate lock.

### The Balance Sheet does not balance

Check incomplete opening balances, temporary opening account balances, cancelled or reposted entries, currency differences, and report filters before closing. Do not use the closing voucher to conceal an unexplained imbalance.

## Frequently asked questions

### Do unpaid invoices carry into the next year?

Receivables and payables are Balance Sheet balances and continue until settled, written off, or otherwise adjusted.

### Do I create opening entries every year?

Opening entries are normally a migration or first-setup activity. Ongoing Balance Sheet balances carry forward through the ledger.

## Related topics

- [Accounting overview](/erpnext/accounting/introduction)
- [Chart of Accounts](/erpnext/chart-of-accounts)
- [General Ledger](/erpnext/general-ledger)
- [Fiscal Year](/erpnext/fiscal-year)
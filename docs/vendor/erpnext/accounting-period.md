---
title: "Accounting Period"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/accounting-period"
updated: "2026-08-14"
---

Nova Industries has approved its April to June financial statements. The finance team now needs those numbers to remain stable while July transactions continue. An Accounting Period locks selected submittable document types for the finished date range, preventing a late invoice, cancellation, or amendment from changing reports that have already been reviewed.



This is a selective lock. You choose which document types are closed. It is different from a [Period Closing Voucher](/erpnext/period-closing-voucher), which transfers profit or loss, and from [freezing accounting entries](/erpnext/freeze-accounting-entries), which applies a broader date-based posting restriction.

## Before you begin

- Finish reconciliations and approved period-end adjustments.
- Confirm which document types must be blocked with the finance controller.
- Create the record only after the end date has passed. ERPNext does not allow a future end date.

## Create an Accounting Period

1. Open **Accounting Period** and create a new record.
2. Enter a descriptive name, start date, end date, and company.
3. Select an exempted role only when your policy permits controlled exceptions.
4. In **Closed Documents**, add the document types to restrict and keep **Closed** selected.
5. Save, review, and submit the record.

![Current Period Closing settings in ERPNext](https://novacompanies.m.frappe.cloud/files/final-accounting-20260814-accounts-settings-closing.png)



## Choose what to close


| Document type                      | Why teams commonly close it                                              |
| ---------------------------------- | ------------------------------------------------------------------------ |
| Sales Invoice and Purchase Invoice | Protect revenue, expense, receivable, payable, and tax balances.         |
| Journal Entry                      | Prevent unapproved backdated adjustments.                                |
| Payment Entry                      | Protect bank, cash, receivable, and payable allocations.                 |
| Stock Entry and stock transactions | Protect valuation and cost of goods sold where stock accounting applies. |


## What users experience

When a selected document is dated inside the closed range, ERPNext blocks creation, amendment, or cancellation after the Accounting Period has ended. A document type that is not listed, or whose **Closed** checkbox is cleared, remains available.

## Troubleshooting

### Users can still post one type of transaction

Open the Accounting Period and confirm that the exact DocType appears in Closed Documents with Closed selected. Also confirm that the posting date falls inside the period and the record is submitted.

### You cannot save the period

Check that the end date is not in the future, the date range is valid, the company is correct, and at least one closed document row is present.

## Frequently asked questions

### Does the exempted role bypass every restriction?

Treat exemptions as controlled finance access and test the exact transaction type. Some period-closing restrictions are intentionally strict and should not be assumed to behave like the broader frozen-accounts role.

### Should I create next month’s Accounting Period in advance?

Create it after the month ends. Use permissions and the frozen-accounts date if you need to control entries during an active month.

## Related topics

- [Accounting overview](/erpnext/accounting/introduction)
- [Chart of Accounts](/erpnext/chart-of-accounts)
- [General Ledger](/erpnext/general-ledger)
- [Fiscal Year](/erpnext/fiscal-year)
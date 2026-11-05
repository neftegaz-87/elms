---
title: "Fixing Fiscal Year Error"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/fiscal-year-error"
updated: "2026-08-14"
---

Nova Industries creates an invoice dated 2 January 2027, but ERPNext reports that the date is not in the selected fiscal year. The transaction date, the selected Fiscal Year, and the company’s defaults no longer agree. Create the missing year or correct the default instead of changing the document to an inaccurate date.

## Resolve the error

1. Open **Fiscal Year** and confirm a record covers the transaction date.
2. Check the start date, end date, and company assignment.
3. Set the new Fiscal Year as default when it should be used for new transactions.
4. Open Global Defaults and confirm the default Fiscal Year.
5. Reload ERPNext and reopen the transaction.

![Fiscal Year start and end dates highlighted](https://novacompanies.m.frappe.cloud/files/final-accounting-20260814-fiscal-year-dates.png)



## Troubleshooting

### The year exists but the error remains

Check whether the Fiscal Year is assigned to the transaction’s company, whether another field explicitly contains the old year, and whether the posting date falls exactly within the configured range.

### The date is intentionally in an older year

Select the appropriate fiscal year and confirm that the period is not frozen or closed. Obtain approval before entering a backdated accounting transaction.

## Frequently asked questions

### Should I change the date just to submit?

The posting date should reflect the real accounting event. Fix the year setup or obtain the required period access instead of using a false date.

## Related topics

- [Accounting overview](/erpnext/accounting/introduction)
- [Chart of Accounts](/erpnext/chart-of-accounts)
- [General Ledger](/erpnext/general-ledger)
- [Fiscal Year](/erpnext/fiscal-year)
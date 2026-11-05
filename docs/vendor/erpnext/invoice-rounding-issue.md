---
title: "Invoice rounding issue"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/invoice-rounding-issue"
updated: "2026-08-14"
---

Nova Industries disables rounded totals, but an invoice print still rounds the amount in words. Two settings can influence the result: the global rounded-total preference and the smallest currency fraction. The currency master must describe the real precision of the transaction currency.

## Check both settings

1. Open Global Defaults and confirm **Disable Rounded Total** matches the company’s policy.
2. Open the Currency used on the invoice.
3. Set **Smallest Currency Fraction Value** correctly, such as 0.01 for a currency whose smallest unit is one cent.
4. Save, reload the invoice, and regenerate the print.

![Currency master with current precision and fraction settings](https://novacompanies.m.frappe.cloud/files/final-accounting-20260814-currency-eur-settings.png)



## Troubleshooting

### The printed words still differ

Check the Print Format, currency, precision, Rounded Total field, and cached print preview. Compare the numeric Grand Total, Rounded Total, and amount in words before changing any ledger posting.

## Frequently asked questions

### Does changing currency precision rewrite old invoices?

It changes how later calculations and displays use that currency. Review the effect carefully and do not expect submitted historical ledger entries to be recalculated automatically.

## Related topics

- [Accounting overview](/erpnext/accounting/introduction)
- [Chart of Accounts](/erpnext/chart-of-accounts)
- [General Ledger](/erpnext/general-ledger)
- [Fiscal Year](/erpnext/fiscal-year)
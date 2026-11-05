---
title: "Round off Account Validation Message"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/round-off-account-validation"
updated: "2026-08-14"
---

A Purchase Invoice for Nova Industries contains item calculations, tax, discount, and currency precision. The exact total differs from the payable amount by a few cents, but no account is configured to hold that difference. ERPNext asks for a Round Off Account so the debit and credit totals remain balanced.

## Configure the default

1. Open the Chart of Accounts and create or identify a small rounding expense or income account.
2. Open the Company record for Nova Industries.
3. In the accounting defaults, set the Round Off Account and Round Off Cost Center.
4. Save the Company, reload the invoice, and submit again.

![Company defaults for Round Off Account and Round Off Cost Center](https://novacompanies.m.frappe.cloud/files/final-accounting-20260814-company-round-off-defaults.png)



## Why rounding appears

Quantity multiplied by rate, taxes, discounts, exchange rates, and currency precision can produce fractions smaller than the currency accepts. ERPNext posts the small difference instead of leaving an unbalanced ledger.

## Troubleshooting

### The error remains after setting the account

Confirm the account and cost center belong to the same company, the account is a ledger account rather than a group, and the transaction was reloaded after the Company was saved.

## Frequently asked questions

### Should I use a large adjustment account?

Round Off is for small precision differences. A material difference usually indicates an incorrect rate, tax, exchange rate, or precision setting and should be investigated.

## Related topics

- [Accounting overview](/erpnext/accounting/introduction)
- [Chart of Accounts](/erpnext/chart-of-accounts)
- [General Ledger](/erpnext/general-ledger)
- [Fiscal Year](/erpnext/fiscal-year)
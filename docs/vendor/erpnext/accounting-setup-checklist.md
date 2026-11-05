---
title: "Accounting Setup Checklist | ERPNext Documentation"
description: "Use this ERPNext accounting setup checklist to verify company, accounts, banking, taxes, opening balances, controls, and go-live testing."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/accounting-setup-checklist"
updated: "2026-08-14"
---

Accounting setup is complete only when a real transaction can move from business activity to the correct ledger accounts without guesswork. The safest approach is to configure the foundation in sequence, then test one small sales, purchase, payment, and reporting cycle.



Nova Industries first establishes its fiscal year and Chart of Accounts, then adds taxes, Cost Centers, bank and payment defaults, credit terms, and company-level fallback accounts. Each later choice depends on the earlier structure, so testing as you go is easier than correcting many submitted transactions later.



Use this checklist as a practical readiness review. It links each setup decision to the transaction or report that proves the configuration works.

## 1. Company and calendar

- Create the legal entity in [Company](https://docs.frappe.io/erpnext/company-setup).
- Confirm abbreviation, country, currency, tax ID, and address.
- Create and assign the [Fiscal Year](https://docs.frappe.io/erpnext/fiscal-year).

## 2. Chart of Accounts and defaults

- Review the [Chart of Accounts](https://docs.frappe.io/erpnext/chart-of-accounts).
- Confirm receivable, payable, cash, bank, income, expense, tax, stock, fixed-asset, write-off, exchange, and rounding accounts.
- Configure [Company accounting defaults](https://docs.frappe.io/erpnext/company-accounting-defaults).
- Create the required [Cost Centers](https://docs.frappe.io/erpnext/cost-center) and other Accounting Dimensions.

## 3. Payments and banking

- Create Bank and Bank Account records.
- Map a ledger account to every company bank account.
- Configure [Modes of Payment](https://docs.frappe.io/erpnext/bank-accounts-and-modes-of-payment).
- Test a receipt, payment, statement import, and reconciliation.

## 4. Sales, purchases, and taxes

- Create Payment Terms and templates.
- Configure sales and purchase tax templates.
- Add Tax Categories, Tax Rules, and Item Tax Templates where required.
- Confirm Customer, Supplier, Item, and Item Group defaults.

## 5. Accounting controls

- Review [Accounts Settings](https://docs.frappe.io/erpnext/accounts-settings).
- Configure roles, approval workflows, and submission permissions.
- Decide how periods will be locked and closed.
- Configure document naming and print formats.

## 6. Opening data

- Choose a cutover date.
- Import parties, Items, fixed assets, and outstanding invoices.
- Import opening ledger balances through approved opening tools.
- Reconcile receivables, payables, bank, stock, fixed assets, tax balances, and equity with the previous system.

## 7. Test before go-live

Run one complete sales, purchase, payment, expense, asset, and return scenario. Verify:

- General Ledger debit and credit;
- Accounts Receivable and Payable;
- Trial Balance;
- Balance Sheet and Profit and Loss Statement;
- Stock Ledger and Stock Balance, if perpetual inventory is enabled;
- tax reports;
- bank reconciliation;
- printed and emailed documents.

Record who approved the opening balances and test results.

## Related topics

- [Opening Balance](https://docs.frappe.io/erpnext/opening-balance)
- [Opening Invoice Creation Tool](https://docs.frappe.io/erpnext/opening-invoice-creation-tool)
- [Data Import](https://docs.frappe.io/erpnext/data-import)
- [Accounting Period](https://docs.frappe.io/erpnext/accounting-period)
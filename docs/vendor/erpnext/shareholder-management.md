---
title: "Shareholder Management"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/shareholder-management"
updated: "2026-08-14"
---

Nova Electronics Trading starts with three shareholders: Elena Brooks holds 6,000 shares, Marcus Lee holds 4,000, and Horizon Ventures LLC holds 1,000. As Nova raises capital and ownership changes, the finance team must answer three questions reliably: who the owners are, how many shares each one holds, and which transaction changed that balance. Shareholder management connects those answers instead of treating them as separate spreadsheets.



In ERPNext, the workflow has three parts. A [Shareholder](/erpnext/shareholder) identifies the owner. A [Share Transfer](/erpnext/share-transfer) records an Issue, Purchase, or Transfer. [Share Reports](/erpnext/share-reports) show the resulting balances and history.

![Nova shareholder register in ERPNext](https://novacompanies.m.frappe.cloud/files/budgets-capital-equity-20260814-shareholder-list.png)

## Use the records in this order


| Step | Record                                   | Result                                                |
| ---- | ---------------------------------------- | ----------------------------------------------------- |
| 1    | Shareholder                              | Creates the owner master and contact context.         |
| 2    | Share Transfer with Issue                | Creates the first holding and assigns a folio number. |
| 3    | Share Transfer with Transfer or Purchase | Changes ownership or records a company buyback.       |
| 4    | Share Balance and Share Ledger           | Verifies current ownership and transaction history.   |


![Share issue type, shareholder, and share type highlighted](https://novacompanies.m.frappe.cloud/files/budgets-capital-equity-20260814-share-issue-details.png)

## Keep the register reliable

Use submitted Share Transfers for every ownership change. Do not overwrite a shareholder's balance manually. Keep [Contacts](/erpnext/contact) and [Addresses](/erpnext/address) linked to the master, and use a consistent [Fiscal Year](/erpnext/fiscal-year) and posting date when related accounting entries are required.

## Frequently asked questions

### Does creating a Shareholder change the company's equity?

The master itself has no ledger impact. A submitted share issue records the ownership movement, and the related [Journal Entry](/erpnext/journal-entry) is used when accounting entries are required.

### Which report shows the current owner balance?

Share Balance shows current holdings. Share Ledger explains how those holdings changed transaction by transaction.

## Related topics

- [Shareholder](/erpnext/shareholder)
- [Share Transfer](/erpnext/share-transfer)
- [Share Reports](/erpnext/share-reports)
- [Chart of Accounts](/erpnext/chart-of-accounts)
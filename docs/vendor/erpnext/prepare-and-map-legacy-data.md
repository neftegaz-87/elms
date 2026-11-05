---
title: "Prepare and Map Legacy Accounting Data | ERPNext Documentation"
description: "Clean, map, classify, and validate legacy accounting data before importing masters, invoices, balances, stock, and assets into ERPNext."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/prepare-and-map-legacy-data"
updated: "2026-08-14"
---

Data exported from an older accounting system rarely matches ERPNext exactly. Preparing and mapping means cleaning that export and translating its customers, suppliers, accounts, tax codes, currencies, and identifiers into values ERPNext can import safely.



Nova Industries may have three spellings for the same customer, inactive ledger accounts, dates in mixed formats, and tax labels that do not exist in the new Chart of Accounts. Resolving those differences before import prevents duplicates and makes validation far easier than correcting submitted records later.



This page shows how to profile the source data, define a mapping workbook, remove unnecessary history, standardize values, and produce import files that can be tested repeatedly.

## Freeze the source extract

Create a dated migration folder and store:

- the original unedited exports;
- cleaned working files;
- approved import files;
- ERPNext import results;
- reconciliation files;
- sign-off evidence.

Never overwrite the original export. Record the source system, report name, filters, company, currency, period, extraction time, and person responsible.

## Clean source records

Standardize:

- names, capitalization, and spaces;
- date format as `YYYY-MM-DD`;
- decimal and thousands separators;
- currency codes;
- tax identifiers;
- country, state, and postal codes;
- units of measure;
- blank values and zero values;
- debit and credit signs.

Remove duplicate parties only after deciding which record survives and how the balances are combined.

## Build mapping tables

Create an approved old-to-new mapping for every controlled field.


| Legacy value    | ERPNext value         | Action        |
| --------------- | --------------------- | ------------- |
| Sales - Devices | Product Sales - NET   | Map           |
| Admin East      | Corporate Sales - NET | Map           |
| Cust-00482      | Northstar Retail      | Merge and map |
| WH-A            | Main Warehouse - NET  | Map           |
| USD             | USD                   | Keep          |


Do not use spreadsheet formulas that silently return blank when a mapping is missing. Add a validation column that marks every unmapped value as an error.

## Map the Chart of Accounts

For every legacy account, record:

- ERPNext account;
- parent group;
- root type;
- group or ledger;
- account type;
- account currency;
- whether it is a control account;
- opening import method;
- whether it will be disabled after migration.

Map retired accounts to an appropriate active account only with finance approval. Keep separate tax, bank, receivable, payable, stock, fixed-asset, depreciation, and equity accounts when reporting requires them.

## Prepare outstanding invoices

Include one row per open invoice or credit note:

- party;
- invoice number;
- posting date;
- due date;
- invoice currency;
- exchange rate;
- original total;
- outstanding amount;
- receivable or payable account;
- Cost Center where required;
- legacy reference.

Do not import paid invoices through the Opening Invoice Creation Tool.

## Prepare the opening Trial Balance

Start from the final Trial Balance after all legacy adjustments. Add columns for:

- legacy account and balance;
- ERPNext account;
- debit;
- credit;
- import method;
- document reference;
- imported amount;
- difference;
- reviewer note.

Classify each line as **Invoice**, **Payment/Advance**, **Bank/Cash**, **Stock**, **Asset**, or **Residual Journal Entry**. Each source balance must appear in one category only.

## Prepare stock and assets

For stock, include Item, Warehouse, quantity, valuation rate, and total value. Reconcile quantity and value separately.

For assets, include asset category, asset name, purchase date, available-for-use date, gross cost, accumulated depreciation, net book value, useful life, remaining periods, location, custodian, and finance book.

## Run pre-import checks

- every required parent exists;
- every linked value uses the exact ERPNext name;
- dates fall in a valid Fiscal Year;
- debit equals credit;
- outstanding invoice totals match ageing;
- stock quantity times rate explains total value;
- asset cost less accumulated depreciation equals net book value;
- no account is assigned to two import methods;
- foreign-currency totals reconcile in both currencies.

## Related topics

- [Import Accounting Masters](https://docs.frappe.io/erpnext/import-accounting-masters)
- [Import Chart of Accounts](https://docs.frappe.io/erpnext/import-chart-of-accounts)
- [Opening Balance in Accounts](https://docs.frappe.io/erpnext/opening-balance)
- [Data Import](https://docs.frappe.io/erpnext/data-import)
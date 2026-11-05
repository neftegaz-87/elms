---
title: "Accounting Migration Overview | ERPNext Documentation"
description: "Plan and complete an ERPNext accounting migration using a clear cutover scope, clean source data, the correct import tools, reconciliation, and finance approval."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/accounting-migration-overview"
updated: "2026-08-15"
---

An accounting migration is not a project to recreate every screen and transaction from the old system. It is a controlled handover: choose a cut-off date, bring across the information needed to continue operations, prove that the opening position is correct, and start new transactions in ERPNext.



Nova Industries has seven years of invoices in its previous system, but only current masters, open invoices, unallocated payments, stock, assets, bank balances, and verified ledger balances are needed to begin. The old system can remain available for historical reporting until those records are no longer operationally useful.



This guide gives an opinionated migration sequence: decide the scope, export, clean and map the data, import masters, load opening transactions and balances, then validate and correct the result before users begin normal posting.

## The migration process

Do at least one test migration before the final cutover. A migration is complete only after the results have been validated and the finance owner has approved them.

## 1. Choose what you will migrate

Start by choosing a cutover date. A financial-year boundary is convenient, but a month-end can also work if waiting is impractical. Close and reconcile your old system through the day before this date. Enter every new transaction in ERPNext from the cutover date onward.

For most companies, the best scope is:

- active Customers, Suppliers, Items, Warehouses, Accounts, Cost Centers, tax templates, and other masters needed after cutover;
- unpaid customer and supplier invoices;
- unallocated payments and advances;
- bank and cash balances;
- stock quantities and values by Item and Warehouse;
- fixed assets with their accumulated depreciation;
- other asset, liability, and equity balances;
- year-to-date income and expense balances only when you are starting during a financial year and need current-year reporting in ERPNext.

Leave closed invoices, settled payments, old quotations, completed orders, and detailed journal history in the old system unless there is a legal or operational reason to move them.

Before deciding, ask a practical question: **Will someone need this record to complete work in ERPNext after cutover?** If the answer is no, preserve it in the old system or as a secure export instead of importing it.

## 2. Export and preserve the source data

Complete the normal month-end or year-end checks in your existing system before extracting data. Once the final export starts, stop users from changing transactions dated before the cutover.

Keep these source reports:


| Source report                                | Why you need it                                                                    |
| -------------------------------------------- | ---------------------------------------------------------------------------------- |
| Trial Balance                                | Proves that the opening general ledger in ERPNext agrees with the old system.      |
| Balance Sheet and Profit and Loss Statement  | Confirms financial-statement totals and account classifications.                   |
| Customer ageing by invoice                   | Provides each unpaid customer invoice, due date, currency, and outstanding amount. |
| Supplier ageing by invoice                   | Provides each unpaid supplier invoice and outstanding amount.                      |
| Bank reconciliation and statements           | Confirms the bank ledger, statement balance, and uncleared transactions.           |
| Stock report by Item and Warehouse           | Provides the opening quantity and value of inventory.                              |
| Fixed Asset register                         | Provides asset cost, date, accumulated depreciation, and remaining life.           |
| Advances and unallocated payments            | Identifies money received or paid that is not allocated to an invoice.             |
| Tax, loan, accrual, and prepayment schedules | Explains balances that cannot be understood from the Trial Balance alone.          |


Save the final reports as protected spreadsheets or PDFs. Record the exact export time, cutover date, company, currency, and filters used. These files are your migration evidence and your fallback when a total does not agree.

## 3. Clean and map the data

Cleaning and mapping means transforming data exported from your current system into the format ERPNext can import.

Do not edit your only source export. Keep it unchanged, then create a working copy. In the working copy:

1. Remove inactive records that you have decided not to migrate.
2. Remove duplicate Customers, Suppliers, Items, and Accounts.
3. Standardize names, dates, country codes, currencies, units of measure, and tax identifiers.
4. Decide the ERPNext name or code for each legacy record.
5. Map every legacy account to an ERPNext Account.
6. Map Customers, Suppliers, Items, Warehouses, Cost Centers, and currencies to their ERPNext names.
7. Separate outstanding invoices, advances, stock, assets, bank balances, and remaining general-ledger balances because they use different import methods.
8. Compare the cleaned totals with the unchanged source reports.

Create a simple mapping workbook with columns such as `Legacy Type`, `Legacy ID`, `Legacy Name`, `ERPNext Type`, `ERPNext Name`, `Action`, and `Notes`. Use `Action` values such as **Import**, **Merge**, **Rename**, and **Do not migrate**. This gives the migration team one approved answer when a legacy name does not match ERPNext.

## 4. Configure ERPNext before importing

Create the Company and confirm its country, default currency, fiscal year, and accounting defaults. Set up the Chart of Accounts, Cost Centers, Warehouses, units of measure, tax accounts, and naming rules before importing dependent records.

Import masters in dependency order. A practical sequence is:

1. Chart of Accounts and Cost Centers
2. Warehouses and units of measure
3. Item Groups, Customer Groups, Supplier Groups, and Territories
4. Customers and Suppliers
5. Items and Item Prices
6. Bank Accounts, Modes of Payment, tax templates, and remaining masters

Test a few records first. Open them in ERPNext and confirm that links, defaults, addresses, currencies, and accounts are correct before importing the complete file.

## 5. Use the right ERPNext import tool

ERPNext provides different tools because not every opening record should be imported in the same way.


| Tool                                                                                          | Use it for                                                                                                                                               |
| --------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Data Import](https://docs.frappe.io/erpnext/data-import)                                     | Import Customers, Suppliers, Items, Warehouses, Cost Centers, and other master records from CSV or Excel templates. It can also update existing records. |
| [Chart of Accounts Importer](https://docs.frappe.io/erpnext/chart-of-accounts-importer)       | Import your own account hierarchy before transactions exist for the Company.                                                                             |
| [Opening Invoice Creation Tool](https://docs.frappe.io/erpnext/opening-invoice-creation-tool) | Create outstanding Sales Invoices and Purchase Invoices without recreating their full item history.                                                      |
| [Opening Balance in Accounts](https://docs.frappe.io/erpnext/opening-balance)                 | Bring in the remaining opening ledger balances through opening entries.                                                                                  |
| [Stock Reconciliation](https://docs.frappe.io/erpnext/stock-reconciliation)                   | Set opening stock quantities and values by Item and Warehouse.                                                                                           |
| [Asset](https://docs.frappe.io/erpnext/asset)                                                 | Create existing fixed assets with their opening cost and depreciation information.                                                                       |


Use small batches and retain every import file. Give each file a clear sequence number so you can tell which version was tested, corrected, and finally imported.

### Avoid double counting

Opening invoices, stock, assets, and opening payments can create accounting entries. Do not import the same value again in the final opening Journal Entry.

For example, suppose your legacy Trial Balance contains:

- $10,000 in Accounts Receivable from unpaid customer invoices;
- a $2,000 unallocated customer receipt;
- a net Accounts Receivable balance of $8,000.

Create the $10,000 outstanding invoices with the Opening Invoice Creation Tool and bring in the $2,000 receipt using the approved opening-payment method. Do not add another $8,000 Accounts Receivable line to the opening Journal Entry. That would count the balance twice.

After all specialized opening documents are created, use an opening Journal Entry only for balances that have not already been produced by another document. The Temporary Opening account should be zero when the migration is complete.

## 6. Validate and correct

Do not judge the migration by the number of successful imports. Judge it by whether ERPNext agrees with the approved source reports.

Validate in this order:

1. Compare the number of imported masters and outstanding invoices.
2. Compare customer and supplier ageing invoice by invoice.
3. Compare bank, cash, stock, fixed assets, advances, tax balances, loans, and other schedules.
4. Run the ERPNext Trial Balance for the cutover date and compare every account with the source Trial Balance.
5. Compare the Balance Sheet and Profit and Loss Statement.
6. Confirm that Temporary Opening and migration-clearing accounts have no unexplained balance.
7. Test normal work, including creating an invoice, receiving a payment, delivering stock, paying a supplier, and running reports.

If a total does not agree, do not post an unexplained Journal Entry to force the Trial Balance to match. Find the source of the difference. Typical causes are duplicate imports, an incorrect account mapping, a missing invoice, reversed debit and credit values, the wrong currency or exchange rate, or importing a control-account balance after its supporting invoices were already created.

Correct the mapping or import file, cancel or reverse the incorrect migration record using the normal ERPNext controls, import the corrected data, and validate again. Keep a correction log that records the issue, cause, action, owner, and evidence.

## 7. Approve the migration and go live

Before go-live, obtain written approval from the finance owner that:

- the Trial Balance and financial statements agree;
- receivables and payables agree with invoice-level schedules;
- bank, stock, asset, tax, and other control balances agree;
- operational tests have passed;
- correction items are resolved or formally accepted;
- the old system exports and backups are stored securely;
- users know the final cutover time and where new transactions must be entered.

After approval, stop changing migration records except through a controlled correction process. Keep the old system read-only for historical reports. ERPNext is now the source of truth for transactions dated on or after the cutover.

## Related topics

- [Data Import](https://docs.frappe.io/erpnext/data-import)
- [Chart of Accounts Importer](https://docs.frappe.io/erpnext/chart-of-accounts-importer)
- [Opening Invoice Creation Tool](https://docs.frappe.io/erpnext/opening-invoice-creation-tool)
- [Opening Balance in Accounts](https://docs.frappe.io/erpnext/opening-balance)
- [Stock Reconciliation](https://docs.frappe.io/erpnext/stock-reconciliation)
- [Trial Balance](https://docs.frappe.io/erpnext/accounting-reports)
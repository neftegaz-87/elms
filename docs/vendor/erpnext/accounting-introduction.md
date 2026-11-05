---
title: "Accounting Introduction | ERPNext Documentation"
description: "Understand ERPNext Accounting features, ledgers, invoices, payments, taxes, banking, inventory accounting, controls, closing, and financial reports."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/accounting-introduction"
updated: "2026-08-14"
---

Accounting in ERPNext turns everyday business activity into a reliable financial record. A sale, purchase, stock movement, expense, or payment begins as an operational document and becomes balanced ledger entries when it is submitted.



At Nova Industries, an electronics manufacturer and distributor, the finance team needs to answer simple questions: Are customers paying on time? What do we owe suppliers? Is the business profitable, and does the bank balance agree with the books? ERPNext connects those questions to the transactions that created each amount.



This guide introduces the accounting features, explains how transactions reach the ledger, and shows which workflow fits different kinds of businesses. You can start with the basic sales and purchase cycles, then move into reconciliation, taxes, dimensions, budgets, and financial reporting as your needs grow.

## The accounting model

Each Company has a base currency, fiscal year, default accounts, and its own [Chart of Accounts](/erpnext/chart-of-accounts). The chart groups accounts under Assets, Liabilities, Equity, Income, and Expenses. Ledger accounts hold postings; group accounts organize them for reporting.



ERPNext uses double-entry accounting. Every accounting transaction has equal debit and credit totals, so the books remain balanced. You do not normally create those entries by hand. Submitting a transaction generates them from the document's values and accounting configuration.

Three records are especially useful when tracing a number:


| Record                   | What it tells you                                                                                             |
| ------------------------ | ------------------------------------------------------------------------------------------------------------- |
| **Source document**      | The business event, amounts, parties, taxes, dates, and references entered by a user                          |
| **GL Entry**             | The debit or credit posted to an account, with its company, party, cost center, project, and other dimensions |
| **Payment Ledger Entry** | How receivables, payables, advances, and payments are linked and allocated                                    |


If stock accounting is enabled, inventory transactions also create Stock Ledger Entries. Stock quantities and values are therefore traceable separately from, but connected to, the General Ledger. Read [How Transactions Affect the Ledger](/erpnext/how-transactions-affect-the-ledger) for posting examples.

## What the Accounting module covers

### Company books and account structure

ERPNext creates a separate set of books for every Company. You can use the standard chart supplied for the selected country, edit it, or use the [Chart of Accounts Importer](/erpnext/chart-of-accounts-importer) during implementation.



Company defaults determine common posting accounts such as receivables, payables, income, expenses, round-off, exchange gain or loss, and retained earnings. [Accounts Settings](/erpnext/accounts-settings) contains controls that apply across transactions, including frozen dates and rules for editing accounting entries.



Use [Finance Books](/erpnext/finance-book) when the same company needs parallel asset depreciation or reporting bases. Use multiple companies and consolidated reports when legal entities must keep independent ledgers but management needs a combined view.

### Sales, purchases, and outstanding amounts

A [Sales Invoice](/erpnext/sales-invoice) records income, tax, and the amount a Customer owes. A [Purchase Invoice](/erpnext/purchase-invoice) records expense or asset value, tax, and the amount owed to a Supplier. Credit Notes and Debit Notes reverse or reduce the effect of invoices while preserving an audit trail.



ERPNext tracks receivables and payables by party, invoice, due date, and payment term. Accounts Receivable and Accounts Payable reports provide ageing and outstanding analysis. Payment terms can divide one invoice into scheduled instalments.



For collection workflows, Payment Requests can share a request or payment link with a Customer. Dunning helps follow up overdue receivables. Supplier payments can be organized with Payment Orders where that approval process is required.

### Payments, advances, and reconciliation

A [Payment Entry](/erpnext/payment-entry) records money received, money paid, or an internal transfer between cash and bank accounts. It can allocate one payment across several invoices, accept a partial payment, record an advance against an order, or retain an excess amount as unallocated credit.



Use [Payment Reconciliation](/erpnext/payment-reconciliation) to match existing unallocated payments, advances, credit notes, and journal entries with invoices. This changes allocation and outstanding balances without creating a second cash movement.



For bank operations, ERPNext stores Bank Accounts and Bank Transactions, imports statement data, and provides a [Bank Reconciliation](/erpnext/bank-reconciliation) tool. Reconciliation matches statement lines with vouchers, creates missing payments where appropriate, and records clearance dates.

### Taxes and regional compliance

Tax templates add sales and purchase taxes to transactions. Tax Categories and Tax Rules can choose the correct template from factors such as party, address, Item, or transaction. Item Tax Templates support different rates for particular products. Tax withholding supports deductions made when paying eligible Suppliers.



Tax reports and statutory behavior vary by country. ERPNext provides the accounting framework, while regional features may come from the selected country configuration or a localization app. Complete [tax setup](/erpnext/setting-up-taxes) before posting live invoices.

### Inventory and cost of goods sold

With perpetual inventory, stock receipts and issues affect both the Stock Ledger and the General Ledger. Purchase Receipts can move value into stock received but not billed. Delivery Notes reduce inventory and recognize cost of goods sold. Stock Entries record transfers, manufacture, repacking, and adjustments.



A Sales Invoice or Purchase Invoice can also update stock when the **Update Stock** option is enabled. This supports a shorter workflow, but it combines billing and stock movement in one document. Choose the workflow deliberately before users begin posting transactions.

### Assets, expenses, and deferred accounting

The Assets module integrates with Accounting for capitalization, depreciation, transfers, disposal, and value adjustments. Depreciation schedules can post entries automatically.



Expense Claims record employee expenses and liabilities. Deferred revenue and deferred expense settings spread eligible invoice amounts across future accounting periods instead of recognizing the full amount on the invoice date.



Subscriptions and recurring documents can automate regular billing. Projects and Timesheets support service billing, cost collection, and profitability analysis.

### Cost control and management reporting

[Cost Centers](/erpnext/cost-center) identify where income and expense belong. Projects track work-specific revenue and cost. Configurable [Accounting Dimensions](/erpnext/accounting-dimensions) add reporting segments such as branch, department, channel, or business unit without expanding the Chart of Accounts.



Budgets can be set by account, cost center, project, or accounting dimension. ERPNext can warn or stop users when an applicable annual or monthly budget is exceeded. Budget Variance reports compare planned and actual values.

### Currencies and intercompany accounting

Companies, parties, bank accounts, and ledger accounts can use different currencies. ERPNext stores transaction currency and company currency values, applies exchange rates, and books realized exchange differences during settlement. Exchange Rate Revaluation handles eligible open foreign-currency balances at a reporting date.



Inter Company Journal Entries and linked sales and purchase invoices help record transactions between entities. Each company still receives its own balanced entries.

### Closing, controls, and auditability

A [Journal Entry](/erpnext/journal-entry) handles adjustments such as accruals, provisions, transfers, write-offs, and corrections that do not belong in a specialized document.



At period end, accountants review reconciliations, depreciation, stock valuation, tax, and adjusting entries. A Period Closing Voucher transfers the period's profit or loss to the selected closing account. An [Accounting Period](/erpnext/accounting-period) can prevent selected transaction types from being posted, amended, or cancelled in a closed period. Frozen-date controls provide another way to restrict backdated accounting.



Submitted documents retain their audit trail. Instead of editing a finalized transaction in place, users cancel and amend it when permissions and period controls allow. ERPNext's immutable-ledger approach creates reversal entries for cancellation rather than deleting the original ledger history.

### Reports and financial statements

The [Accounting Reports](/erpnext/accounting-reports) workspace includes:

- General Ledger and Trial Balance for account-level verification
- Balance Sheet, Profit and Loss Statement, and Cash Flow
- Accounts Receivable and Accounts Payable with ageing
- Sales and Purchase Registers
- Bank reconciliation and payment reports
- Tax, budget, cost center, project, and dimension-based reports
- Consolidated statements and multi-currency display options where supported

Reports read submitted ledger data. A draft document does not affect the books, and cancelling a submitted transaction reverses its accounting effect.

## A practical way to learn the module

Start with [Understanding Debit and Credit](/erpnext/understand-debit-and-credit), then follow one complete business cycle. Create an invoice, submit it, open its **Accounting Ledger**, record a payment, and review the General Ledger and Accounts Receivable or Payable report.

Before a production rollout:

1. Finalize Companies, fiscal years, currency, and the Chart of Accounts.
2. Configure default accounts, taxes, payment terms, cost centers, and dimensions.
3. Decide which sales, purchase, stock, and service workflows users will follow.
4. Import opening balances and outstanding invoices using the appropriate migration tools.
5. Test representative transactions and reconcile their ledger effect.
6. Set roles, approval controls, frozen dates, and period-closing responsibilities.

See [Accounting Workflows by Business Type](/erpnext/accounting-workflows-by-business-type) to choose a starting workflow.

## Related topics

- [Chart of Accounts](/erpnext/chart-of-accounts)
- [How Transactions Affect the Ledger](/erpnext/how-transactions-affect-the-ledger)
- [Understanding Debit and Credit](/erpnext/understand-debit-and-credit)
- [Accounting Reports](/erpnext/accounting-reports)
- [Opening and Closing](/erpnext/opening-and-closing)
- [Accounting Workflows by Business Type](/erpnext/accounting-workflows-by-business-type)
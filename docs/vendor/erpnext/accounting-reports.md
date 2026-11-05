---
title: "Accounting Reports"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/accounting-reports"
updated: "2026-08-14"
---

It is the end of August at Nova Industries. The sales team says the company had a strong month, but the finance manager sees less cash in the bank than expected. Customers still owe money, several supplier bills are overdue, and the team needs to explain which transactions produced the balances before deciding what to collect and what to pay.



No single report answers all of those questions. ERPNext accounting reports show the same submitted transactions from different angles. This guide helps you begin with the decision you need to make, select the right report, interpret a populated example, and move from a summary number to its source document.

## Begin with the question, not the report name


| Question                                                               | Start with                                                      | Why                                                                     |
| ---------------------------------------------------------------------- | --------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Which individual entries produced this account balance?                | [General Ledger](/erpnext/general-ledger)                       | It lists debit and credit postings with their source vouchers.          |
| Do debit and credit balances agree at the end of the period?           | Trial Balance                                                   | It summarizes opening, period, and closing balances account by account. |
| What does the company own and owe on a particular date?                | Balance Sheet                                                   | It presents assets, liabilities, and equity at a point in time.         |
| Did the company earn a profit during the period?                       | Profit and Loss Statement                                       | It compares income with expenses for a period.                          |
| Why did cash increase or decrease even when the company made a profit? | Cash Flow                                                       | It explains cash movement through operations, investing, and financing. |
| Which customer invoices need collection follow-up?                     | [Accounts Receivable](/erpnext/accounts-receivable-and-payable) | It shows invoice-level outstanding balances and ageing.                 |
| Which supplier invoices should be paid next?                           | Accounts Payable                                                | It shows supplier balances, due dates, and ageing.                      |
| Why is an invoice still outstanding after a payment was recorded?      | [Payment Ledger](/erpnext/payment_ledger)                       | It shows invoice and payment allocations used by outstanding reports.   |


## Follow Nova's month-end review

The finance manager does not open every report at once. She begins with the broad result, identifies the number that needs explanation, and then moves to a more detailed report.

### Check whether the books balance

Start with Trial Balance after posting the period's invoices, payments, stock transactions, and adjustments. Opening Debit and Opening Credit show the position brought into the period. Debit and Credit show activity during the selected dates. Closing Debit and Closing Credit show the resulting balance.



The total debit and credit columns should agree because every submitted accounting transaction posts equal debits and credits. Agreement proves mathematical balance, but it does not prove that every transaction used the correct account. Use the General Ledger to investigate the composition of a suspicious balance.

### Explain an account with General Ledger

For 13 July to 13 August 2026, Nova's General Ledger contains Sales Invoice, stock, tax, and bank entries. One $20,000 sale debits Debtors and credits Sales. The same invoice credits Stock In Hand by $14,500 and debits Cost of Goods Sold by $14,500. This is why one sales invoice can create more than two ledger rows.

![General Ledger showing debit and credit rows created by Nova sales invoices](https://novacompanies.m.frappe.cloud/files/docs-accounting-reports-20260814-nova-industries-general-ledger.png)

The report totals show $395,762 of debits and $395,762 of credits. That confirms balance for the selected scope. To investigate the $229,000 sale, open its Voucher No. The voucher explains the business event, while the General Ledger explains its accounting effect.



Use the General Ledger for evidence and tracing. Use Trial Balance when you need one closing balance per account. Selecting different companies, dates, Finance Books, Cost Centers, Projects, or other [Accounting Dimensions](/erpnext/accounting-dimensions) can make two otherwise similar report runs show different totals.

### Decide what to collect with Accounts Receivable

Nova's Accounts Receivable report shows $249,212 outstanding from four customers as of 13 August 2026. The entire visible amount falls in the 0 to 30 day ageing bucket. This tells the finance manager that the invoices are recent. It does not automatically mean they are overdue because due dates and payment terms must also be considered.

![Accounts Receivable showing four customer balances in the 0 to 30 day ageing bucket](https://novacompanies.m.frappe.cloud/files/docs-accounting-reports-20260814-nova-industries-accounts-receivable.png)

The next action is to review Due Date and outstanding amount for each invoice. A payment that exists but remains unallocated may require [Payment Reconciliation](/erpnext/payment-reconciliation). An overdue customer may require a statement through [Process Statement of Accounts](/erpnext/process-statement-of-accounts) or a [Dunning](/erpnext/dunning) record.



Accounts Receivable is better than General Ledger for collection work because it keeps the invoice, payment allocation, due date, and ageing together. General Ledger remains the better report when the amount itself needs accounting investigation.

### Plan supplier payments with Accounts Payable

Nova's Accounts Payable report shows $184,293 outstanding to Summit Traders Ltd., Zuckerman Security Ltd., and MA Inc. in the 121 days and above bucket. Unlike the recent receivables, these balances are old and require immediate review.

![Accounts Payable showing three supplier balances aged more than 121 days](https://novacompanies.m.frappe.cloud/files/docs-accounting-reports-20260814-nova-industries-accounts-payable.png)

The finance manager should verify whether the invoices are genuinely unpaid, disputed, or already covered by an unallocated payment. After confirming the balances, she can create a [Payment Entry](/erpnext/payment-entry) for routine settlement or use a [Payment Order](/erpnext/payment-order) when several approved supplier payments need coordinated processing.

### Understand why profit and cash differ

Nova's Cash Flow report shows Profit for the year of $109,440, but Net Cash from Operations is negative $117,866. The largest visible reason is the $316,212 increase in Accounts Receivable. Revenue contributed to profit, but much of the cash has not yet been collected. The $184,293 increase in Accounts Payable offsets part of that pressure because Nova has not yet paid those suppliers.

![Cash Flow showing profit of 109440 dollars and negative operating cash flow of 117866 dollars](https://novacompanies.m.frappe.cloud/files/docs-accounting-reports-20260814-nova-industries-cash-flow-report.png)

This is the decision the reports enable: profit is positive, but collection must improve before Nova commits to additional cash spending. Profit and Loss explains whether the business earned money. Cash Flow explains why the bank position moved differently.

## Understand the core financial statements


| Statement                 | Period or date                                       | What to read                                                           | What it does not explain alone              |
| ------------------------- | ---------------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------- |
| Trial Balance             | A reporting period with opening and closing balances | Whether debit and credit totals agree and which accounts hold balances | Business meaning of each transaction        |
| Balance Sheet             | A point in time                                      | Assets, liabilities, equity, liquidity, and capital structure          | How profit was earned during the period     |
| Profit and Loss Statement | A period                                             | Income, cost of sales, operating expenses, and profit                  | Whether income has been collected in cash   |
| Cash Flow                 | A period                                             | Cash movement from operations, investing, and financing                | Invoice-level collection or payment details |


## Apply filters consistently


| Filter                                     | Why it matters                                                                                                       |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| Company                                    | Restricts the report to one legal entity. Use Consolidated Financial Statements for a group view.                    |
| Reporting dates or fiscal year             | Changes the activity and balances included in the result.                                                            |
| Finance Book                               | Includes entries belonging to the selected accounting book and can explain apparent differences between report runs. |
| Cost Center, Project, or another dimension | Shows only the selected operational slice rather than the whole company.                                             |
| Presentation currency                      | Changes displayed amounts without changing the underlying ledger entries.                                            |
| Include or exclude period-closing entries  | Changes whether closed income and expense balances are included in the view.                                         |


When two reports appear not to agree, first match Company, dates, Finance Book, dimensions, currency, and period-closing options. Then check whether one report shows activity during a period while the other shows a balance as of a date.

## Other useful accounting reports


| Decision                                                           | Report                                                    |
| ------------------------------------------------------------------ | --------------------------------------------------------- |
| Compare actual expenses with approved limits                       | [Budget Variance Report](/erpnext/budget-variance-report) |
| Review invoiced sales, purchases, and tax columns                  | Sales Register or Purchase Register                       |
| Review sales or purchase movement by item and period               | Item-wise register or invoice trend report                |
| Find ordered, delivered, or received items that still need billing | To Bill reports                                           |
| Compare several companies under one group                          | Consolidated Financial Statements                         |


## Troubleshooting

### Trial Balance and General Ledger appear different

Run both reports with the same Company, dates, Finance Book, dimensions, and period-closing treatment. Trial Balance separates opening, period, and closing values, while General Ledger lists individual postings. Previous fiscal years that have not been closed can also affect how income and expense balances appear.

### A financial statement is empty

Confirm that submitted transactions exist inside the selected company and period. Remove optional Finance Book and dimension filters one at a time, refresh the report, and verify that the underlying accounts use the correct root and report types.

### A report contains the right total but the wrong account

A balanced total cannot detect incorrect account selection. Open the amount in General Ledger, inspect the source voucher, and correct it through the supported cancellation and amendment or adjustment workflow.

### The report remains in a loading state

Reduce an unusually large period or filter scope and run it again. For large datasets, use the report's prepared-report option when available and wait for completion before interpreting or exporting it.

## Frequently asked questions

### Why can a profitable company have negative cash flow?

Profit records income and expenses when they are recognized. Cash Flow records when cash actually moves. Credit sales can increase profit before customers pay, while unpaid supplier bills can delay cash outflow.

### Which report should an auditor receive?

The exact package depends on the engagement. A common starting set includes Trial Balance, General Ledger, Balance Sheet, Profit and Loss Statement, Cash Flow, Accounts Receivable, Accounts Payable, and the source vouchers supporting material balances.

### Do filters change accounting entries?

Report filters change which entries are selected and how they are presented. They do not modify submitted ledger entries.

### Can I export a report before reviewing it?

ERPNext can export many reports, but first verify the Company, dates, currency, dimensions, grouping, and totals in the application. An export preserves a mistaken filter choice just as accurately as a correct one.

## Related topics

- [General Ledger](/erpnext/general-ledger)
- [Payment Ledger](/erpnext/payment_ledger)
- [Accounts Receivable and Payable](/erpnext/accounts-receivable-and-payable)
- [Financial Report Template](/erpnext/financial-report-template)
- [Accounting Dimensions](/erpnext/accounting-dimensions)
- [Finance Book](/erpnext/finance-book)
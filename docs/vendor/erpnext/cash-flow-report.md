---
title: "Cash Flow Report"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/cash-flow-report"
updated: "2026-08-14"
---

Nova Industries earned $109,440 in 2026, yet cash from operations fell by $117,866. The owner needs to understand where the profit went before approving more spending.



The Cash Flow report explains changes in cash and cash equivalents through operating, investing, and financing activities. It starts from accounting results and adjusts for non-cash items and working-capital movement. Use the [Profit and Loss Report](/erpnext/profit-and-loss-report) to measure earnings and the [Balance Sheet](/erpnext/balance-sheet) to review financial position.

## Run Cash Flow

1. Open **Accounting** and select **Cash Flow**.
2. Select **Nova Industries** and the required fiscal year or date range.
3. Choose periodicity and optional [Finance Book](/erpnext/finance-book), [Cost Center](/erpnext/cost-center), Project, Department, or [Accounting Dimension](/erpnext/accounting-dimensions).
4. Enable opening and closing balances when the cash reconciliation requires them.
5. Refresh and wait for totals, chart, and report sections to load.

![Loaded Nova Industries Cash Flow report showing negative operating cash flow](https://novacompanies.m.frappe.cloud/files/docs-20260814-nova-industries-cash-flow-loaded.png)

## Interpret Nova's cash movement


| Line                          | Value     | Interpretation                                             |
| ----------------------------- | --------- | ---------------------------------------------------------- |
| Profit for the year           | $109,440  | Accounting profit before cash-flow adjustments.            |
| Change in Accounts Receivable | -$316,212 | Income was recognized, but much of it remains uncollected. |
| Change in Accounts Payable    | $184,293  | Unpaid supplier balances temporarily preserved cash.       |
| Net Cash from Operations      | -$117,866 | Core operations consumed cash despite positive profit.     |


The largest pressure is receivables. Nova should review [Accounts Receivable](/erpnext/accounts-receivable), prioritize collections, and verify old balances before committing to new cash expenditure. Review [Accounts Payable](/erpnext/accounts-payable) before using delayed supplier payments as a source of cash.

## Understand the three sections


| Section   | Typical movements                                                                                   |
| --------- | --------------------------------------------------------------------------------------------------- |
| Operating | Profit, depreciation, receivables, payables, inventory, and taxes arising from ordinary operations. |
| Investing | Purchases and disposals of equipment, investments, and other long-term assets.                      |
| Financing | Owner capital, borrowings, repayments, dividends, and similar funding movements.                    |


## Trace a line to accounting evidence

Select an account or supporting value to inspect its [General Ledger](/erpnext/general-ledger) activity. Review source [Payment Entries](/erpnext/payment-entry) and approved [Journal Entries](/erpnext/journal-entry) when they explain a material movement. Working-capital lines are changes between reporting dates, so also compare the relevant Balance Sheet accounts and party reports.

![General Ledger report showing the accounting entries behind Cash Flow movements](https://novacompanies.m.frappe.cloud/files/docs-20260814-nova-industries-cash-flow-gl-evidence.png)

## Default and customised formats

The standard report classifies accounts using ERPNext's financial-statement logic. When the organisation needs approved labels or more precise classifications, configure [Customise Cash Flow Report](/erpnext/customise-cash-flow-report). A [Financial Report Template](/erpnext/financial-report-template) can control presentation where supported. Customisation changes classification and layout, not the underlying ledger entries.

## Troubleshooting

### Profit and operating cash flow differ sharply

Review receivables, payables, inventory, depreciation, taxes, and other non-cash or working-capital lines. The difference is often expected and should be explained, not forced to match.

### A cash movement is in the wrong section

Review the account's mapping and report configuration. Confirm whether a custom cash-flow format is enabled before changing any classification.

### Net change does not reconcile to cash balances

Match Company, dates, Finance Book, currency, dimensions, and opening or closing balance options. Look for omitted bank or cash accounts and overlapping custom mappings.

## Frequently asked questions

### Does positive profit guarantee positive cash flow?

Credit sales, inventory purchases, debt payments, asset purchases, and other timing differences can make cash flow negative while profit is positive.

### Is Accounts Payable growth always good for cash?

Unpaid bills preserve cash temporarily but create obligations and may harm supplier relationships. Interpret the change with due dates and payment plans.

### Does a report mapping change ledger entries?

Mappings change how existing balances are classified and displayed. They do not repost transactions.

## Related topics

- [Accounting Reports](/erpnext/accounting-reports)
- [Profit and Loss Report](/erpnext/profit-and-loss-report)
- [Balance Sheet](/erpnext/balance-sheet)
- [Accounts Receivable](/erpnext/accounts-receivable)
- [Accounts Payable](/erpnext/accounts-payable)
- [Customise Cash Flow Report](/erpnext/customise-cash-flow-report)
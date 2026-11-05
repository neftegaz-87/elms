---
title: "Balance Sheet"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/balance-sheet"
updated: "2026-08-14"
---

Nova Industries ends 2026 with $293,745 of assets, $184,305 of liabilities, and $109,440 of provisional profit. The owner wants to know what the business controls, what it owes, and why its bank balance is negative even though the company is profitable.



The Balance Sheet shows financial position at a point in time. Assets describe resources controlled by the business. Liabilities describe obligations. Equity and current profit explain the owners' residual interest. Use the [Profit and Loss Report](/erpnext/profit-and-loss-report) to explain how profit was earned during a period and [Cash Flow](/erpnext/cash-flow-report) to explain cash movement.

## Before you begin

Submit all relevant [Sales Invoices](/erpnext/sales-invoice), [Purchase Invoices](/erpnext/purchase-invoice), payments, stock transactions, assets, loans, payroll, depreciation, taxes, and approved [Journal Entries](/erpnext/journal-entry). Confirm that accounts have the correct Asset, Liability, or Equity root in the [Chart of Accounts](/erpnext/chart-of-accounts).

## Run the Balance Sheet

1. Open **Accounting** and select **Balance Sheet**.
2. Select **Nova Industries**.
3. Choose Fiscal Year or Date Range and the comparison periodicity.
4. Apply Finance Book, Cost Center, Project, Department, or another [Accounting Dimension](/erpnext/accounting-dimensions) only when required.
5. Refresh and wait for totals, chart, and account rows to load.

![Loaded Nova Industries Balance Sheet with assets liabilities and provisional profit](https://novacompanies.m.frappe.cloud/files/docs-20260814-nova-industries-balance-sheet-loaded.png)

## Interpret the Nova Industries result


| Section            | Value    | Meaning                                                           |
| ------------------ | -------- | ----------------------------------------------------------------- |
| Total Assets       | $293,745 | Resources controlled at the reporting date.                       |
| Total Liabilities  | $184,305 | Amounts owed to suppliers and other parties.                      |
| Equity             | $0       | Posted equity balances visible in the selected scope.             |
| Provisional Profit | $109,440 | Current-period profit not yet transferred through period closing. |


Assets equal liabilities plus equity and provisional profit: $293,745 equals $184,305 plus $109,440. This proves the statement balances mathematically. It does not prove that every account is correctly classified.

## Understand the account groups

Current Assets include balances expected to turn into cash or be used soon, such as receivables, bank, cash, and inventory. Fixed Assets support longer-term operations. Current Liabilities include obligations such as supplier payables and taxes. Longer-term loans belong in non-current liabilities. Equity contains owner capital, reserves, retained results, and period-closing transfers according to the organisation's account design.



Nova shows $316,212 in Accounts Receivable and a negative $118,104 Bank Accounts balance. The large receivable explains why the company can own net assets while still facing immediate cash pressure. Open [Accounts Receivable](/erpnext/accounts-receivable) to identify customers to collect from.

## Drill into a balance

Select an account amount to open its [General Ledger](/erpnext/general-ledger) entries. Keep Company, date, Finance Book, currency, and dimensions aligned with the Balance Sheet before comparing values.

![General Ledger drill-down opened from a Balance Sheet account](https://novacompanies.m.frappe.cloud/files/docs-20260814-nova-industries-balance-sheet-loaded-drilldown.png)

## Important filters


| Filter                        | Effect                                                                                             |
| ----------------------------- | -------------------------------------------------------------------------------------------------- |
| Reporting date or fiscal year | Sets the point in time and comparison columns.                                                     |
| Accumulated Values            | Shows balances accumulated through each displayed period.                                          |
| Finance Book                  | Restricts entries to a selected accounting book.                                                   |
| Dimensions                    | Shows the financial position for a selected operational segment when entries carry that dimension. |
| Currency                      | Changes presentation without changing ledger postings.                                             |
| Report Template               | Uses a configured [Financial Report Template](/erpnext/financial-report-template).                 |


## Troubleshooting

### The Balance Sheet does not balance

Check provisional profit, opening balances, account roots, period-closing entries, and identical report filters. Trace the difference through Trial Balance and General Ledger.

### An account appears in the wrong section

Review its Root Type and Report Type in Chart of Accounts. Correcting an account can affect reporting and should follow your accounting controls.

### A segment report looks incomplete

Transactions without the selected dimension are excluded. Verify dimension values on source entries before treating the filtered statement as a full-company balance sheet.

## Frequently asked questions

### Why is current profit shown separately from equity?

Profit remains provisional until the period is closed and transferred according to the configured closing process.

### Can a company be profitable but have a negative bank balance?

Profit includes income recognized before collection. Receivables, inventory, debt repayment, and other timing differences can consume cash.

### Does the Balance Sheet show market value?

The statement shows accounting balances produced by recorded transactions and valuation rules, not an automatic market valuation of the business.

## Related topics

- [Accounting Reports](/erpnext/accounting-reports)
- [Profit and Loss Report](/erpnext/profit-and-loss-report)
- [Cash Flow](/erpnext/cash-flow-report)
- [Trial Balance](/erpnext/trial-balance)
- [General Ledger](/erpnext/general-ledger)
- [Period Closing Voucher](/erpnext/period-closing-voucher)
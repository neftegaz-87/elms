---
title: "Period Closing Voucher\n"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/period-closing-voucher"
updated: "2026-08-14"
---

At year end, Nova Industries has finished invoicing, posted depreciation and accruals, reconciled its bank accounts, and reviewed receivables and payables. Its income and expense accounts still contain the year’s activity. A Period Closing Voucher transfers their net balance to an equity account so the next period starts with fresh Profit and Loss balances while Balance Sheet balances continue.



The voucher does not erase history or stop backdated entries. It creates balanced General Ledger entries. Use an [Accounting Period](/erpnext/accounting-period) or [Accounts Frozen Upto](/erpnext/freeze-accounting-entries) when the closed period must also be protected from later changes.

## Before you begin

- Complete bank, payment, stock, tax, depreciation, deferred accounting, accrual, and correction entries.
- Review the [Profit and Loss Statement](/erpnext/profit-and-loss-report), [Balance Sheet](/erpnext/balance-sheet), Trial Balance, Accounts Receivable, and Accounts Payable.
- Confirm the closing account with your accountant. It is commonly a Retained Earnings, Reserves and Surplus, or owner’s equity account.
- Take a backup and close only after the period’s adjustments are approved.

## Create a Period Closing Voucher

1. Open **Period Closing Voucher** and click **Add Period Closing Voucher**.
2. Select the company and the fiscal year being closed.
3. Set the posting date to the last day of the period.
4. Select the closing account that will receive the net profit or loss.
5. Enable **Book Cost Center Wise Profit/Loss** when retained earnings must preserve the cost center split.
6. Add a clear remark, save, review, and submit.

![Period Closing Voucher with the fiscal year and closing account highlighted](https://novacompanies.m.frappe.cloud/files/final-accounting-20260814-period-closing-voucher9ebf10.png)



## What submission posts


| Result for the period | Debit                                      | Credit                                     |
| --------------------- | ------------------------------------------ | ------------------------------------------ |
| Net profit            | Net balance of income and expense accounts | Closing equity account                     |
| Net loss              | Closing equity account                     | Net balance of income and expense accounts |


The entries reduce the period’s income and expense balances to zero and move the difference to equity. They do not close receivable, payable, bank, stock, asset, liability, or other Balance Sheet accounts.

![General Ledger showing the accounting effect of period closing](https://novacompanies.m.frappe.cloud/files/accounting-entries-20260802-accounting-entries-period-closing.png)



## If entries are posted after closing

ERPNext does not silently rewrite the submitted voucher. Complete the new approved adjustments and submit another Period Closing Voucher for the same fiscal year. The later voucher transfers only the remaining Profit and Loss balance.



Do not create a new opening entry every year. Opening entries are for migration or first-time setup. The previous year’s Balance Sheet balances carry forward through the ledger.

## Troubleshooting

### The closing balance is not what you expected

Run Profit and Loss with the same company, dates, Finance Book, and dimensions. Check draft or missing adjustments, unusual income and expense accounts, and entries posted after the earlier closing voucher.

### The voucher takes too long

Review the [Period Closing Voucher controller](/erpnext/legacy-controller-for-period-closing-voucher). Large ledgers can use batched background processing instead of one large database transaction.

## Frequently asked questions

### Does a Period Closing Voucher lock the year?

It transfers Profit and Loss balances. Use Accounting Period or the frozen-accounts date to restrict later postings.

### Can I close monthly or quarterly?

You can, but confirm the policy with your accountant. Year-end closing is the most common use, and extra vouchers add audit activity.

## Related topics

- [Accounting overview](/erpnext/accounting/introduction)
- [Chart of Accounts](/erpnext/chart-of-accounts)
- [General Ledger](/erpnext/general-ledger)
- [Fiscal Year](/erpnext/fiscal-year)
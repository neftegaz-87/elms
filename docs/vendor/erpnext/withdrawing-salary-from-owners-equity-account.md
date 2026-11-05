---
title: "Withdrawing Salary from Owner's Equity Account\n"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/withdrawing-salary-from-owners-equity-account"
updated: "2026-08-14"
---

Jordan Lee owns Nova Electronics Trading and wants to take $1,000 from the business for personal use. This is not payment for work performed by an employee. Recording it as salary expense would reduce Nova's profit and could misstate both management reports and tax records.



When the payment is legally an owner's draw, distribution, or dividend, record it against an Equity account instead of a salary Expense account. Nova uses **Dividends Paid** for this example because it already exists in the child company's approved Chart of Accounts. Ask a qualified accountant which equity account and tax treatment apply to your legal structure and jurisdiction.

## Before you begin

Confirm that the withdrawal is not payroll, reimbursement, a director loan, or repayment of money the owner previously advanced to the company. Those situations require different accounts and may require payroll or tax reporting.

- Identify the bank or cash account from which money will leave.
- Confirm the appropriate non-group Equity account with your accountant.
- Use a posting date in an open [Accounting Period](/erpnext/accounting-period).

## Check the equity account

Open the [Chart of Accounts](/erpnext/chart-of-accounts) for the company. Use an existing approved equity-withdrawal account, or ask an authorised accountant to create one under the Equity root.

![Nova Electronics Trading Chart of Accounts used to locate an equity withdrawal account](https://novacompanies.m.frappe.cloud/files/docs-accounting-reports-20260814-owner-draws-chart-of-accounts.png)

## Record the withdrawal

1. Open [Journal Entry](/erpnext/journal-entry) and create a new record.
2. Select Nova Electronics Trading and enter the posting date.
3. Debit **Dividends Paid - NET** by $1,000.
4. Credit **Nova Operating Bank - NET** by $1,000.
5. Add a clear remark identifying the transaction as an owner withdrawal, then save and submit.

![Submitted owner withdrawal Journal Entry debiting Dividends Paid and crediting Nova Operating Bank](https://novacompanies.m.frappe.cloud/files/docs-accounting-reports-20260814-owner-draw-journal-entry.png)

## Understand the accounting impact


| Account                    | Debit  | Credit | Effect                                                                  |
| -------------------------- | ------ | ------ | ----------------------------------------------------------------------- |
| Dividends Paid, Equity     | $1,000 |        | Reduces the owner's accumulated equity without creating salary expense. |
| Nova Operating Bank, Asset |        | $1,000 | Reduces the company's bank balance.                                     |


The entry does not affect the Profit and Loss Statement because neither row uses an income or expense account. It reduces Cash and Equity on the [Balance Sheet](/erpnext/accounting-reports). Verify the result in the [General Ledger](/erpnext/general-ledger) before relying on financial statements.

## Troubleshooting

### The withdrawal appears as salary expense

The debit row uses an Expense account. Cancel and amend the entry according to your controls, then use the approved Equity account after confirming the treatment with your accountant.

### The entry cannot be submitted

Check that debit and credit totals match, both accounts belong to the selected company, the posting period is open, and the bank account permits posting.

## Frequently asked questions

### Can every business owner use an owner's draw?

The permitted treatment depends on the entity type and local law. Corporations, partnerships, and sole proprietorships may treat payments to owners differently.

### Should I use Payment Entry instead?

A [Payment Entry](/erpnext/payment-entry) is normally used for customer, supplier, employee, or account transfers. A Journal Entry makes the equity debit and bank credit explicit for this accounting adjustment.

### Does this replace payroll?

Payments that are legally salary or wages must continue through the applicable payroll process. An owner withdrawal is not a shortcut around payroll obligations.

## Related topics

- [Journal Entry](/erpnext/journal-entry)
- [Chart of Accounts](/erpnext/chart-of-accounts)
- [General Ledger](/erpnext/general-ledger)
- [Payment Entry for Capital Account](/erpnext/payment-entry-for-capital-account)
- [Accounting Entries](/erpnext/accounting-entries)
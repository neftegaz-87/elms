---
title: "Invoice Discounting | ERPNext Documentation"
description: "Record invoice-backed short-term financing, disbursement, settlement, charges, and receivable accounts in ERPNext."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/invoice_discounting"
updated: "2026-08-01"
---

**Invoice Discounting** uses unpaid Sales Invoices as collateral for short-term financing from a Bank or finance company. ERPNext tracks the financed invoices, loan period, Bank charges, status, and the accounts used when financing is sanctioned, disbursed, and settled.

Use this feature only after finance has approved the accounting design. The receivable remains connected to the Customer while the financing creates a separate obligation to the lender.

## Before you begin

You need:

- one or more submitted [Sales Invoices](/erpnext/sales-invoice) with an outstanding balance;
- a Company Bank Account and Bank ledger;
- short-term loan and Bank charges accounts;
- Accounts Receivable credit, discounted, and unpaid accounts configured for the workflow;
- agreed financing amount, period, fees, recourse terms, and settlement process.

Test the complete lifecycle with finance before using it for live financing. The account names in examples are illustrative and must match your Chart of Accounts and policy.

## Create Invoice Discounting

1. Go to **Accounting &gt; Banking &gt; Invoice Discounting**.
2. Select **Add Invoice Discounting**.

![Invoice Discounting list with Add Invoice Discounting highlighted](https://novacompanies.m.frappe.cloud/files/banking-10-invoice-discounting-list.png)

3. Select the Company and enter the Posting Date.
4. Enter the **Loan Start Date** and **Loan Period (Days)**. Verify the calculated Loan End Date against the lender agreement.

![Invoice Discounting dates and loan period](https://novacompanies.m.frappe.cloud/files/banking-11-invoice-discounting-dates.png)

5. Select **Get Invoices** or add eligible Sales Invoices to the Invoices table.
6. Verify the Customer, date, outstanding amount, and receivable account for every row.
7. Select the highlighted pencil icon to open the full discounted-invoice row when you need to inspect row details.

![Discounted Sales Invoice row and pencil icon](https://novacompanies.m.frappe.cloud/files/banking-12-discounted-invoice-row.png)

8. Enter Bank charges and verify the Total Amount.
9. Select the **Short Term Loan Account**.

![Short-term loan account for Invoice Discounting](https://novacompanies.m.frappe.cloud/files/banking-13-invoice-discounting-loan-account.png)

10. Select the Bank Account that receives the disbursement.

![Bank Account for the financing disbursement](https://novacompanies.m.frappe.cloud/files/banking-13b-invoice-discounting-bank-account.png)

11. Select the Bank Charges Account and the three Accounts Receivable control accounts.

![Bank Charges Account for Invoice Discounting](https://novacompanies.m.frappe.cloud/files/banking-13c-invoice-discounting-charges-account.png)

12. Save and submit after the selected invoices and accounts have been reviewed.

## Important fields and what they mean


| Field                                  | What it controls                                                                     |
| -------------------------------------- | ------------------------------------------------------------------------------------ |
| Posting Date                           | Accounting date for the workflow action.                                             |
| Loan Start Date                        | Date financing begins.                                                               |
| Loan Period                            | Financing duration in days.                                                          |
| Loan End Date                          | Expected maturity or settlement date.                                                |
| Status                                 | Draft, Sanctioned, Disbursed, Settled, or Cancelled stage.                           |
| Invoices                               | Sales Invoices pledged or discounted. Each must have an eligible outstanding amount. |
| Total Amount                           | Total outstanding value represented by selected invoices.                            |
| Bank Charges                           | Fees deducted or charged by the financier.                                           |
| Short Term Loan Account                | Liability account for the financing obligation.                                      |
| Bank Account                           | Ledger receiving the disbursed funds.                                                |
| Bank Charges Account                   | Expense account for financing fees.                                                  |
| Accounts Receivable Credit Account     | Control account used when receivables are credited in the financing entries.         |
| Accounts Receivable Discounted Account | Tracks receivables assigned or discounted.                                           |
| Accounts Receivable Unpaid Account     | Tracks financed invoices that remain unpaid under the configured lifecycle.          |


## Status and lifecycle


| Status     | Operational meaning                                                            |
| ---------- | ------------------------------------------------------------------------------ |
| Draft      | Financing proposal is being prepared and has not posted the lifecycle actions. |
| Sanctioned | Lender has approved the facility or selected invoices.                         |
| Disbursed  | Funds have been received and the financing obligation is active.               |
| Settled    | Customer receipt and lender settlement have completed the financing lifecycle. |
| Cancelled  | The arrangement was canceled under ERPNext cancellation rules.                 |


Use the actions available on the document to move through sanctioned, disbursed, and settled stages. Review every generated [Journal Entry](/erpnext/journal-entry) and [Payment Entry](/erpnext/payment-entry) before submission.

## When the Customer pays

Record the Customer receipt using the agreed collection route. Depending on whether the Customer pays your Company or the lender, the accounting and bank movement may differ. Follow the facility agreement and the configured ERPNext workflow.

After collection:

1. allocate the receipt to the correct Sales Invoice;
2. settle the lender liability and fees;
3. update the Invoice Discounting status;
4. confirm that the Customer outstanding, discounted receivable, Bank, and loan balances are correct;
5. reconcile the bank statement.

Use [Payment Reconciliation](/erpnext/payment-reconciliation) only when allocations need adjustment. Do not use reconciliation to hide an incorrect accounting entry.

## Controls and reporting

Maintain evidence for lender approval, disbursement, charges, pledged invoices, Customer receipts, and settlement. Reconcile:

- the Invoice Discounting register to short-term loan balances;
- discounted and unpaid receivable accounts to individual invoices;
- disbursement and settlement to [Bank Transactions](/erpnext/bank-transaction);
- charges to lender statements and agreements;
- maturity dates to open facilities.

Prevent the same Sales Invoice from being financed twice unless the product and agreement explicitly support it and the remaining eligible balance is clear.

## Troubleshooting

### Get Invoices returns no records

Confirm that Sales Invoices are submitted, belong to the selected Company, have an outstanding balance, and are not already fully allocated to another discounting record.

### An account cannot be selected

Check its Company, root type, group status, and currency. Use ledger accounts, not groups, and confirm the account purpose with finance.

### The disbursed amount differs from the invoice total

Review Bank charges, holdbacks, advance rates, and lender deductions. Record each difference in the correct account instead of forcing the Bank amount to equal the gross invoice value.

### The Customer paid after the loan maturity date

Follow the lender agreement for interest, penalties, or recourse. Record additional charges separately and settle the open liability using supported vouchers.

## Frequently asked questions

### Does Invoice Discounting sell the invoice?

Not always. The legal and accounting substance depends on the agreement, recourse, control, and local standards. Confirm treatment with finance and auditors.

### Can several invoices be financed together?

They can when eligible. Add each invoice row and verify the outstanding amount and Customer.

### Does creating the record receive money automatically?

It does not at the draft stage. Use the documented lifecycle action and verify the generated accounting entries when funds are disbursed.

## Related topics

- [Sales Invoice](/erpnext/sales-invoice)
- [Bank Account](/erpnext/bank-account)
- [Payment Entry](/erpnext/payment-entry)
- [Journal Entry](/erpnext/journal-entry)
- [Payment Reconciliation](/erpnext/payment-reconciliation)
- [Bank Reconciliation](/erpnext/bank-reconciliation)
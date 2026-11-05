---
title: "Accounts Receivables | ERPNext Documentation"
description: "Review customer outstanding balances, ageing, payments, and credits with the Accounts Receivable report in ERPNext."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/accounts-receivables"
updated: "2026-08-14"
---

Nova Industries has submitted invoices to several customers. The sales total shows how much was billed, but the collections team needs a different answer: who still owes money, which invoices are overdue, and where an existing payment or credit has not been allocated correctly?



The **Accounts Receivable** report brings every open customer receivable into one view. It shows the original invoiced amount, payments and Credit Notes already allocated, the remaining outstanding amount, the due date, and how long the balance has been open.



For example, the report can show that Northstar Retail still owes part of an invoice while another customer has an unallocated advance. Use it to prioritize collection follow-up, investigate mismatched allocations, and estimate incoming cash before opening the exact invoice or payment that needs attention.

## Before you begin

Submit your [Sales Invoices](/erpnext/sales-invoice) and record customer receipts through [Payment Entries](/erpnext/payment-entry). Draft transactions do not affect the receivable balance. Also confirm that the report date and Company are correct.

## Run the report

1. Search for **Accounts Receivable**.
2. Select the **Company** and **Posting Date**.
3. Add filters such as Customer, Receivable Account, Cost Center, Project, Territory, or Customer Group when you need a narrower view.
4. Review the invoice rows and the total outstanding amount.

![Accounts Receivable report with populated customer balances](https://novacompanies.m.frappe.cloud/files/accounts-receivables-accounts-receivable-report575529.png)

## Understand the columns


| Column             | What it means                                                       |
| ------------------ | ------------------------------------------------------------------- |
| Posting Date       | Date on which the accounting entry was posted                       |
| Party              | Customer that owes the amount                                       |
| Voucher No         | Sales Invoice, Journal Entry, or other source transaction           |
| Due Date           | Date by which payment was expected                                  |
| Invoiced Amount    | Original receivable created by the voucher                          |
| Paid Amount        | Amount already allocated against the voucher                        |
| Credit Note        | Credit already allocated against the voucher                        |
| Outstanding Amount | Amount still open after payments and credits                        |
| Age (Days)         | Number of days used for ageing                                      |
| Ageing buckets     | Outstanding amount grouped into periods such as 0–30 and 31–60 days |


The report can show a negative balance when a customer has an unallocated advance or credit. It can also show an old invoice as outstanding when a payment exists but has not been allocated to that invoice.

## Accounts Receivable Summary

Use **Accounts Receivable Summary** when you need one consolidated line per customer instead of invoice-level detail. It is useful for collection meetings and customer-level exposure checks. Return to the detailed report before taking action so you can identify the exact vouchers involved.

## Follow up on overdue balances

- Open the Sales Invoice from **Voucher No** to review its payment schedule.
- Use [Process Statement Of Accounts](/erpnext/process-statement-of-accounts) to send statements to several customers.
- Create a [Dunning](/erpnext/dunning) against an overdue invoice when you need a formal reminder with interest or fees.
- Use [Payment Reconciliation](/erpnext/payment-reconciliation) when a receipt or credit exists but is not allocated to the correct invoice.
- Create a [Credit Note](/erpnext/credit-note) for an approved return or invoice reduction.

## Common issues

**A submitted payment is not reducing the invoice**

Check whether the Payment Entry references that invoice. If it is unallocated, reconcile it against the invoice.

**The report does not match the General Ledger**

Confirm Company, date, currency, party, and receivable account filters. The Accounts Receivable report is voucher-oriented, while the [General Ledger](/erpnext/general-ledger) shows individual ledger postings.

**An invoice appears in the wrong ageing bucket**

Check whether ageing is based on Due Date or Posting Date, then review the invoice payment schedule.

## Related topics

- [Sales Invoice](/erpnext/sales-invoice)
- [Payment Entry](/erpnext/payment-entry)
- [Credit Note](/erpnext/credit-note)
- [Process Statement Of Accounts](/erpnext/process-statement-of-accounts)
- [Sales Interest / Dunning](/erpnext/dunning)
- [Accounts Receivable and Payable report](/erpnext/accounts-receivable-and-payable)
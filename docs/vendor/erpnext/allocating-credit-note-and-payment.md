---
title: "Allocating a Credit Note and Payment | ERPNext Documentation"
description: "Allocate customer payments and credit notes against outstanding sales invoices with ERPNext Payment Reconciliation."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/allocating-credit-note-and-payment"
updated: "2026-07-31"
---

Allocate a Credit Note or unallocated customer payment when the credit should settle a specific Sales Invoice. Allocation updates the outstanding amounts without creating another sale or payment.

## Before you begin

Confirm that the Sales Invoice, Credit Note, and Payment Entry are submitted for the same Customer, Company, currency, and receivable account. The credit or payment must still have an unallocated amount.

## Allocate with Payment Reconciliation

1. Search for **Payment Reconciliation**.
2. Select the Company, Party Type **Customer**, Customer, and receivable account.
3. Fetch unallocated payments and invoices.
4. Select the Credit Note or Payment Entry in the payments section.
5. Select the Sales Invoice in the invoices section.
6. Enter the amount to allocate.
7. Review the remaining unallocated and outstanding amounts.
8. Select **Reconcile**.

The Payment Reconciliation tool places open invoices and available payments or Credit Notes side by side. Select only the entries that should be matched before allocating the amount.



![Payment Reconciliation with open Sales Invoices and an unallocated customer payment](https://novacompanies.m.frappe.cloud/files/sales-receivables-allocating-credit-note-and-payment-payment-reconciliation.png)

You may allocate one payment across several invoices or combine several credits against one invoice, provided the allocation does not exceed the available or outstanding amount.

## Verify the result

Open the [Accounts Receivable](/erpnext/accounts-receivables) report and confirm:

- the Sales Invoice outstanding amount has reduced;
- the Credit Note or Payment Entry unallocated amount has reduced;
- the Customer's total balance is unchanged by the allocation itself.

Allocation matches existing debit and credit entries. It does not post new income, tax, stock, or cash movement.

## When to use a Journal Entry

Use a Journal Entry only when the accounting adjustment cannot be represented by Payment Reconciliation. Add the Customer as Party and select the correct Sales Invoice or Credit Note in **Reference Type** and **Reference Name**. Missing references leave the vouchers open even when the account balance appears correct.

## Troubleshooting

**The credit or invoice does not appear**

Check submission status, Customer, Company, currency, receivable account, and remaining unallocated or outstanding amount.

**The ledger balances but the invoice stays unpaid**

The entry probably lacks the invoice reference. Reconcile the payment or correct the referenced Journal Entry.

**The wrong allocation was made**

Use the supported unreconcile action where available, then reconcile the correct vouchers. Do not cancel unrelated sales documents.

## Related topics

- [Credit Note](/erpnext/credit-note)
- [Payment Entry](/erpnext/payment-entry)
- [Payment Reconciliation](/erpnext/payment-reconciliation)
- [Accounts Receivables](/erpnext/accounts-receivables)
- [Journal Entry](/erpnext/journal-entry)
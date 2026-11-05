---
title: "Sales Interest and Dunning | ERPNext Documentation"
description: "Set up formal overdue-payment reminders with interest, fees, letter text, and payment processing in ERPNext."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/dunning"
updated: "2026-08-14"
---

Northstar Retail has not paid an invoice by its due date. Nova Industries can see the overdue balance in Accounts Receivable, but the customer now needs a formal notice that states what is overdue, the interest or reminder fee being charged, and the amount required to settle it.



A **Dunning** turns that overdue balance into a traceable collection document. It brings the relevant Sales Invoice instalments into a formal reminder, calculates optional interest and fees, stores the letter sent to the Customer, and links the eventual payment back to the demand.



Use Dunning when ordinary follow-up is no longer enough and your collection policy requires a formal reminder. It does not replace the Sales Invoice or create another sale. This guide explains how to configure reusable Dunning Types, issue the notice, and record the payment that resolves it.

## Before you begin

- The [Sales Invoice](/erpnext/sales-invoice) must be submitted and overdue.
- Create at least one Dunning Type.
- Choose the income account and Cost Center that should receive interest and dunning fees.

## Set up a Dunning Type

A Dunning Type stores reusable defaults for the reminder. Create different types for stages such as first reminder, second reminder, and final notice.


| Field                       | What it controls                                  |
| --------------------------- | ------------------------------------------------- |
| Is Default                  | Applies this type automatically when appropriate  |
| Dunning Fee                 | Fixed charge added to the reminder                |
| Rate of Interest (%) Yearly | Annual rate used to calculate interest            |
| Dunning Letter              | Language-specific body and closing text           |
| Income Account              | Account credited when fees and interest are paid  |
| Cost Center                 | Cost Center used for the fee and interest posting |


![Dunning Type with fee, interest, reminder text, and accounting defaults](https://novacompanies.m.frappe.cloud/files/dunning-type-clean.png)

## Create a Dunning

### From an overdue Sales Invoice

1. Open the overdue Sales Invoice.
2. Select **Create &gt; Dunning**.
3. Review the overdue payment schedule rows fetched into the document.
4. Select a **Dunning Type**, or enter the fee, interest, and letter text manually.
5. Save and submit.

### From the Dunning list

1. Open the Dunning list and select **Add Dunning**.
2. Select the Customer.
3. Select **Fetch Overdue Payments**.
4. Choose the overdue rows and select **Get Items**.
5. Complete the reminder details, then save and submit.

The Dunning must reflect the amount you intend to collect. Review the invoice rows, interest, fee, total outstanding, income account, and Cost Center before submission.

## Record payment

When the customer pays the invoice together with the interest and fee:

1. Open the submitted Dunning.
2. Select **Create &gt; Payment**.
3. Review the referenced invoices and the additional amount.
4. Submit the Payment Entry.

ERPNext records the interest and fee through the deductions or loss section of the Payment Entry and resolves the Dunning after the full amount is received.

## Statuses


| Status     | Meaning                                                   |
| ---------- | --------------------------------------------------------- |
| Draft      | Reminder has not been submitted                           |
| Unresolved | Submitted, but the required payment has not been received |
| Resolved   | Outstanding amount, interest, and fee have been settled   |
| Cancelled  | Submitted Dunning was cancelled                           |


## Troubleshooting

**Create Dunning is not available**

Confirm that the Sales Invoice is submitted, has an outstanding amount, and is past its due date.

**Interest or fee posts to the wrong account**

Review the Income Account and Cost Center on both the Dunning Type and the Dunning before creating the Payment Entry.

**The Dunning remains unresolved**

Open the linked Payment Entry and verify that it is submitted and covers all referenced invoice, interest, and fee amounts.

## Related topics

- [Sales Invoice](/erpnext/sales-invoice)
- [Payment Entry](/erpnext/payment-entry)
- [Accounts Receivables](/erpnext/accounts-receivables)
- [Process Statement Of Accounts](/erpnext/process-statement-of-accounts)
- [Payment Terms](/erpnext/payment-terms)
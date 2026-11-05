---
title: "Purchase Invoice | ERPNext Documentation"
description: "Create, verify, submit, pay, return, and track supplier Purchase Invoices in ERPNext."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/purchase-invoice"
updated: "2026-08-14"
---

Apex Components, a supplier to Nova Industries, sends a bill for phone screens that have already been received. Until that bill is recorded, Nova Industries has stock but no formal payable showing how much it owes the supplier.



A Purchase Invoice records the supplier's bill, creates the payable, and posts the expense, asset value, and taxes. It can be created from a Purchase Order, a Purchase Receipt, or entered directly.



Use a Purchase Invoice when a supplier has billed your company for goods or services. Submission updates the supplier balance and the General Ledger.



## Before you begin

You need:

- a [Supplier](/erpnext/supplier) with the correct currency and payment terms;
- Items or expense accounts for the purchase;
- a Company with a default payable account and Cost Center;
- applicable [Purchase Taxes and Charges Templates](/erpnext/purchase-taxes-and-charges-template);
- a Purchase Order or Purchase Receipt when the invoice must update an earlier buying document.

Confirm whether the goods have already been received. If a Purchase Receipt exists, invoice from it. If goods and the bill arrive together, you may use **Update Stock** on the Purchase Invoice instead of creating a separate receipt.

## Create a Purchase Invoice

1. Go to **Accounting &gt; Purchase Invoice**.
2. Select **Add Purchase Invoice**.

![Purchase Invoice list with Add Purchase Invoice highlighted](https://novacompanies.m.frappe.cloud/files/purchase-payables-01-purchase-invoice-list.png)

3. Select the **Supplier**. ERPNext fetches the payable account, currency, price list, addresses, and payment terms from the relevant defaults.
4. Enter the Supplier's invoice number in **Supplier Invoice No** and its date in **Supplier Invoice Date**. Use the date printed on the Supplier's bill, not the date on which you enter it.
5. Review the **Posting Date** and **Due Date**.

![Supplier, bill reference, and due date on a Purchase Invoice](https://novacompanies.m.frappe.cloud/files/purchase-payables-02-supplier-bill-and-dates.png)

6. Add the Items. Enter the billed quantity and rate, then verify the expense account, Cost Center, Warehouse, and tax treatment.

The colored dot before an Item Code shows stock availability at a glance. Green means in stock and red means out of stock.

Select the highlighted pencil icon to open the full Item row. This is where you can review fields that are not shown as columns in the table.

![Purchase Invoice Items table with the row pencil highlighted](https://novacompanies.m.frappe.cloud/files/purchase-payables-03-items-and-edit-row.png)

Check the **Accepted Qty**, **Rate**, UOM, expense account, Cost Center, and any linked Purchase Order or Purchase Receipt row. ERPNext calculates the amount from the quantity and rate.

![Quantity and rate in a Purchase Invoice Item row](https://novacompanies.m.frappe.cloud/files/purchase-payables-04-item-quantity-and-rate.png)

7. Review taxes, discounts, additional charges, payment schedule, rounding, and the Grand Total.
8. Save the draft and compare it with the Supplier's bill.
9. Select **Submit** when the document is correct.

## Alternative ways to create a Purchase Invoice

### From a Purchase Order

Open a submitted Purchase Order and select **Create &gt; Purchase Invoice**. ERPNext copies the Supplier, Items, quantities, rates, taxes, and references. Adjust only the quantities that are being billed now. This method updates the order's billed percentage after submission.

Use this route when the invoice arrives before receipt, or when your business does not use Purchase Receipts for that purchase.

### From a Purchase Receipt

Open a submitted Purchase Receipt and select **Create &gt; Purchase Invoice**. This carries the received quantities and receipt references into the invoice. The invoice normally clears the **Stock Received But Not Billed** value created by the receipt and establishes the Supplier payable.

This is the preferred route when receiving and invoice verification are separate responsibilities.

### Using Get Items From

In a new Purchase Invoice, select **Get Items From** to fetch one or more eligible Purchase Orders or Purchase Receipts for the same Supplier. Use this when a single Supplier invoice covers several orders or receipts.

### Direct Purchase Invoice

Create the invoice directly when there is no preceding order or receipt, such as a utility bill, professional service, rent, or a small approved expense. A direct invoice creates the payable but does not update a Purchase Order's billed status.

### Recurring supplier invoices

Use [Auto Repeat](/erpnext/auto-repeat) or a Supplier [Subscription](/erpnext/subscription) for recurring charges. Choose Auto Repeat when you want scheduled copies of a reference document. Choose Subscription when billing follows a defined subscription plan and service period.

## Important fields and what they mean


| Field                        | What it controls                                                                                                                                 |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Supplier                     | The party to whom the amount is payable. It also provides currency, payable account, tax, and payment defaults.                                  |
| Supplier Invoice No          | The Supplier's own bill reference. It helps prevent duplicate entry and supports audit matching.                                                 |
| Supplier Invoice Date        | The date on the Supplier's bill. Use it for document reference and ageing controls.                                                              |
| Posting Date and Time        | The accounting and optional stock posting date. Closed periods and frozen accounts can restrict it.                                              |
| Due Date                     | The date by which payment is expected. Payment terms can calculate it automatically.                                                             |
| Credit To                    | The payable ledger credited when the invoice is submitted. Normally use a common payable account with the Supplier recorded as the party.        |
| Update Stock                 | Posts receipt of stock through the Purchase Invoice. Leave it clear when a Purchase Receipt already records the stock movement.                  |
| Is Paid                      | Records payment with the invoice when this workflow is enabled and the required payment account is selected.                                     |
| Is Return (Debit Note)       | Converts the Purchase Invoice into a Debit Note that reduces or reverses a Supplier bill.                                                        |
| Apply Tax Withholding Amount | Calculates configured Supplier withholding tax. Verify the category and applicable threshold before submission.                                  |
| Items                        | The products, services, assets, or expenses being billed. Each row can carry its own account, Warehouse, Cost Center, Project, and tax template. |
| Taxes and Charges            | Tax, freight, duty, and other additions or deductions. The charge type determines how each row is calculated.                                    |
| Payment Schedule             | Splits the amount across one or more due dates based on payment terms.                                                                           |
| Accounting Dimensions        | Attributes such as Cost Center, Project, Branch, or custom dimensions used for reporting and controls.                                           |
| On Hold                      | Prevents the invoice from being selected for payment until the hold is released.                                                                 |


## Taxes, currency, and additional charges

Select the correct buying price list and transaction currency before adding Items. ERPNext stores the exchange rate used to convert the invoice into Company currency. Review it when the invoice is in a foreign currency.

Apply the correct tax template or add tax rows manually. Charges can be based on Net Total, a previous row, Actual amount, or other supported calculation types. Check whether freight or duty should affect Item valuation. Use a [Landed Cost Voucher](/erpnext/landed-cost-voucher) when additional costs must be allocated after receipt.

For country-specific taxes, use the regional documentation and fields supplied by the installed localization. Do not copy tax examples from another jurisdiction without confirming the legal and accounting treatment.

## Submit and next steps

Submitting a Purchase Invoice normally:

- credits the Supplier payable account;
- debits expense, asset, stock, or Stock Received But Not Billed accounts based on the workflow;
- posts tax and additional-charge ledgers;
- updates billed quantities on linked Purchase Orders or Purchase Receipts;
- creates Payment Ledger entries used by Accounts Payable and reconciliation.

After submission, use **Create &gt; Payment** to make a [Payment Entry](/erpnext/payment-entry). You can also include the invoice in a [Payment Order](/erpnext/payment-order), reconcile an existing payment, place it on hold, or create a return.

To reduce or reverse the bill, open the submitted invoice and select **Create &gt; Return / Debit Note**.

![Create Return or Debit Note from a submitted Purchase Invoice](https://novacompanies.m.frappe.cloud/files/purchase-payables-05-create-debit-note.png)

Use **View &gt; Accounting Ledger** to inspect the General Ledger effect. If stock was updated, review the Stock Ledger as well.

## Status


| Status            | Meaning                                                                                        |
| ----------------- | ---------------------------------------------------------------------------------------------- |
| Draft             | Saved but not posted to the ledgers.                                                           |
| Unpaid            | Submitted with an outstanding payable amount.                                                  |
| Partly Paid       | Payments or credits cover only part of the invoice.                                            |
| Paid              | The outstanding amount is zero.                                                                |
| Overdue           | The invoice remains outstanding after its due date.                                            |
| Return            | The document is a submitted Debit Note.                                                        |
| Debit Note Issued | A Debit Note has been created against the invoice.                                             |
| Canceled          | The submitted document was canceled and its ledger effect reversed according to ERPNext rules. |


## Troubleshooting

### The invoice duplicates stock value

Check whether a Purchase Receipt already exists. Do not enable **Update Stock** on the Purchase Invoice when the receipt already posted the same stock movement.

### A Purchase Order or Purchase Receipt is missing from Get Items From

Confirm that it is submitted, belongs to the same Supplier and Company, has a billable balance, and is not closed. Also verify user permissions.

### The expense account is unexpected

ERPNext can fetch it from the Item, Item Group, Company defaults, or linked receipt accounting. Open the Item row and verify the account and accounting dimensions before submission.

### Payment cannot be created

Confirm that the invoice is submitted, not on hold, has an outstanding amount, and uses a payable account valid for the Supplier and Company.

### Supplier invoice number is rejected as a duplicate

Search existing Purchase Invoices for the same Supplier and bill number. Do not change the reference only to bypass the warning. Confirm whether the bill was already entered.

## Frequently asked questions

### Can I invoice only part of a Purchase Order?

You can. Create the Purchase Invoice from the order and retain only the quantity billed now. Later invoices can bill the remaining quantity.

### Should services use Update Stock?

They should not. Service Items do not require a stock receipt. Post them to the appropriate expense or asset account.

### Can one Purchase Invoice cover several Purchase Receipts?

You can. Use **Get Items From &gt; Purchase Receipt** and select eligible receipts for the same Supplier.

### Can I edit a submitted Purchase Invoice?

Submitted accounting fields are protected. Use Cancel and Amend when permitted, or issue a Debit Note when you need a traceable reduction or return.

## Related topics

- [Purchase Order](/erpnext/purchase-order)
- [Purchase Receipt](/erpnext/purchase-receipt)
- [Debit Note](/erpnext/debit-note)
- [Payment Entry](/erpnext/payment-entry)
- [Accounts Payable](/erpnext/accounts-payable)
- [Purchase Taxes and Charges Template](/erpnext/purchase-taxes-and-charges-template)
- [Landed Cost Voucher](/erpnext/landed-cost-voucher)
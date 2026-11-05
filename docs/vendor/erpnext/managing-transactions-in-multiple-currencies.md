---
title: "Managing Transactions in Multiple Currencies | ERPNext Documentation"
description: "Create, review, print, pay, and verify foreign-currency sales and purchase transactions in ERPNext."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/managing-transactions-in-multiple-currencies"
updated: "2026-08-14"
---

Nova Industries distributes electronics internationally while keeping its Company accounts in USD.



EuroTech Retail wants to receive and pay a EUR invoice, while Nova must keep its books in USD. Users need to enter, print, collect, and reconcile the sale in EUR without losing the USD value required for accounting.



This guide follows a EUR 1,200 Sales Invoice at `1 EUR = 1.15 USD`. The customer sees EUR 1,200 while ERPNext records USD 1,380 in Company currency. You will see where the currencies and rates come from, how payment is converted, and how to verify the result. The same controls apply to purchases through the corresponding Supplier and payable fields.

## Before you begin

Complete [Multi Currency Setup](/erpnext/multi-currency-setup):

- EUR is enabled in [Currency](/erpnext/currency).
- EuroTech Retail has Billing Currency EUR.
- Euro Receivables is a EUR Receivable [Account](/erpnext/chart-of-accounts) linked to the Customer.
- Nova Europe EUR is an enabled selling [Price List](/erpnext/price-lists).
- A dated EUR to USD rate exists in [Currency Exchange](/erpnext/currency-exchange), or the configured provider covers it.
- The Company has an Exchange Gain/Loss account.

Test the full invoice and payment cycle in Draft before using imported or live data.

## Create a foreign-currency Sales Invoice

1. Open Accounting &gt; Sales and Receivables &gt; Sales Invoice.
2. Select **Add Sales Invoice**.
3. Choose Nova Electronics Distribution and EuroTech Retail.
4. Confirm the Posting Date, Payment Due Date, and EUR Currency.
5. Review the Exchange Rate field. Its label states the direction.
6. Select Nova Europe EUR and confirm Price List Currency EUR.
7. Add the item, quantity, and rate.
8. Review taxes, payment terms, and totals.

![EUR transaction and price-list rates](https://novacompanies.m.frappe.cloud/files/docs-multi-currency-2026-sales-invoice-eur-currency-rate.png)

The screenshot shows two rates:


| Field                    | Purpose in this example                                                             |
| ------------------------ | ----------------------------------------------------------------------------------- |
| Exchange Rate            | Converts the EUR transaction total to the USD Company value. `1 EUR = 1.15 USD`.    |
| Price List Exchange Rate | Converts Price List currency to transaction currency. It is 1 because both are EUR. |


An Actual tax or charge entered directly on the transaction is entered in the transaction currency. Review calculated taxes and Company-currency equivalents according to the tax template and charge type.

## Confirm the receivable account

Open the Accounting section and check **Debit To**. It should be Euro Receivables for this Customer and Company.



![EUR receivable selected on the Sales Invoice](https://novacompanies.m.frappe.cloud/files/docs-multi-currency-2026-sales-invoice-eur-receivable-account.png)

If the selected account is in a foreign currency, the invoice currency must normally match it. Do not switch only the Currency field and ignore Debit To.

## Compare transaction and Company totals

Before submission, compare the party-facing total and the Company-currency total.



![EUR and USD Sales Invoice totals](https://novacompanies.m.frappe.cloud/files/docs-multi-currency-2026-sales-invoice-eur-totals.png)

For EUR 1,200 at 1.15:


| View                        | Amount    |
| --------------------------- | ---------: |
| Customer invoice total      | EUR 1,200 |
| Company-currency total      | USD 1,380 |
| Receivable account currency | EUR       |


Submit only after the rate, account, prices, taxes, and terms are correct. The submitted [Sales Invoice](/erpnext/sales-invoice) retains these values even if a later Currency Exchange record changes.

## Print and send the invoice

Open Print or Preview and confirm that rates, amounts, totals, and amount in words use the expected party-facing currency. The print format should show EUR for the invoice values. Company-currency fields are accounting fields and do not normally replace the agreed invoice currency in the customer-facing document.

If the symbol or number separators are wrong, correct the Currency master or site number format rather than hard-coding symbols into every print format.

## Create the Payment Entry

Create the Payment Entry from the submitted invoice when possible:

1. Open the invoice and select Create &gt; Payment.
2. Confirm Payment Type **Receive** and the Customer.
3. Confirm **Paid From** is the EUR receivable account.
4. Select the actual bank account under **Paid To**.
5. Enter the amount received in the bank account currency.
6. Review Source Exchange Rate and the Company-currency amount.
7. Confirm the invoice reference and allocated amount.

![Account currencies in Payment Entry](https://novacompanies.m.frappe.cloud/files/docs-multi-currency-2026-payment-entry-two-account-currencies.png)



![Paid and received amounts with the source rate](https://novacompanies.m.frappe.cloud/files/docs-multi-currency-2026-payment-entry-exchange-rates-and-amounts.png)

The paid-from and paid-to account currencies control the amount fields. In the example, EUR 1,200 is cleared from the receivable and USD 1,380 is received into the operating bank.

If the payment-date rate differs from the invoice rate, use [Manage Foreign Exchange Difference](/erpnext/manage-foreign-exchange-difference). Keep bank charges, withholding, write-offs, and exchange difference in their appropriate accounts.

## Enter a foreign-currency purchase

On a [Purchase Invoice](/erpnext/purchase-invoice), select the Supplier, EUR, the buying Price List, and the EUR payable account. Review the Exchange Rate and Price List Exchange Rate exactly as on the sales side.



![EUR Purchase Invoice conversion fields](https://novacompanies.m.frappe.cloud/files/docs-multi-currency-2026-purchase-invoice-eur-currency-rate.png)

On submission, the payable outstanding is maintained according to the party account currency. Create a Pay-type Payment Entry and verify the amount removed from the bank and the EUR amount cleared from the payable.

## Transactions in several currencies for one party

Accounts Settings includes **Allow multi-currency invoices against single party account**.



![Allow invoices in multiple currencies against one party account](https://novacompanies.m.frappe.cloud/files/docs-multi-currency-2026-accounts-settings-multi-currency-invoices.png)

This can support a party invoiced in multiple currencies while using a Company-currency party account. It does not make a bank account multi-currency, and it can make outstanding and payment interpretation harder. Use dedicated currency accounts for currencies that the business regularly holds or reconciles. Test [Payment Reconciliation](/erpnext/payment-reconciliation), ageing, credit notes, advances, and returns before enabling the option broadly.

## Verify reports

Use the [General Ledger](/erpnext/general-ledger) filtered by the foreign account. It shows debit, credit, and balance in account currency when appropriate.



![EUR bank balance in the General Ledger](https://novacompanies.m.frappe.cloud/files/docs-multi-currency-2026-foreign-currency-general-ledger.png)

Review [Accounts Receivable and Payable](/erpnext/accounts-receivable-and-payable) in the party or account currency. Financial statements use Company currency. At period end, run [Exchange Rate Revaluation](/erpnext/exchange-rate-revaluation) for eligible open foreign balances.

## Troubleshooting

### Currency changes but item rates look wrong

Check Price List, Price List Currency, and Price List Exchange Rate. The transaction Exchange Rate does not necessarily convert the source Item Price.

### The invoice cannot be saved because account currency differs

Use the matching receivable or payable account, or correct the party's per-Company default. Do not change an account currency after postings exist.

### Payment Entry receives the wrong USD amount

Check the paid-to bank currency, source or target rate, paid amount, received amount, and invoice allocation. Use the actual bank amount and account for legitimate differences separately.

### The printed currency differs from the agreement

Verify the submitted transaction Currency and Price List. Then inspect the print format for hard-coded symbols or base-currency fields.

## FAQs

### Can I omit the invoice exchange rate and convert only at payment?

No, ERPNext needs a Company-currency value when the invoice posts. A later payment can use a different rate and recognize the difference.

### Can the invoice and Price List use different currencies?

Yes, Price List Exchange Rate converts item prices, while Exchange Rate converts the transaction to Company currency.

### Why does Payment Entry not have a free Currency selector?

Its currencies come from the paid-from and paid-to accounts. Select accounts that represent the actual balances.

### Can I show Company currency on the print format too?

Yes, with an appropriate print design, but keep the agreed transaction-currency amount clear and verify custom fields and labels.

### What happens when a foreign invoice remains unpaid at month end?

Its foreign amount remains outstanding. Revalue the eligible account to update its Company-currency carrying value according to your closing policy.

## Related topics

- [Multi Currency Accounting](/erpnext/multi-currency-accounting)
- [Sales Invoice](/erpnext/sales-invoice)
- [Purchase Invoice](/erpnext/purchase-invoice)
- [Payment Entry](/erpnext/payment-entry)
- [Exchange Rate Revaluation](/erpnext/exchange-rate-revaluation)
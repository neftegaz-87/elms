---
title: "Currency Exchange | ERPNext Documentation"
description: "Store dated buying and selling exchange rates in ERPNext and understand when a transaction uses them."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/currency-exchange"
updated: "2026-08-14"
---

When Nova Industries sells electronics in EUR but reports in USD, finance needs a controlled conversion rate.



Nova agrees to invoice a customer in EUR while maintaining its books in USD. Finance approves `1 EUR = 1.15 USD` for 3 August 2026, so users should not look up or retype the rate on every transaction. A Currency Exchange record stores the approved rate, its effective date, and the direction in which it applies.



ERPNext checks eligible stored records before asking the configured online provider. This gives finance control when a contract fixes the rate, historical entries need a known rate, or a provider does not cover the pair. Use this page to make transactions apply the correct dated rate consistently.

## Before you begin

Enable both currencies in the [Currency](/erpnext/currency) list. Confirm the intended direction and rate convention. `EUR to USD = 1.15` means one euro equals 1.15 US dollars. The inverse is not automatically the same number, so create `USD to EUR` separately when that direction is needed.

Review [Accounts Settings](/erpnext/accounts-settings), especially **Allow Stale Exchange Rates** and **Stale Days**. These settings decide how old a stored record may be when ERPNext searches for a rate. Also review the active [Currency Exchange Settings](/erpnext/currency-exchange-settings) provider, which is used when no eligible manual record is found.

## Create a Currency Exchange record

1. Open Accounting &gt; Multi Currency &gt; Currency Exchange.
2. Select **Add Currency Exchange**.
3. Enter the date from which the rate applies.
4. Select the From Currency and To Currency.
5. Enter the rate using the relationship shown in the field label.
6. Select **For Buying**, **For Selling**, or both.
7. Save.

The list can contain multiple dated records for the same pair. ERPNext searches by transaction date and chooses the latest eligible matching record.



![Dated Currency Exchange records](https://novacompanies.m.frappe.cloud/files/docs-multi-currency-2026-currency-exchange-list.png)



![EUR to USD exchange rate for buying and selling](https://novacompanies.m.frappe.cloud/files/docs-multi-currency-2026-currency-exchange-rate.png)

## Important fields and what they mean


| Field         | Meaning                                                                                                             |
| ------------- | ------------------------------------------------------------------------------------------------------------------- |
| Date          | The key date used when ERPNext searches for the latest eligible rate on or before a transaction date.               |
| From Currency | The currency representing one unit in the field's relationship.                                                     |
| To Currency   | The currency calculated from the From Currency.                                                                     |
| Exchange Rate | The number of To Currency units equal to one From Currency unit. Read the generated field label before entering it. |
| For Buying    | Makes the record eligible for buying transactions that request a buying rate.                                       |
| For Selling   | Makes the record eligible for selling transactions that request a selling rate.                                     |


If both boxes are selected, the same rate can be used for buying and selling. Use separate records when your approved buying and selling rates differ.

## How ERPNext chooses a rate

For a requested direction, date, and transaction type, current develop behavior follows this pattern:

1. Search Currency Exchange for the latest matching record on or before the transaction date.
2. Apply the stale-rate rule from Accounts Settings.
3. If no eligible stored record exists and the provider is enabled, request the rate from the configured service.
4. If ERPNext still cannot find a rate, ask the user to create a manual Currency Exchange record.

The direction and buying or selling flag matter. A record for EUR to USD does not necessarily satisfy a request for USD to EUR. A record marked only For Buying does not satisfy a selling-rate request.

## Understand stale rates

When **Allow Stale Exchange Rates** is enabled, ERPNext may use the latest matching stored record without an age limit. This is useful for contract rates or finance-approved rates that remain valid until replaced. It can also preserve an old rate longer than intended, so establish a review process.

When the option is disabled, **Stale Days** limits how far back ERPNext searches. If no eligible manual rate remains, ERPNext tries the configured provider. The setting does not create an approval workflow and does not guarantee that a transaction stops when a manual rate expires, because the provider may return a market rate.

See [Freeze Exchange Rate](/erpnext/exchange-rate-field-frozen) if a transaction's Exchange Rate field appears read-only or behaves differently from what the page title suggests.

## Use the rate in a transaction

On a draft [Sales Invoice](/erpnext/sales-invoice), [Purchase Invoice](/erpnext/purchase-invoice), [Quotation](/erpnext/quotation), or order, select the foreign currency and confirm the Exchange Rate. ERPNext calculates Company-currency totals using that rate. If the Price List uses a different currency, **Price List Exchange Rate** converts item prices separately.

The same check applies when a [Sales Order](/erpnext/sales-order) becomes the commercial source for a later invoice. A mapped document may carry forward currency and rate context, so verify the new document rather than assuming it refreshed to the latest master.

On a [Payment Entry](/erpnext/payment-entry), the currencies come from the paid-from and paid-to accounts. The source or target exchange rate converts between the account amounts and Company currency. A payment made at a different rate from its invoice can create a realized exchange gain or loss.

## Correct or supersede a rate

If a saved record is wrong and has not been relied on operationally, correct it with appropriate permission. If a new rate becomes valid later, create a new record with the later date rather than overwriting the historical record. Submitted transactions retain their own exchange-rate values; changing the master does not silently revalue old documents.

Use [Exchange Rate Revaluation](/erpnext/exchange-rate-revaluation) to update the Company-currency carrying value of eligible open foreign-currency accounts at a reporting date. Do not alter historical Currency Exchange records merely to force a current closing balance.

## Troubleshooting

### ERPNext says it cannot find an exchange rate

Check that both currencies are enabled, the direction matches, the date is on or before the transaction date, and the buying or selling flag matches. Then verify stale-rate settings and whether the provider supports the pair.

### ERPNext uses an older manual rate instead of the market rate

An eligible Currency Exchange record is preferred. Review **Allow Stale Exchange Rates**, the latest dated record, and its flags. Create a new dated record or change the stale-rate policy according to your finance process.

### The transaction shows two exchange-rate fields

**Exchange Rate** converts the transaction currency to Company currency. **Price List Exchange Rate** converts the Price List currency for item prices. They can be different when the transaction and Price List use different currencies.

## FAQs

### Must I create a Currency Exchange record every day?

No, if no eligible manual record exists, ERPNext can use the configured provider. Create manual records only when you need controlled, historical, unsupported, or contract rates.

### Does the latest record override submitted invoices?

No, a submitted invoice retains the rate saved on that document. The new master affects later rate lookups.

### Can I store different buying and selling rates?

Yes, create records with the appropriate flags and rates. Do not select both flags if finance uses different rates for purchases and sales.

### Why does the inverse direction use another rate?

The system searches the exact From and To direction. Store the inverse record when that direction is needed, using the approved reciprocal or independently supplied rate.

### Can I type over the fetched rate?

The field may be editable depending on document state, permissions, and stale-rate behavior. Always verify the saved value and Company-currency total before submission.

## Related topics

- [Currency](/erpnext/currency)
- [Multi Currency Setup](/erpnext/multi-currency-setup)
- [Currency Exchange Settings](/erpnext/currency-exchange-settings)
- [Manage Foreign Exchange Difference](/erpnext/manage-foreign-exchange-difference)
- [Exchange Rate Revaluation](/erpnext/exchange-rate-revaluation)
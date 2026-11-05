---
title: "Freeze Exchange Rate | ERPNext Documentation"
description: "Understand why an ERPNext exchange-rate field may be read-only and how stale-rate settings affect manual and fetched rates."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/exchange-rate-field-frozen"
updated: "2026-08-14"
---

A Nova Industries sales user may find that an exchange rate cannot be edited on a foreign-currency invoice.



A Nova sales user opens a foreign-currency invoice, sees an unexpected Exchange Rate, and cannot edit it. The field may appear frozen because the document is submitted, the selected accounts determine the currencies, the user lacks permission, or ERPNext has applied a stored-rate policy from Accounts Settings.



This guide helps you identify the actual cause on a Draft before changing configuration. A submitted invoice is intentionally locked and should not be repriced to solve a setup problem. When a manual override is approved, record its source so finance can explain the rate later.

## Before you begin

Confirm that the document is Draft and that at least two currencies are involved. A Company-currency transaction with Company-currency accounts needs no conversion rate. Check the user's write permission for the transaction and [Accounts Settings](/erpnext/accounts-settings).

Read the rate label carefully. `1 EUR = 1.15 USD` is a direction, not a generic ratio. Verify the [Currency Exchange](/erpnext/currency-exchange) record for that exact direction and date.

## Review Allow Stale Exchange Rates

Open Accounting &gt; Settings &gt; Accounts Settings and locate Currency Exchange Settings.



![Allow Stale Exchange Rates in Accounts Settings](https://novacompanies.m.frappe.cloud/files/docs-multi-currency-2026-accounts-settings-allow-stale-rate.png)

The current behavior is best understood as a rate-selection policy:


| Setting                             | Lookup behavior                                                                                                            |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Allow Stale Exchange Rates enabled  | The latest matching stored rate may be used without an age limit. This supports rates that remain valid until replaced.    |
| Allow Stale Exchange Rates disabled | ERPNext limits stored-rate age using Stale Days, then tries the configured provider when no eligible manual record exists. |


The existing documentation associates this setting with whether the Exchange Rate field is editable. Because field behavior has changed across releases and can vary by document, verify the Draft page after changing the setting instead of relying only on the word “stale.” In current develop, users can often override a fetched rate on a Draft when permissions and document logic allow it.

## If you need a controlled fixed rate

Create a dated Currency Exchange record with the approved value and the correct buying or selling flag. Then decide whether the record may remain valid until another is entered.



![Approved EUR to USD rate](https://novacompanies.m.frappe.cloud/files/docs-multi-currency-2026-currency-exchange-rate.png)

For a contract rate, enabling stale rates can be appropriate because the latest manual record remains eligible. For daily treasury rates, disable stale rates and use a small Stale Days value or import a new approved rate regularly.

This is not a true record-level “freeze” that prevents authorized users from changing the master. Control update permission and establish an approval process if rates must be protected.

For a stronger control, assign rate maintenance to a small finance role and have another person review the Draft transaction before submission. Keep the approved source and effective date with the treasury workpaper. This separates rate approval from transaction entry without misusing the stale-rate setting as a security control.

## If you need the current provider rate

Disable stale rates or ensure there is no eligible manual record that should win. Review [Currency Exchange Settings](/erpnext/currency-exchange-settings) and verify that the provider covers the pair and historical date.

ERPNext first searches an eligible stored record. The provider is a fallback, so changing provider settings does not override a matching manual record.

## If you need to enter the rate manually on a transaction

1. Keep the transaction in Draft.
2. Select the correct foreign Currency.
3. Confirm the receivable, payable, bank, or cash [Account](/erpnext/chart-of-accounts) currencies.
4. Review the Exchange Rate field and its direction.
5. Enter the approved rate if the field is editable.
6. Compare the transaction and Company-currency totals.
7. Save and reload the Draft to confirm the value persisted.

![Exchange Rate on a Draft EUR Sales Invoice](https://novacompanies.m.frappe.cloud/files/docs-multi-currency-2026-sales-invoice-eur-currency-rate.png)

The **Price List Exchange Rate** is a different field. It converts [Price List](/erpnext/price-lists) currency to transaction currency. Do not change it when the issue concerns the accounting conversion between transaction and Company currency.

## Submitted transactions

A submitted [Sales Invoice](/erpnext/sales-invoice), [Purchase Invoice](/erpnext/purchase-invoice), or [Payment Entry](/erpnext/payment-entry) represents an accounting event. ERPNext locks material fields to preserve the audit trail. If the rate is materially wrong, follow the document's cancel and amend process, subject to permissions, linked records, [Immutable Ledger](/erpnext/immutable-ledger-in-erpnext) rules, and the open [Accounting Period](/erpnext/accounting-period).

Do not update Currency Exchange and expect old submitted documents to change. They retain their own saved rates.

Before cancelling, inspect downstream payments, returns, credit notes, stock consequences, and reconciliations. A correct amendment should reproduce the commercial facts with the approved rate and preserve a readable audit trail. Ask finance to confirm whether the difference is truly an invoice error or a legitimate exchange movement that belongs at settlement.

## Common causes of a read-only field


| Cause                                 | What to check                                                              |
| ------------------------------------- | -------------------------------------------------------------------------- |
| Document is submitted                 | Cancel and amend only when accounting policy and links permit it.          |
| No currency conversion is needed      | Company, transaction, and relevant account currencies are the same.        |
| Account currency determines the flow  | The selected party or bank account fixes the amount currency.              |
| Stored rate policy controls selection | Review Allow Stale Exchange Rates, Stale Days, date, direction, and flags. |
| Provider supplied the value           | Verify the provider and whether Draft override is permitted.               |
| User lacks permission                 | Review role permissions rather than weakening accounting controls.         |
| Custom script or customization        | Test in a clean role and inspect client or server customization.           |


## Troubleshooting

### The field remains read-only after changing Accounts Settings

Reload the transaction, confirm it is Draft, and check account currencies, permissions, and customizations. Test a new Draft instead of a document whose state was already submitted or mapped from another transaction.

### ERPNext keeps using the old rate

Search Currency Exchange for the latest eligible record. Check Allow Stale Exchange Rates and Stale Days. A later transaction date does not force a provider call while an eligible manual record still wins.

### ERPNext cannot fetch a rate after stale rates are disabled

The provider may not support the pair or historical date. Create a manual record or select an approved provider that covers it.

### Changing the rate also changes item prices

Separate Exchange Rate from Price List Exchange Rate. If the Price List currency differs, item rates can be converted independently.

## FAQs

### Does Allow Stale Exchange Rates literally freeze a rate?

No, it allows the latest matching manual record to remain eligible without an age limit. Permissions and transaction logic determine editability.

### Can I lock a rate after finance approves it?

Restrict Currency Exchange write permission and use an approval or import process. The stale-rate option alone is not a master-record lock.

### Why can I edit a Draft but not a submitted invoice?

Submission posts accounting consequences and locks material fields for audit integrity.

### Will a new Currency Exchange record update old Drafts?

Not necessarily. Reload or retrigger the currency and date logic, then verify the saved field. Submitted documents remain unchanged.

### Should I disable the provider to force manual rates?

You can, but first ensure all required directions and dates have manual records and define what users should do when a rate is missing.

## Related topics

- [Currency Exchange](/erpnext/currency-exchange)
- [Currency Exchange Settings](/erpnext/currency-exchange-settings)
- [Accounts Settings](/erpnext/accounts-settings)
- [Managing Transactions in Multiple Currency](/erpnext/managing-transactions-in-multiple-currencies)
- [Manage Foreign Exchange Difference](/erpnext/manage-foreign-exchange-difference)
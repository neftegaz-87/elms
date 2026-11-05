---
title: "Currency Exchange Settings | ERPNext Documentation"
description: "Configure the exchange-rate provider ERPNext uses when no eligible manual Currency Exchange record is available."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/currency-exchange-settings"
updated: "2026-08-14"
---

International transactions at Nova Industries sometimes need a market rate when finance has not stored one manually.



A Nova sales user creates a EUR invoice, but finance has not entered a manual rate for that date. ERPNext can either stop the user or ask an online exchange-rate service for a rate. Currency Exchange Settings controls that fallback through the provider, endpoint, request parameters, credentials, and result mapping.



The setting is global, so one incorrect configuration can affect transactions and period-end revaluation across several Companies. Use it when market rates are acceptable, or disable it when finance requires only approved [Currency Exchange](/erpnext/currency-exchange) records. This page helps you configure and test the provider before users depend on it.

## Before you begin

List the required currency pairs, transaction dates, and rate types. Confirm whether the provider covers historical dates as well as current rates. Decide who owns provider credentials, rate-source approval, outage handling, and manual fallback.

Enable the required [Currency](/erpnext/currency) records. Review the stale-rate controls in [Accounts Settings](/erpnext/accounts-settings), because a valid manual record is preferred before the provider is called. If **Allow Stale Exchange Rates** is enabled, an old manual rate can continue to win indefinitely.

## Review the configured provider

1. Open Currency Exchange Settings.
2. Confirm that **Disabled** is clear when provider fallback is required.
3. Select the Service Provider.
4. Review the API Endpoint and protocol.
5. Enter an Access Key only for a provider that requires one.
6. Review request Parameters and Result Key mappings.
7. Save, then test from a draft foreign-currency transaction.

![Frankfurter v2 provider configuration](https://novacompanies.m.frappe.cloud/files/docs-multi-currency-2026-currency-exchange-provider-settings.png)

The current develop options include `frankfurter.dev`, `frankfurter.dev - v2`, `exchangerate.host`, and `Custom`. Frankfurter v2 supports more currencies than the older v1 configuration. Exchangerate.host requires an access key. Provider coverage and commercial terms can change, so validate them directly with the provider before rollout.

## Important fields and what they mean


| Field             | Meaning                                                                                                                       |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Disabled          | Stops provider requests. ERPNext can still use eligible stored Currency Exchange records.                                     |
| Service Provider  | Loads a predefined provider mapping or allows a Custom configuration.                                                         |
| API Endpoint      | URL template called by ERPNext. It can use placeholders such as `{transaction_date}`, `{from_currency}`, and `{to_currency}`. |
| Use HTTP Protocol | Uses HTTP instead of HTTPS. Leave this clear unless a trusted internal service specifically requires HTTP.                    |
| Access Key        | Credential required by some providers. Protect it like any external API secret.                                               |
| Parameters        | Key-value pairs sent with the request. Values can contain the supported placeholders.                                         |
| Result Key        | Path used to extract the numeric rate from the provider response.                                                             |
| Example URL       | A preview that helps validate the resulting request format.                                                                   |


Do not paste a secret into documentation, screenshots, support posts, or client scripts. Restrict write permission to this setting.

Use [Role Based Permissions](/erpnext/role-based-permissions) to limit who can alter the provider or its credentials. A rate source is an accounting control, not merely a technical preference. Record the owner, renewal date, approved providers, supported currency pairs, and manual fallback in the finance operating procedure.

## Provider choices

### Frankfurter v2

Use the v2 predefined configuration for a keyless, centrally sourced rate when its supported currencies and historical coverage match your need. The configured endpoint on the demo site requests a rate for the From Currency, To Currency, and transaction date.

### Frankfurter v1

The older endpoint covers fewer currencies. Keep it only when an existing integration has been tested against its supported list. New setups should evaluate v2 first.

### Exchangerate.host

This provider supports a broader commercial service but requires an access key in the current predefined setup. Review its free or paid plan, rate limits, historical coverage, licensing, and uptime before use.

### Custom

Use Custom for an approved treasury service or internal rate endpoint. Configure the URL, parameters, and result path carefully. The response must provide a numeric rate in the direction ERPNext requests.

## Understand lookup priority

When ERPNext requests a rate for a direction, date, and buying or selling context, it first searches stored Currency Exchange records. If none is eligible, the provider is called. If the provider fails or returns no usable value, ERPNext asks for a manual record.

This priority matters when users report that the system is not using the market rate. The cause may be an eligible stored record, not the provider. Review [Freeze Exchange Rate](/erpnext/exchange-rate-field-frozen) and stale-rate settings before changing the API configuration.

## Test the configuration

Create a Draft [Sales Invoice](/erpnext/sales-invoice) or [Purchase Invoice](/erpnext/purchase-invoice) dated on a known business day. Select a supported foreign currency and verify:

- the Exchange Rate populates;
- the direction in the field label is correct;
- the Company-currency total matches the rate;
- a historical date returns a plausible historical rate;
- a deliberately unsupported pair produces a clear fallback process;
- no API key or response detail is exposed to ordinary users.

Also test a [Payment Entry](/erpnext/payment-entry), because its source and target account currencies can request a different direction. Test [Exchange Rate Revaluation](/erpnext/exchange-rate-revaluation) separately for a closing date.

Repeat the test after application upgrades or provider configuration changes. Compare the returned value with an independently approved reference on a known date, and confirm that the same request is not unexpectedly using an older manual master.

## Disable provider fallback

Select **Disabled** when every rate must come from a manually approved master or another controlled process. Before doing so, create the required directional and dated records and test the behavior when a rate is missing. Disabling the provider does not create a warning-based approval workflow by itself.

If finance imports rates, use [Data Import](/erpnext/data-import) with a controlled template and validation process. Do not allow duplicate or incorrectly directed records to accumulate unnoticed.

## Troubleshooting

### ERPNext cannot find a rate for one currency

Confirm that the provider supports both currencies and the requested historical date. A provider can cover USD and EUR but not a regional currency. Try an approved alternative provider or create a manual record.

### The provider is configured but a different rate appears

Search Currency Exchange for a matching manual record. Check the transaction date, direction, buying or selling flag, Allow Stale Exchange Rates, and Stale Days.

### A custom provider returns data but ERPNext reads zero

Review the Result Key path and verify that the extracted value is numeric. Compare the request URL and response structure without exposing credentials.

### Historical rates fail while current rates work

The provider or plan may not support historical dates. Use a provider with suitable coverage or import approved historical Currency Exchange records.

## FAQs

### Does ERPNext always call the configured provider?

No, an eligible manual Currency Exchange record is preferred.

### Which provider should I choose?

Choose based on currency coverage, historical support, accuracy policy, licensing, rate limits, reliability, and security. There is no universal best provider.

### Are provider rates automatically posted to the ledger?

No, the fetched rate populates a document. The ledger changes only when a submittable accounting transaction or resulting Journal Entry is submitted.

### Can each Company use a different provider?

Currency Exchange Settings is a site-level singleton. Use controlled manual records or customization if Companies require separate approved sources.

### Should I enable HTTP for an external provider?

No, use HTTPS for external services. HTTP should be limited to a deliberately secured internal architecture.

## Related topics

- [Currency Exchange](/erpnext/currency-exchange)
- [Multi Currency Setup](/erpnext/multi-currency-setup)
- [Accounts Settings](/erpnext/accounts-settings)
- [Managing Transactions in Multiple Currency](/erpnext/managing-transactions-in-multiple-currencies)
- [Exchange Rate Revaluation](/erpnext/exchange-rate-revaluation)
---
title: "Control Item Rate Changes Through the Sales Cycle | ERPNext Documentation"
description: "Configure ERPNext to preserve, warn about, or stop item-rate changes between Sales Orders, Delivery Notes, and Sales Invoices."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/change-the-rate-of-items-in-the-sales-cycle"
updated: "2026-07-25"
---

ERPNext can validate whether an Item's rate changes as it moves from a [Sales Order](/erpnext/sales-order) to a [Delivery Note](/erpnext/delivery-note) or [Sales Invoice](/erpnext/sales-invoice). Use this control when confirmed order rates should remain consistent through fulfilment and billing.

## Before you begin

Confirm:

- Item Prices and the intended [Price List](/erpnext/price-lists).
- The roles permitted to approve price exceptions.
- Whether your process requires a warning or a hard stop.
- How legitimate amendments and returns should be handled.

This setting does not replace pricing governance. Document when a rate may change and who may approve it.

## Configure rate validation

1. Open [Selling Settings](/erpnext/selling-settings).
2. Open the Item Price Settings section.
3. Enable **Maintain Same Rate Throughout Sales Cycle**.
4. Set **Action If Same Rate Is Not Maintained** to:
  - **Warn** to allow saving after notifying the user.
  - **Stop** to block the inconsistent rate.
5. When Stop is selected, choose the role allowed to override the action if your version provides that field.
6. Save.

![Selling Settings with the same-rate controls highlighted.](https://novacompanies.m.frappe.cloud/files/sales-cycle-rate-settings.png)

## Test the control

1. Create and submit a Sales Order with an Item rate.
2. Create a Delivery Note or Sales Invoice from the Sales Order.
3. Select the highlighted pencil icon to open the complete Item row.
4. Change the Rate.
5. Save and confirm that ERPNext warns or stops the change according to Selling Settings.

![A mapped Sales Invoice item row with the Rate field highlighted.](https://novacompanies.m.frappe.cloud/files/sales-cycle-rate-change.png)

The dot before an Item Code shows stock availability at a glance: green means in stock and red means out of stock.

## When a rate legitimately changes

Use the workflow that preserves the audit trail:

- Amend the confirmed Sales Order when the commercial agreement changed before fulfilment.
- Use [Update Items](/erpnext/amending-sales-order-after-submit) when the supported after-submit workflow fits the change.
- Create a Credit Note or return when correcting a submitted invoice.
- Use an authorized override only when policy permits it.

Do not silently change a downstream rate simply to make totals match.

## How pricing sources interact

A transaction rate can be influenced by:

- Item Price and Price List.
- [Pricing Rules](/erpnext/pricing-rule).
- [Promotional Schemes](/erpnext/promotional-scheme).
- Item-level margin or discount.
- Additional Discount.
- Currency conversion.
- A manually entered Rate when permissions allow it.

The same-rate validation compares the mapped sales-cycle rate. It does not prevent every possible upstream pricing configuration.

## Important settings


| Setting                                   | Effect                                                                             |
| ----------------------------------------- | ---------------------------------------------------------------------------------- |
| Maintain Same Rate Throughout Sales Cycle | Enables comparison against the upstream rate                                       |
| Action: Warn                              | Shows a warning but permits the user to continue                                   |
| Action: Stop                              | Blocks the rate change                                                             |
| Override Role                             | Lets authorized users bypass Stop when supported                                   |
| Allow User to Edit Price List Rate        | Controls editing of the Price List Rate field, not the complete sales-cycle policy |


## Troubleshooting


| Problem                                | What to check                                                                            |
| -------------------------------------- | ---------------------------------------------------------------------------------------- |
| No warning appears                     | Confirm the downstream document was mapped from the Sales Order and the setting is saved |
| Authorized user cannot override        | Confirm the configured role and the user's assigned roles                                |
| Rate changes before mapping            | Review Item Prices, Pricing Rules, discounts, currency, and the source document          |
| Return or credit correction is blocked | Use the appropriate return or amendment workflow                                         |
| Users confuse Rate and Price List Rate | Explain the reference rate, margin, discount, and final transaction rate                 |


## Frequently asked questions

### Does the setting apply to unrelated standalone invoices?

It is intended to validate rates through a linked sales cycle. A standalone invoice has no Sales Order rate to compare.

### Should I choose Warn or Stop?

Use Warn where exceptions are common and reviewed later. Use Stop where approval must happen before the document is saved.

### Can a role override Stop?

Yes, when the override-role field is available and configured in your ERPNext version.

### Does the setting stop Pricing Rules?

No. Pricing Rules remain part of rate calculation. Test the combined workflow.

## Related topics

- [Selling Settings](/erpnext/selling-settings)
- [Sales Order](/erpnext/sales-order)
- [Amending Sales Order after Submit](/erpnext/amending-sales-order-after-submit)
- [Pricing Rule](/erpnext/pricing-rule)
- [Applying a Discount](/erpnext/applying-discount)
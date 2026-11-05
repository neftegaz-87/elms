---
title: "Add Margin to Quotations and Sales Orders | ERPNext Documentation"
description: "Add percentage or fixed margins to ERPNext quotation and sales order items manually or through Pricing Rules, with calculation examples."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/adding-margin"
updated: "2026-07-25"
---

Margin increases an item's transaction Rate above its Price List Rate. ERPNext can apply a percentage or fixed amount directly on a [Quotation](/erpnext/quotation) or [Sales Order](/erpnext/sales-order) item, or apply it automatically through a [Pricing Rule](/erpnext/pricing-rule).

## Before you begin

Create:

- The required [Item](/erpnext/item).
- A selling [Price List](/erpnext/price-lists).
- An [Item Price](/erpnext/item-price) that supplies the Price List Rate.

Margin needs a reference Price List Rate. If no rate is fetched, verify the Item Price before troubleshooting the margin calculation.

## Add margin directly to an item

1. Create a Quotation or Sales Order.
2. Select the Customer, Price List, and Item.
3. Select the highlighted pencil icon to open the complete item-row editor.
4. Set **Margin Type** to **Percentage** or **Amount**.
5. Enter **Margin Rate or Amount**.
6. Review the calculated Rate and Amount.
7. Save.

![A Sales Order item row with its pencil icon highlighted.](https://novacompanies.m.frappe.cloud/files/discount-item-pencil.png)

![The item row editor with Margin Type and Margin Rate or Amount highlighted.](https://novacompanies.m.frappe.cloud/files/margin-item-fields-v2.png)

## Margin calculation

For a fixed margin:

`Rate = Price List Rate + Margin Amount`

For a percentage margin:

`Rate = Price List Rate + (Price List Rate × Margin Percentage ÷ 100)`

Example:


| Value           | Amount |
| --------------- | ------ |
| Price List Rate | $1,000 |
| Margin          | 15%    |
| Margin amount   | $150   |
| Resulting Rate  | $1,150 |


Any item discount is evaluated separately. Review Price List Rate, Margin, Discount, Rate, and Net Rate together when both are used.

## Apply margin automatically with a Pricing Rule

Use a Pricing Rule when the same margin should apply under repeatable conditions.

1. Create or open a Pricing Rule.
2. Configure its applicability, such as Item, Item Group, Customer, Customer Group, quantity, amount, and validity.
3. In the **Margin** section, select Percentage or Amount.
4. Enter the Margin Rate or Amount.
5. Save and enable the rule.
6. Test it on a new Quotation or Sales Order.

![A Pricing Rule with its Margin settings highlighted.](https://novacompanies.m.frappe.cloud/files/margin-pricing-rule.png)

When several rules can match, review their priorities and conditions. A more specific rule may need a higher priority than a general Item Group rule.

## Margin and discounts

Margin and discount solve different pricing needs:

- Margin adds a markup to the Price List Rate.
- [Applying a Discount](/erpnext/applying-discount) reduces a price or total.
- A fixed Pricing Rule Rate can replace the fetched rate.

Avoid combining them without a documented pricing policy. Users should be able to explain how the final Rate was reached.

## Downstream transactions

When a Sales Order is created from a Quotation, or a [Sales Invoice](/erpnext/sales-invoice) is created later in the cycle, verify the mapped Rate. [Selling Settings](/erpnext/selling-settings) can warn or stop users when the rate changes through the sales cycle.

## Troubleshooting


| Problem                             | What to check                                                                  |
| ----------------------------------- | ------------------------------------------------------------------------------ |
| Margin fields do not affect Rate    | Confirm that a Price List Rate was fetched                                     |
| Margin is not applied automatically | Verify the Pricing Rule is enabled, valid, and matches the transaction         |
| A different rule wins               | Review rule priority, Item or party specificity, and overlapping conditions    |
| The downstream rate changes         | Review mapped values and the Maintain Same Rate setting                        |
| Final profitability is unclear      | Margin is based on Price List Rate, not necessarily valuation or purchase cost |


## Frequently asked questions

### Is margin calculated from valuation rate?

No. The item margin fields use Price List Rate as their pricing reference.

### Can I add a fixed dollar margin?

Yes. Select Amount as the Margin Type.

### Can margin apply to Sales Invoices?

Margin fields are primarily entered on Quotation and Sales Order items. Downstream documents can carry the resulting rate.

### How do I enforce a minimum selling price?

Review the selling-price validation in Selling Settings and test it against your purchase or valuation rates.

## Related topics

- [Price Lists](/erpnext/price-lists)
- [Item Price](/erpnext/item-price)
- [Pricing Rule](/erpnext/pricing-rule)
- [Applying a Discount](/erpnext/applying-discount)
- [Change the Rate of Items in the Sales Cycle](/erpnext/change-the-rate-of-items-in-the-sales-cycle)
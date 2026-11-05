---
title: "Selling Settings | ERPNext Documentation"
description: "Configure ERPNext Selling Settings for customer defaults, pricing, transaction rules, commissions, subcontracting, and document naming."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/selling-settings"
updated: "2026-08-25"
---

Selling Settings controls the defaults and validations used across the ERPNext sales cycle. These settings affect customers, pricing, quotations, sales orders, delivery notes, sales invoices, returns, commissions, and document naming.

Review the settings with your sales, fulfilment, and finance teams before enabling them. A validation that improves control for one business can interrupt a different sales process.

## Before you begin

- You need permission to edit Selling Settings.
- Create the required [Customer Groups](/erpnext/customer-group), [Territories](/erpnext/territory), and [Price Lists](/erpnext/price-list) first.
- Test changes with representative transactions before applying them to production users.

To open the page, go to **Selling &gt; Settings &gt; Selling Settings**. Settings are organized into six tabs. Select **Save** after making changes.

## Customer Defaults

Customer defaults reduce data entry when creating a [Customer](/erpnext/customer) or converting a Lead or Quotation into a Customer.



![Customer Defaults tab in ERPNext Selling Settings](https://novacompanies.m.frappe.cloud/files/customer-defaults-1440.png)


| Field                  | What it means                                                                                                                                                         |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Customer Naming By     | Choose Customer Name, Naming Series, or Auto Name for the customer ID. Customer Name is the default. Naming Series produces IDs such as CUST-00001.                   |
| Default Customer Group | Sets the Customer Group on new customers when another value is not provided. It is also used when ERPNext creates a Customer while converting a Lead-based Quotation. |
| Default Territory      | Sets the Territory on new customers and supports automatic Customer creation from a Lead-based Quotation.                                                             |


If Default Customer Group or Default Territory is blank, automatic conversion can stop and ask for the missing value.

## Pricing

The Pricing tab determines how ERPNext fetches and validates item rates throughout the sales cycle.



![Pricing tab in ERPNext Selling Settings](https://novacompanies.m.frappe.cloud/files/pricing-1440.png)


| Field                                                     | What it means                                                                                                                                                                                                                                                                   |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Default Price List                                        | Provides the default selling Price List for a [Quotation](/erpnext/quotation), [Sales Order](/erpnext/sales-order), Delivery Note, and Sales Invoice.                                                                                                                           |
| Use prices from Default Price List as fallback            | Fetches an Item Price from the default Price List when the transaction’s selected Price List has no matching Item Price. Do not combine it with automatic insertion of missing Item Prices in Stock Settings, because a fallback rate could be written into another Price List. |
| Allow editing Price List rate in transactions             | Makes Price List Rate editable in sales item tables. Keep it disabled when rates must always come from [Item Price](/erpnext/item-price) records.                                                                                                                               |
| Maintain same rate throughout sales cycle                 | Checks whether an item rate changes in a Delivery Note or Sales Invoice created from a Sales Order.                                                                                                                                                                             |
| Action if same rate is not maintained                     | Appears after maintaining the same rate is enabled. Warn allows the transaction after showing a message. Stop prevents the change.                                                                                                                                              |
| Role allowed to override Stop action                      | Appears when the action is Stop. Users with the selected role can override the validation.                                                                                                                                                                                      |
| Validate selling price against purchase or valuation rate | Blocks a sale when the selling rate is below the relevant purchase or valuation rate. Test this carefully for promotions and clearance items.                                                                                                                                   |
| Calculate Product Bundle price based on child Item rates  | Makes packed-item rates editable and calculates the [Product Bundle](/erpnext/product-bundle) price from its child items. A manually changed bundle rate is recalculated when the document is saved.                                                                            |
| Allow negative rates for Items                            | Permits negative item rates for supported adjustments, refunds, returns, or special pricing. Use this only with appropriate accounting review.                                                                                                                                  |


## Transaction

Transaction settings define which documents are required and which exceptions users may use.



![Transaction tab in ERPNext Selling Settings](https://novacompanies.m.frappe.cloud/files/transaction-1440.png)


| Field                                                             | What it means                                                                                                                                                                                                       |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Is Sales Order required to create Sales Invoice or Delivery Note? | Set to Yes to require a Sales Order before a [Sales Invoice](/erpnext/sales-invoice) or [Delivery Note](/erpnext/delivery-note). A Customer can allow Sales Invoice creation without a Sales Order as an exception. |
| Is Delivery Note required to create Sales Invoice?                | Set to Yes to require a Delivery Note before invoicing. A Customer can allow invoicing without a Delivery Note as an exception.                                                                                     |
| How often should sales data be updated in Company or Project?     | Choose Each Transaction, Daily, or Monthly. Daily or Monthly can reduce repeated updates on sites with a high transaction volume.                                                                                   |
| Allow same Item to be added multiple times                        | Allows the same item on more than one row of a transaction. Disable it when duplicate lines are usually an error.                                                                                                   |
| Allow multiple Sales Orders against a customer’s Purchase Order   | Allows several Sales Orders to use the same customer purchase order number and date.                                                                                                                                |
| Hide Customer’s Tax ID from sales transactions                    | Stops the Customer Tax ID from appearing in selling transactions when your process does not require it.                                                                                                             |
| Allow Sales Order creation for expired Quotation                  | Allows an expired Quotation to be converted. Users should still confirm that the rate and terms remain valid.                                                                                                       |
| Don’t reserve Sales Order qty on sales return                     | Prevents a return from automatically reserving quantity against the linked Sales Order.                                                                                                                             |
| Enable cut-off date on creating bulk Delivery Notes               | Adds a cut-off date to bulk Delivery Note creation so only eligible Sales Orders up to that date are processed.                                                                                                     |
| Set incoming rate as zero for expired Batch                       | Sets the incoming rate to zero for a stand-alone credit note containing an item from an expired Batch.                                                                                                              |
| Allow Quotation with zero quantity                                | Allows zero-quantity lines when the rate is agreed before the quantity, such as a rate contract.                                                                                                                    |
| Allow Sales Order with zero quantity                              | Allows zero-quantity Sales Order lines for a similar rate-contract workflow.                                                                                                                                        |
| Blanket Order Allowance (%)                                       | Controls how much a Sales Order may exceed the quantity agreed in a [Blanket Order](/erpnext/blanket-order).                                                                                                        |


## **Skip Delivery Note Creation for Service Items**

![](/files/Screenshot 2026-08-25 at 5.20.08 PM.webp)

Sales Orders that contain services no longer wait for a delivery that will never happen. When this setting is on, non-stock items are excluded from delivery tracking, and an order made up entirely of them completes as soon as it is fully billed.

### The problem it solves

A Sales Order for services — consulting, installation, an AMC — has nothing to deliver. Without this feature the order still expects a Delivery Note, so after billing it sits at **To Deliver** and eventually shows as **Overdue**, even though the work is done and paid for.

### Enabling it

> **Selling Settings → Skip Delivery Note for Service Items**

The switch applies to all order types — Sales, Maintenance, and Shopping Cart alike. No per-order checkbox is needed; each order works it out from its items.

### How items qualify

Every time a Sales Order is saved, each item row is marked with a hidden `Skip Delivery` flag. A row is exempt from delivery only when **all** of these hold:

- the item is not a stock item
- the item is not a fixed asset
- the item is not a Product Bundle that contains stock items
- the row is not delivered by the supplier (drop shipping)

Anything failing a check keeps normal delivery tracking. The flags refresh on every save — including **Update Items** on a submitted order — so changing the item mix or the setting is always reflected.

### Order status

When every row on the order is exempt, the order needs no delivery at all: **% Delivered** is set to 100 and the delivery status shows **Not Applicable**.

```
To Bill  →  (Sales Invoice for the full amount)  →  Completed
```

On a mixed order, only the deliverable rows count toward **% Delivered**, and the Delivery Note picks up only those rows. The order completes once the stock items are delivered and everything is billed.

### Examples


| Order contents         | Delivery Note   | Completed when                        |
| ---------------------- | --------------- | ------------------------------------- |
| Services only          | Not required    | Fully billed                          |
| Stock items + services | Stock rows only | Stock rows delivered and fully billed |
| Setting disabled       | All rows        | Fully delivered and fully billed      |


## Advanced Features

Use these settings when your implementation requires commission tracking, separate discount accounting, or campaign attribution.



![Advanced Features tab in ERPNext Selling Settings](https://novacompanies.m.frappe.cloud/files/advanced-features-1440.png)


| Field                                  | What it means                                                                                                                             |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Enable tracking sales commissions      | Enables commission management for Sales Partners and the sales team.                                                                      |
| Enable discount accounting for selling | Creates additional ledger entries to post discounts to a separate Discount Account.                                                       |
| Enable UTM                             | Adds UTM attribution fields to supported documents including Lead, Quotation, Sales Order, Delivery Note, Sales Invoice, and POS Invoice. |
| Use Legacy (Client side) Reactivity    | An experimental compatibility option. Keep the default unless a tested customization requires the legacy behavior.                        |


## Subcontracting Inward

These controls apply when your company receives materials from a customer, processes them, and delivers finished goods back to that customer.



![Subcontracting Inward tab in ERPNext Selling Settings](https://novacompanies.m.frappe.cloud/files/subcontracting-inward-1440.png)


| Field                                   | What it means                                                                                                      |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Allow delivery of overproduced quantity | Allows the entire produced quantity to be delivered even when it exceeds the Subcontracting Inward Order quantity. |
| Deliver secondary Items                 | Adds secondary items generated with a finished good to the Stock Entry used for delivery.                          |


## Document Naming

This tab shows the current naming series for Quotation, Sales Order, Sales Invoice, and Delivery Note, including separate return series where applicable.



![Document Naming tab in ERPNext Selling Settings](https://novacompanies.m.frappe.cloud/files/document-naming-1440.png)

Configure or extend naming series according to your company’s document-control policy. Avoid changing an active series without checking reporting, integrations, and print formats.

## Frequently asked questions

### Can I require a Sales Order for most customers but allow exceptions?

Y

es. Set the global requirement in Selling Settings, then use the relevant exception on the Customer record for approved cases.

### Why are some pricing fields not visible?

Action and override-role fields appear only after Maintain same rate throughout sales cycle is enabled. The override role is relevant when the selected action is Stop.

### Should I allow users to edit Price List Rate?

Enable it only when users are authorized to depart from maintained Item Prices. Otherwise, keep the field controlled and use Pricing Rules for repeatable exceptions.

### When should zero-quantity transactions be allowed?

Use them for rate contracts or agreements where the unit rate is confirmed before the final quantity. They should not replace quantities in normal orders.

### What should I test after changing Selling Settings?

Create a test Customer, Quotation, Sales Order, Delivery Note, Sales Invoice, and return that reflect your normal and exception workflows. Confirm rates, document links, accounting entries, and permissions before production use.
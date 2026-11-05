---
title: "Buying Settings"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/buying-settings"
updated: "2026-10-16"
---

Keystone Cables agreed to sell Nova Electronics Trading (NET) 200 USB-C adapters at $18.00 each, and NET's Purchase Order PUR-ORD-2026-00022 says so: $3,600.00 before tax. A week later the supplier's invoice arrives at $19.00 per adapter, $200.00 more than agreed. Should the accounts clerk be able to book it as it stands?



If ERPNext quietly accepts the new rate, NET pays the extra $200.00 and nobody notices until margins slip. If it blocks every change, a genuine price correction needs someone senior to step in each time. NET's finance controller wants the first case to stop and the second to have a named owner.



Buying Settings is where that kind of company-wide purchasing rule lives. With **Maintain same rate throughout the purchase cycle** set to **Stop**, the invoice created from NET's order keeps the $18.00 rate, and saving it at $19.00 is refused. The same form also decides how suppliers are named, which price list buyers start from, which documents must come first, and how subcontracting and Requests for Quotation behave. The settings apply to every company on the site.

## Open Buying Settings

Search for **Buying Settings** in the awesome bar, or open it from the Buying workspace. The settings are grouped into the tabs **Defaults**, **Pricing**, **Transaction Settings**, **Subcontracting Settings**, **Request for Quotation** and **Document Naming**. Change a value and click **Save**; it applies to documents created afterwards.

## Defaults

![Buying Settings Defaults tab with Supplier Naming By highlighted](https://novacompanies.m.frappe.cloud/files/buying-setup-20261007-buying-settings-defaults.png)

**Supplier Naming By** decides the name ERPNext gives a new [Supplier](/erpnext/supplier), which is how the supplier is referred to on every document.

| Option | Result |
| --- | --- |
| **Supplier Name** | The supplier's name becomes its ID, for example Keystone Cables. This is the default and the setting at NET. |
| **Naming Series** | The supplier gets the next number in a series such as SUP-2026-00001, chosen on the supplier form. See [Naming Series](/erpnext/naming-series). |
| **Auto Name** | Uses the Supplier document's own naming rule, which in a standard setup is the same naming series. |

**Default Supplier Group** pre-fills the [Supplier Group](/erpnext/supplier-group) on new suppliers. NET leaves it empty so that the person creating a supplier chooses the category, and with it the category's payment terms.

## Pricing

![Buying Settings Pricing tab with Maintain same rate throughout the purchase cycle, the Stop action and the override role highlighted](https://novacompanies.m.frappe.cloud/files/buying-setup-20261007-buying-settings-pricing.png)

**Default Buying Price List** is the price list new buying documents start with when the supplier has none of its own. At NET it is Standard Buying; Keystone Cables overrides it with its own [Price List](/erpnext/price-lists), Nova Purchase USD.



**Maintain same rate throughout the purchase cycle** compares each item's rate on a Purchase Receipt or [Purchase Invoice](/erpnext/purchase-invoice) with the rate on the document it was created from. A Purchase Receipt is checked against its Purchase Order, and a Purchase Invoice against both the order and the receipt. When it is enabled, two more fields appear:

| Field | What it does |
| --- | --- |
| **Action if same rate is not maintained** | **Stop** refuses to save the document. **Warn** saves it and shows a warning. |
| **Role allowed to override stop action** | Users with this role can save a changed rate even when the action is Stop. Leave it empty to stop everyone. |

Returns (debit notes) and purchases from internal suppliers are not checked, because a return may legitimately carry a different rate.

### See it in a Purchase Invoice

NET's clerk opened PUR-ORD-2026-00022 and chose **Create > Purchase Invoice**. The new invoice, ACC-PINV-2026-00023, carried over the 200 adapters at $18.00 with Keystone Cables' invoice number KC-INV-1187.

![Purchase Invoice created from PUR-ORD-2026-00022 with the $18.00 rate highlighted](https://novacompanies.m.frappe.cloud/files/buying-setup-20261007-purchase-invoice-from-order-rate.png)

Changing the rate to $19.00 and saving stops with the message **Row #1: Rate must be same as Purchase Order: PUR-ORD-2026-00022 (19.0 / 18.0)**: the new rate first, then the order's rate. The draft keeps $18.00. To accept a real price change, a user with the override role saves the invoice, or the buyer amends the order first so the rates match again.



**Set Landed Cost Based on Purchase Invoice Rate** is shown only while Maintain same rate is disabled, and enabling Maintain same rate turns it off. It lets the invoice rate correct the value of stock already received. Suppose a Purchase Receipt valued an item at $100 and the invoice later comes in at $150 because the exchange rate moved. With this option on, submitting the invoice updates the receipt's incoming rate to $150 and reposts the stock and accounting entries that depend on it through a [Repost Item Valuation](/erpnext/repost-item-valuation). The new value appears once the repost completes. To add freight or duty to stock instead, use a [Landed Cost Voucher](/erpnext/landed-cost-voucher).

## Transaction Settings

![Buying Settings Transaction Settings tab with the Purchase Order and Purchase Receipt requirements highlighted](https://novacompanies.m.frappe.cloud/files/buying-setup-20261007-buying-settings-transaction.png)

| Field | What it does |
| --- | --- |
| **Is Purchase Order required for Purchase Invoice & Receipt creation?** | **Yes** stops a Purchase Receipt or Purchase Invoice that was not created from a [Purchase Order](/erpnext/purchase-order). Returns are not affected. For invoices only, a supplier can be exempted with **Allow purchase invoice creation without purchase order** on its Settings tab. NET leaves it at No so that samples can be received directly. |
| **Is Purchase Receipt required for Purchase Invoice creation?** | **Yes** stops a Purchase Invoice that was not created from a Purchase Receipt. A supplier can be exempted with **Allow purchase invoice creation without purchase receipt**. |
| **How often should project be updated of Total Purchase Cost?** | **Each Transaction** updates a project's purchase cost on every linked purchase; **Manual** waits until you update it. |
| **Over Order Allowance (%)** | How much more a Purchase Order may order than its [Material Request](/erpnext/material-request) asked for. With 10%, a request for 100 units allows an order of 110. |
| **Allow Item to be added multiple times in a transaction** | When unchecked, an item can appear on only one row of a document, which prevents accidental double orders. Keep it checked if the same material is bought on several lines. |
| **Allow negative rates for Items** | Allows a negative rate on buying documents. |
| **Disable last purchase rate** | Stops ERPNext from filling in the rate from the item's last purchase on new documents. |

The **Purchase Invoice Settings** section controls invoices made from receipts and orders.

| Field | What it does |
| --- | --- |
| **Bill for rejected quantity in Purchase Invoice** | Includes the rejected quantity of a Purchase Receipt when the invoice is created from it. |
| **Set valuation rate for rejected Materials** | Shown when the option above is on. Values rejected material and books accounting entries for it; by default rejected material has no value and no ledger entry. |
| **Use Transaction Date Exchange Rate** | For an invoice made from a Purchase Order in a foreign currency, uses the exchange rate of the invoice date instead of the order's rate. |

![Zero-Quantity Line Items and Blanket Orders sections of Buying Settings](https://novacompanies.m.frappe.cloud/files/buying-setup-20261007-buying-settings-zero-qty-blanket.png)

**Zero-Quantity Line Items** allow a Supplier Quotation, a Request for Quotation or a Purchase Order to be submitted with a quantity of zero. This suits rate contracts, where the price is agreed now and quantities are called off later. **Blanket Order Allowance (%)** is how far orders may exceed a [Blanket Order](/erpnext/blanket-order): with 10%, a blanket order for 100 units allows 110.

## Subcontracting Settings

![Buying Settings Subcontracting Settings tab](https://novacompanies.m.frappe.cloud/files/buying-setup-20261007-buying-settings-subcontracting.png)

These settings govern [Subcontracting](/erpnext/subcontracting), where a supplier converts your raw materials into a finished item.

| Field | What it does |
| --- | --- |
| **Backflush raw materials of subcontract based on** | **BOM** consumes raw materials on the Subcontracting Receipt as per the finished item's BOM. **Material Transferred for Subcontract** consumes what was actually transferred against the Subcontracting Order, and nothing if no material was transferred. |
| **Over Transfer Allowance (%)** | Shown for BOM. How much more raw material may be transferred than ordered. |
| **Validate consumed quantity (as per BOM)** | Shown for Material Transferred for Subcontract. Checks the consumed quantity against the BOM. |
| **Auto create Subcontracting Order** | Creates a draft Subcontracting Order when a subcontracted Purchase Order is submitted. |
| **Auto create Purchase Receipt** | Creates a draft Purchase Receipt for the service items when a Subcontracting Receipt is submitted. |

## Request for Quotation

![Buying Settings Request for Quotation tab with Fixed Outgoing Email Account highlighted](https://novacompanies.m.frappe.cloud/files/buying-setup-20261007-buying-settings-rfq.png)

**Fixed Outgoing Email Account** sends every [Request for Quotation](/erpnext/request-for-quotation) from one [Email Account](/erpnext/email-account), such as a shared purchasing mailbox, instead of the sender's own or the default outgoing account.

## Document Naming

![Buying Settings Document Naming tab listing the naming series of buying documents](https://novacompanies.m.frappe.cloud/files/buying-setup-20261007-buying-settings-document-naming.png)

This tab lists the current naming series of each buying document, such as Material Request, Request for Quotation, Purchase Order, Purchase Receipt and Purchase Invoice. Use the edit icon on a row to change its series.

## Troubleshooting

### An invoice will not save because the rate differs from the order

The message names the row, the source document, the new rate and the original rate. If the original rate is right, change the row back. If the price really changed, ask a user with the override role to save it, or switch the action to Warn. An order raised with a rate of zero triggers the same check, so enter the agreed rate on the order before invoicing.

### A Purchase Receipt cannot be created without a Purchase Order

**Is Purchase Order required for Purchase Invoice & Receipt creation?** is set to Yes, and the message names the item without an order. Create the receipt from a Purchase Order. The supplier-level exemption covers Purchase Invoices only, so a receipt always needs an order while the setting is Yes.

### A debit note was saved with a different rate

Returns are not checked by Maintain same rate, so a debit note can carry any rate. Review the rate on the return before submitting it.

## Frequently asked questions

### Do these settings apply to every company?

Buying Settings is a single record for the whole site, so every company follows the same rules. Supplier-level exemptions and per-supplier defaults are the way to vary them.

### Does Buying Settings affect Sales Orders and Sales Invoices?

Selling has its own rules in [Selling Settings](/erpnext/selling-settings), including a separate same-rate check for the sales cycle.

## Related topics

- [Supplier](/erpnext/supplier)
- [Supplier Group](/erpnext/supplier-group)
- [Purchase Order](/erpnext/purchase-order)
- [Purchase Receipt](/erpnext/purchase-receipt)
- [Purchase Invoice](/erpnext/purchase-invoice)
- [Price Lists](/erpnext/price-lists)
- [Subcontracting](/erpnext/subcontracting)

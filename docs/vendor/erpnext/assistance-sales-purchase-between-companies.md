---
title: "Create a Sales Invoice without an Item Code | ERPNext Documentation"
description: "Create ERPNext Sales Invoices and Credit Notes for one-time charges without an Item Code by completing the required child-row fields."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/assistance-sales-purchase-between-companies"
updated: "2026-07-25"
---

Use inter-company drop shipping when one Company sells to a Customer while goods are supplied directly by another Company in the same ERPNext site. This combines the [Drop Ship](/erpnext/drop-shipping-in-erpnext) workflow with inter-company Customer and Supplier relationships.

## Before you begin

Create or confirm:

- Both [Companies](/erpnext/company) in the same site.
- An internal Customer representing the supplying Company.
- An internal Supplier representing the selling Company.
- **Represents Company** and internal-party settings on both masters.
- Items, Warehouses, Price Lists, taxes, and inter-company accounts.
- Permissions for both Companies.

Review [Inter Company Invoices](/erpnext/inter-company-invoices) before using the workflow. Each Company remains a separate accounting entity.

## Configure internal parties

1. Create a Customer for the Company that buys internally.
2. Enable **Is Internal Customer** and select **Represents Company**.
3. Create the reciprocal Supplier.
4. Enable **Is Internal Supplier** and select the represented Company.
5. Save both records.

![](/files/subsidiary-drop-ship-internal-customer-v3.webp)

## Create the customer Sales Order

1. In the selling Company, create a [Sales Order](/erpnext/sales-order) for the external Customer.
2. Add the Items.
3. Select the highlighted pencil icon to open the Item row.
4. Enable **Drop Ship** for the row.
5. Select the Supplier that represents the supplying subsidiary.
6. Save and submit.

![A Sales Order Item with Supplier delivers to Customer and the subsidiary Supplier highlighted.](https://novacompanies.m.frappe.cloud/files/subsidiary-drop-ship-sales-order-v2.png)

In a drop-ship flow, stock availability in the selling Company's Warehouse does not replace Supplier fulfilment planning.

## Create the Purchase Order

From the submitted Sales Order:

1. Select **Create > Purchase Order**.
2. Choose the internal Supplier.
3. Review the mapped external Customer delivery address and Items.
4. Confirm the buying Company, schedule dates, rates, taxes, and terms.
5. Save and submit.

![A Purchase Order created for an internal Supplier with the Customer delivery address.](https://novacompanies.m.frappe.cloud/files/subsidiary-drop-ship-purchase-order.png)

The Purchase Order instructs the supplying subsidiary to deliver directly to the external Customer.

## Complete the inter-company documents

Create the corresponding internal sales and purchase invoices according to your [inter-company transaction](/erpnext/inter-company-invoices) process. Then invoice the external Customer from the selling Company.

Keep these relationships clear:


| Relationship                               | Document                  |
| ------------------------------------------ | ------------------------- |
| External Customer owes selling Company     | External Sales Invoice    |
| Selling Company owes supplying subsidiary  | Internal Purchase Invoice |
| Supplying subsidiary bills selling Company | Internal Sales Invoice    |


Tax and transfer-pricing requirements vary by jurisdiction. Configure them with qualified accounting advice.

## Troubleshooting


| Problem                                | What to check                                                                                 |
| -------------------------------------- | --------------------------------------------------------------------------------------------- |
| Internal Supplier cannot be selected   | Confirm Is Internal Supplier, Represents Company, permissions, and disabled status            |
| Purchase Order uses the wrong Company  | Review the internal party relationship and mapped Company                                     |
| Customer address is missing            | Confirm the Sales Order shipping address and drop-ship row                                    |
| Inter-company invoice is not generated | Review reciprocal Customer and Supplier masters and inter-company settings                    |
| Stock is moved in the selling Company  | Confirm that the Item row uses Drop Ship and that no Delivery Note was created for that stock |


## Frequently asked questions

### Does the selling Company receive the goods?

No. In the intended drop-ship flow, the Supplier delivers directly to the external Customer.

### Are inter-company invoices still required?

Yes. The Companies remain separate accounting entities even though they share an ERPNext site.

### Can only selected lines be drop shipped?

Yes. Configure Drop Ship at the Item-row level and plan the remaining lines through the normal warehouse flow.

### Does ERPNext determine legal transfer prices?

No. Configure internal rates and taxes according to your organization's policy and applicable law.

## Related topics

- [Drop Ship](/erpnext/drop-shipping-in-erpnext)
- [Inter Company Invoices](/erpnext/inter-company-invoices)
- [Sales Order](/erpnext/sales-order)
- [Purchase Order](/erpnext/purchase-order)
- [Company](/erpnext/company)
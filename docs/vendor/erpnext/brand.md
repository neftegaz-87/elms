---
title: "Brand\n"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/brand"
updated: "2026-03-06"
---

**A Brand identifies items with a specific name.**

Usually, a Brand is the manufacturer or packer of a specific product. For example, Apple is a brand that manufactures laptops. A Brand is not necessarily the [Manufacturer](/erpnext/manufacturer) of an Item, it's only the name under which a product is sold. For example, if you manufacture plastic cups, you may license them to a big brand so that they sell them under their Brand.

In ERPNext, Brands can be assigned to Items for identifying and assigning certain defaults.

To access the Brand list, go to:

> Home > Selling > Sales > Brand

## 1. How to Create a Brand

1. Go to the Brand list and click on New.
2. Enter a Brand name and enter a description if needed.
3. Save.
  [Brand](/files/brand.png)

Now this Brand can be associated with different Items.

![](/files/item_brand.png)

## 2. Features

### 2.1 Setting defaults for Items of this Brand

![](/files/brand_defaults.png)

The following defaults can be set for a Brand. On assigning this brand to an Item, the set defaults will be fetched when performing Sales/Purchase transactions with Item of this Brand.

- **Default Warehouse**: The Warehouse from which the Item will be sourced/stored depending on the transaction.
- **Default Price List**: The Price List set here will be fetched in Purchase/Sales transactions.

#### Purchase Defaults

When performing Purchase transactions like Purchase Order, Purchase Receipt, or Purchase Invoice, the defaults set here will be fetched on selecting Item of this Brand.

- Default Buying Cost Center
- Default Supplier
- Default Expense Account

#### Sales Defaults

When performing Sales transactions like Sales Order, Delivery Note, or Sales Invoice, the defaults set here will be fetched on selecting Item of this Brand.

- Default Selling Cost Center
- Default Income Account

## 3. Related Topics

1. [Purchase Order](/erpnext/purchase-order)
2. [Sales Order](/erpnext/sales-order)
3. [Purchase Receipt](/erpnext/purchase-receipt)
4. [Delivery Note](/erpnext/delivery-note)
5. [Sales Invoice](/erpnext/sales-invoice)
6. [Purchase Invoice](/erpnext/purchase-invoice)


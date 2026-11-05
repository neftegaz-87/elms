---
title: "Stock Settings"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/stock-settings"
updated: "2026-06-13"
---

You can set default settings for your stock-related transactions from the Stock Settings page...

### Item Naming By

---

![Stock Settings](/files/stock-settings-1.png)



By default, the Item Name is set as per the Item Code entered. If you want Items to be named by a set [Naming Series,](/erpnext/naming-series) choose the 'Naming Series' option.

## Defaults

---

### Default Item Group

This will be the default item group allocated to a newly created item. Item groups are useful for classification and setting properties for the whole group. To know more visit the [Item Group](/erpnext/item-group) page.

### Default Stock UOM

The default unit of measure for stock is set as numbers (Nos), it can be changed from here.

### Default Warehouse

Set the default Warehouse from which the stock transactions are done. This will be fetched into the Default Warehouse in the Item master: 

![Stock Settings](/files/stock-settings-def.png)



### Sample Retention Warehouse

This is the Warehouse where sample retentions are stored. To know more, visit [this page](/erpnext/retain-sample-stock).

### Default Valuation method

You can choose between FIFO (first in first out), LIFO (last in first out) or moving average valuation for your items. The default method is FIFO. If you select Moving Average or LIFO, new Items will be valuated on new method. You can change this when creating new Items in the Item form. Once the Item is saved, the Valuation Method cannot be changed. Read more [here](https://frappe.io/blog/erpnext-features/inventory-valuation-method-fifo-vs-moving-average).

### Limit Percent

---

This is the percentage you are allowed to receive or deliver more against the quantity ordered. For example: If you have ordered 100 units, Supplier sends 120 units and the percentage is set to 10% then you are allowed to receive 110 units. By default, this is set to 0.

### Role Allowed to Over Deliver/Receive

---

Users with this role are allowed to over deliver/receive against orders above the allowance percentage

### Show Barcode Field

---

A field to enter Barcode details for an item. If unticked, the field won't be visible in the Item form.

### Convert Item Description to Clean HTML

---

Usually, descriptions are copy-pasted from a website or Word/PDF file and they contain a lot of embedded styles. This messes up the Print view of your invoices or quotes.

To fix this, you can check "Convert Item Description to Clean HTML" in Stock Settings. This will ensure that when you save the Items, their descriptions will be cleaned up.

If you want to control your description, views, and allow any HTML to be embedded, you can uncheck this property.

### Auto insert

---

![Stock Settings](/files/stock-settings-2.png)



### Auto insert Price List rate if missing

Enabling this will insert an Item Price to the Price List of an Item automatically when using the Item in its first transaction. This price is fetched from the 'Rate' set in the first transaction with the Item. The Price List depends on whether you're using a Purchase or Sales transaction.

Note that, the Item Price will be automatically inserted only in the first transaction if not already present.

If this is unticked, the 'Standard Selling Rate' set in the Item when creating the Item will be added as Item Price.

### Automatically Set Serial Nos based on FIFO

Serial numbers for stock will be set automatically based on the Items entered based on first in first out. The Serial Numbers will be set automatically in transactions like Purchase/Sales Invoices, Delivery Notes, etc.

## Allow Negative Stock

---

This will allow stock items to be displayed in negative values. Using this option depends on your use case. For example, the stock transaction entries are entered at the weekend or month-end. In this case, negative stock needs to be enabled so that you can continue with your purchase/sales transaction entries.

Instead of enabling negative stock globally you can also enable it for specific items.

> Allow Negative Stock has removed for Serial / Batch Items from version 15. So from version 15, users won't be able to make negative stock transactions for serial /batch items even though Allow Negative Stock has enabled in the Stock Settings.

## Set Qty in Transactions based on Serial No Input

---

The quantity of items will be set according to the serial numbers. For example, if the user has added serial nos like A001, A002, and A003 then the system will set the quantity as 3 in the transaction.

## Automatic Material Request

---

![Stock Settings](/files/stock-settings-3.png)



### Raise Material Request when the stock reaches re-order level

This option is useful if you want to ensure a constant supply of raw materials/products and avoid shortage. A [Material Request](/erpnext/material-request) will be raised automatically when stock reached the re-order level defined in the [Item form](/erpnext/item#34-automatic-reordering).

### Notify by Email on the creation of automatic Material Request

An email will be sent to notify the User with the role 'Purchase Manager' when an automatic Material Request is created.

## Inter Warehouse Transfer Settings

---

![Delivery Note Material Transfer](/files/inter-warehouse.png)



### Enable customer warehouse for material transfer from Delivery Note and Sales Invoice

This option is useful when material transfer needs to be presented as a Delivery Note. For example, if there are statutory requirements where taxes are to be applied on each transfer of Material. It is easier to manage in a transaction like Delivery Note, than in the Stock Entry

### Enable supplier warehouse for material transfer from Purchase Receipt and Purchase Invoice

Similar to above option this option is useful when material transfer needs to be presented as Purchase Receipt.

To know more about inter warehouse material transfer via Delivery Note and Purchase Invoice please refer this article [Material Transfer From Delivery Note](/erpnext/material-transfer-from-delivery-note)

## Freeze Stock Entries

---

The User will not be allowed to make stock postings beyond this date.

![Stock Settings](/files/stock-settings-4.png)



- **Stock Frozen Upto**: A threshold date till which stocks will be frozen.
- **Freeze Stocks Older Than [Days]**: Stocks older than x days will be frozen. This is calculated based on the creation date of the item.
- **Role Allowed to edit frozen stock**: The role you choose here will be allowed to edit frozen stock.

### Batch identification

---

Global setting for batches of stocks to be identified by a [Naming Series](/erpnext/naming-series). You can override this in the Item DocType.

## Allow to Edit Stock Quantity

---





Enable "Allow to Edit Stock UOM Qty for Sales Documents / Allow to Edit Stock UOM Qty for Purchase Documents" in the stock settings.

![stock_settings_edit_stock_qty](/files/stock_settings_edit_stock_qty.png "stock_settings_edit_stock_qty.png")

## Allow to Edit Qty as per Stock UOM in Stock Entry

---

![](/files/Screenshot 2026-06-13 at 7.35.49 PM.png)



### **Why to Edit Stock Qty / Qty as Per Stock UOM**

If you're using multi-uom and your stock uom is a whole number, then you might face the issue that the Stock UOM should be non-decimal. Users experience this problem when they are unable to set an accurate conversion factor..

**Solution**

User will set the Stock Quantity and system will calculate the conversion factor

![stock_qty_editable](/files/stock_qty_editable.gif "stock_qty_editable.gif")



### Allow UOM with Conversion Rate Defined in Item

---

If enabled, the system will allow selecting UOMs in sales and purchase transactions only if the conversion rate is set in the item master.

![UOM Restriction](/files/Screenshot%202025-03-31%20at%204.03.34%20PM.png)
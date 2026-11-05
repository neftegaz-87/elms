---
title: "Serial Number"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/serial-no"
updated: "2026-09-16"
---

> Allow Negative Stock has removed for Serial / Batch Items from version 15. So from version 15 users won't be able to make negative stock transactions for serial /batch items even though Allow Negative Stock has enabled in the Stock Settings.



To enable serial / batch feature for the item, first check the 'Enable Serial and Batch No for Item' checkbox in the 'Stock Settings'.

![](/files/Screenshot 2026-03-06 at 11.52.18 AM.png)



As discussed in the [Item](/erpnext/item) page, if an **Item** is *serialized*, a **Serial Number** (Serial No) record is maintained for each quantity of that **Item**. This information helps track the location of the Serial No, its warranty and end-of-life (expiry) information.

You can also track from which **Supplier** you purchased the **Serial No** and to which **Customer** you have sold it. The **Serial No** status will tell you its current inventory status.

If your Item is *serialized* you will have to enter the Serial Nos in the related column with each Serial No in a new line. You can maintain single units of serialized items using Serial Number.

To access the Serial Number list, go to: &gt; Home &gt; Stock &gt; Serial No and Batch &gt; Serial No

1. Prerequisites

---

Before creating and using a Serial Number, it is advised that you create the following first:

- [Item](/erpnext/item)
- Enable 'Has Serial No' in the Item master ![Serial No Enabled](/files/serial-no-enabled.png)

2. How to create a Serial Number

---

Usually, Serial Numbers are auto-created when transactions are made against a serialized Item. This works only when 'Has Serial No' is enabled and a series is set in the Item master.

For example, a series was set for the following Item as 'PB2L.#####'. Then a Stock Entry was submitted to receive the Item. The Serial Numbers were created accordingly.

![Serial No Created](/files/serial-no-created.png)



However, if you want to create a Serial No *manually* follow these steps:

1. Go to the Serial Number list, click on New.
2. Enter a Serial Number.
3. Enter the Item Code and details will be fetched.
4. If any transaction is done with an item, Serial No cannot be set or unset.
5. Save.

Inventory of an Item can only be affected if the Serial No is transacted via a Stock transaction (Stock Entry, Purchase Receipt, Delivery Note, Sales Invoice). When a new Serial No is created directly, its Warehouse cannot be set.

![Serial Number](/files/serial-no.png)



### 2.1 Notes about Serial Number

- The Status is set based on Stock Entry.
- Only Serial Numbers with status 'Available' can be delivered.
- Serial Nos can automatically be created from a Stock Entry or Purchase Receipt. If you mention Serial No in the Serial Nos column, it will automatically create those serial Nos.
- If in the Item Master, the Serial No Series is mentioned, you can leave the Serial No column blank in a Stock Entry / Purchase Receipt. Serial Nos will automatically be set from that series.

3. Features

---

### 3.1 Purchase/Manufacture details

The document from which the Serial No was created will be shown. If you purchased it from a Supplier, it'll be linked here.

### 3.2 Delivery Details

If the Serial No was generated from a Sales Order, the Customer will be linked here.

### 3.3 Warranty/AMC Details

If the Item is under warranty or AMC (Annual Maintenance Contract), the expiry dates for these can be set.

### 3.4 Use Serial No Wise Valuation



For more details please check the [link](https://docs.frappe.io/erpnext/use-serial-no-wise-valuation)

---

### 5. Related Topics

1. [Item Codification](/erpnext/item-codification)
2. [Item Variants](/erpnext/item-variants)
3. [Serial Number Naming](/erpnext/serial-no-naming)
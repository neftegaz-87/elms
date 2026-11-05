---
title: "Purchasing in Different UoM"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/purchasing-in-different-unit"
updated: "2026-09-29"
---

Each item has a stock unit of measure (UoM) associated with it. For example, the UoM of a pen could be numbers (Nos), and sand could be stocked in kg. However, when you place an order with a supplier, the UoM for an item could change. For example, you might order one box of pens, or one truck of sand. When creating a purchase transaction, you can change the Purchase UoM for an item.

Scenario:

Item Ballpoint Pen is stocked in Nos, but purchased in Box. Hence, we will make a Purchase Order for pens in Boxes.

#### Step 1: Edit UoM in the Purchase Order

In the Purchase Order Items table, open the item row. You will find two UoM fields:

- **UOM**
- **Stock UOM**

In both fields, the default UoM of the item is fetched. Edit the **UOM** field and select the Purchase UoM (Box in this case). Updating the Purchase UoM is mainly for the supplier's reference. In the print format, you will see the item qty in the Purchase UoM.

#### Step 2: Update UoM Conversion Factor

If one Box contains 20 Nos of pens, the **UOM Conversion Factor** will be 20. If the conversion factor is set in the Item master, it is fetched automatically.

Based on the Qty and Conversion Factor, the qty is calculated in the Stock UoM of the item and shown in **Qty in Stock UOM**. In the example below, 5 Boxes are purchased, so the Qty in Stock UOM is 100.

![UOM, Stock UOM and Conversion Factor in Purchase Order item](/files/buying-po-item-uom.webp)

### Stock Ledger Posting

Irrespective of the Purchase UoM selected, the stock ledger posting is done in the default (stock) UoM of the item. Hence, ensure that the conversion factor is entered correctly while purchasing an item in a different UoM. In the example below, receiving 5 Boxes adds 100 Nos to the stock.

![Stock Ledger in Stock UOM](/files/buying-stock-ledger-pen.webp)

### Set Conversion Factor in Item

You can list all the possible UoMs of an item, along with their conversion factors, in the Item master. To do this, go to:

> Stock &gt; Item &gt; open the Item &gt; UOM

In the **UOM Conversion Details** table, add each **UOM** with its **Conversion Factor**. For example, 1 Box = 20 Nos, so the conversion factor is 20. You can also set the **Default Purchase Unit of Measure** in the **Purchasing** tab of the Item, so it is fetched automatically in purchase transactions.

![UOM Conversion Details in Item](/files/buying-item-uom-box.webp)
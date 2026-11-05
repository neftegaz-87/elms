---
title: "Subcontracting"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/subcontracting"
updated: "2026-02-27"
---

**In subcontracting, you employ an external party to carry out tasks for your organization, especially manufacturing.**

Subcontracting is a type of job contract that seeks to outsource certain kinds of work to other companies. It allows work on more than one phase of the project to be done at once, often leading to quicker completion.

Subcontracting is practised by various industries. For example, manufacturers who make several products from complex components subcontract certain components and package them at their facilities.

If your business involves outsourcing certain processes to a third-party Supplier where you supply the raw materials and the third party does the labour/production, you can track this by using the subcontracting feature of ERPNext.

## How to Set up Subcontracting

---

1. Create a Service Item (Non-stock Item). It represents the service cost of the subcontracted operation.
  ![](/files/image0cf7e0.png)
2. Create separate Items for the unprocessed and the processed product. For example, if you supply unpainted X to your Supplier and the Supplier returns you X, you can create two Items: “X-unpainted” and “X”.
3. Create a Warehouse for your Supplier so that you can keep track of Items supplied. (You may supply a month's worth of Items in one go).
4. For the processed Item, in the Item master, enable “Supply Raw Materials for Purchase”.
  ![](/files/imageb3b64c.png)

### Creating a BOM

Make a [Bill Of Materials](/erpnext/bill-of-materials) for the processed Item, with the unprocessed Items as sub-items. Let's consider a simple example, where you manufacture a pen. The processed pen will be named under the Bill of Materials(BOM), whereas the nib, plastic, ink, etc. ,will be categorized as sub-items.

This BOM will be without Operations if all of the production work is done by a third party. Let's see with a simple example of a CPU Assembly:

![](/files/imagefbe036.png)

### Creating a Subcontracting BOM

While optional, creating a Subcontracting BOM allows you to predefine a relationship between your Service Item and Finished Good Item.

When you create a Subcontracted Purchase Order, if you have created a Subcontracting BOM for your Service Item or Finished Good Item, selecting either one will automatically fill out the other details of the Purchase Order line item. If you create a lot of Subcontracted Purchase Orders for the same Service Item and Finished Good Item combination, you can save some time and effort by creating a Subcontracting BOM for that combination in advance.

Using a Subcontracting BOM, you can:

1. Select a default BOM for your Finished Good Item.
2. Select a default UOM for your Service Item.
3. Specify the conversion factor between your Service Item and Finished Good Item.

![](/files/imaged3e66b.png)

In the above image, we have specified that 1 unit of "Painting" will produce 2 units of "Tiles" after the subcontracting process is complete. Upon saving this document, you will see that the conversion factor for this relationship is calculated automatically (0.5 in this case).

Note:

1. There can only be 1 Subcontracting BOM for any Finished Good Item.
2. If there are multiple Subcontracting BOMs for a single Service Item, upon making a Subcontracted Purchase Order and selecting that Service Item, a dialog box will appear which will ask you to select the Finished Good Item for that specific Service Item. The list of those Finished Good Items will be fetched from the list of Subcontracting BOMs, where the Service Item is the one you have entered.

### Creating a Purchase Order

Make a Subcontract Purchase Order for the Service Item and select the Finished Good Item, the one for which you've created a BOM.

1. Enable the "Is Subcontracted" since this Purchase Order is for Subcontracting.
  ![](/files/po - subc.png)
2. Here the Rate field value of the Items table in the Purchase Order will be the service cost you have agreed with the third party or the Supplier.
3. After filling in the details, Save and Submit the [Purchase Order](/erpnext/purchase-order#35-raw-materials-supplied).

### Creating a Subcontracting Order

Make a Subcontracting Order for the Purchase Order by clicking on Create > Subcontracting Order. When you “Save”, in the “Raw Materials Supplied”, all your un-processed Items will be updated based on your Bill of Materials. You can also select the Warehouse in which the raw materials would be reserved for subcontracting under Reserve Warehouse.



![](/files/Screen Recording 2026-02-17 at 11.43.42 AM.mov)











1. The costs involved with the subcontracting process should be recorded in the Rate field of the Items table in the Subcontracting Order shown as follows:
  ![](/files/image0c3d0a.png)
2. In the previous image, we are providing the subcontractor with the following items:
  ```
  8 Motherboards
  8 Processors
  16 RAMs
  8 Hard Disks
  8 Cabinets
  The cost for one CPU including Raw Materials and Service Costs is 1,02,994 and the total cost for all CPUs is 8,23,952
  ```
  ![sco items row qty rate](/files/sco-items-row-qty-rate.png)
3. From a Subcontracting Order, select the raw materials to transfer to the subcontractor:
  ![](/files/subcontracting order.mp4)


4. Once the Subcontracting Order is submitted, you can also view the item's reserved quantity on the item dashboard.

![](/files/imageff75a7.png)

### Creating Stock Entry to Transfer Raw Materials

Now that the raw materials are reserved, make a Stock Entry and deliver the raw material Items to your Supplier.

In the Subcontracting Order, click on Transfer > Material to Supplier. Set the Source and Target Warehouses. The Stock Entry will be of type 'Send to Subcontractor' where you transfer from one Warehouse to another. Tick 'From BOM', select the BOM, enter the quantity, and click the Get Items button.

![](/files/image4e5ebf.png)

### Creating a Subcontracting Receipt to receive the Finished and Scrap items

Receive the Items from your Supplier using a Subcontracting Receipt. You need to enter the Supplier Warehouse from where the raw materials will be taken and finished goods will be received in the Accepted Warehouse. Consider this like a backflush for subcontracting.

Click on Create > Subcontracting Receipt from the Subcontracting Order. Set the Accepted and Supplier Warehouses. Make sure to check the “Consumed Quantity” in the “Raw Materials” table so that the correct stock is maintained at the Supplier’s end. You need to select the Supplier's Warehouse where you'll receive the finished goods.

Scrap items are fetched from the chosen Bill of Materials (BOM) for Finished Goods within the Items table. The Qty is computed using the Qty of the Finished Good Item, while the Rate is determined by either the Valuation Rate or the Scrap Rate specified in the BOM.



![](/files/Screen Recording 2026-02-19 at 10.51.47 AM.mov)





#### Service Expense Account in Subcontracting Receipt

User can set the expense account for the service item in the subcontracting receipt.

![](/files/image564411.png)

If the user sets the expense account in the service item, the same account will be auto-filled in the Service Expense Account field. The user can also manually set the service expense account in the subcontracting receipt. If no service expense account is set, the system will use the Finished Item’s expense account to book the service cost. Once the subcontracting receipt is submitted, the system books the service cost against the service expense account.

![](/files/imagea0223e.png)

### Backflush of Raw Material

![](/files/image4ba089.png)

- **BOM**
  - If you set backflush based on BOM, system will consume raw materials even though you have not transferred materials against the Subcontracting Order and have enough stock at supplier's warehouse.
- **Material Transferred for Subcontract** 
  - If you set backflush based on "Material Transferred for Subcontract" system will consume raw materials based on the materials transferred against the Subcontracting Order. If no stock transferred then no materials will be consume at the time of Subcontracting Receipt.

### Creating a Purchase Receipt

Back to Purchase Order, click on `Create > Purchase Receipt.` There will be no effect on the Stock Ledger and Accounting Ledger since both the Stock and Accounting Ledger are updated when you Submit the Subcontracting Receipt. In case you have "Purchase Taxes and Charges" the Accounting Ledger will update accordingly.

### Supplier Sourced Raw Material

While creating a BOM for subcontracting, there might be a few raw materials like nuts and bolts that the Suppliers will have to procure themselves.

While creating a Stock Entry for "Transfer" from a Subcontracting Order, these items can be excluded one by one, but it is impossible to do so if you have more than 100 items.

If some raw material is sourced by the Supplier directly, then such raw materials have to be included in the BOM.

- It will have zero value in BOM
- In the Subcontracting Order, this raw material will not appear in Supplied Items since it is not supplied
- Also, while creating a "Transfer", such items will be excluded from the Stock Entry

![](/files/imaged2428f.png)

However, the Supplier may choose to include the supplier-provided items in their Sales Order sent to you.

## Notes

---

- Make sure that the “Rate” of the processed Item is the processing/service cost (excluding the raw material cost).
- ERPNext will automatically add the raw material rate for your valuation purpose when you receive the finished item in your stock.
- ERPNext will automatically default the 'Reserve Warehouse' in the Subcontracting Order from the BOM. If not found in the BOM, it would default it from the default Warehouse set in the Item. You can set the default Reserve Warehouse for all the Items in the Subcontracting Order from the 'Reserve Warehouse' field in the Raw Materials Supplied section.

:::note
New in V16
:::



## Features

### Creating multiple Subcontracting Orders from a single Subcontracted Purchase Order

ERPNext now allows users to create multiple Subcontracting Orders from a single Purchase Order.

How to use:

1. When you click on Create Subcontracting Order from your Purchase Order, by default ERPNext will fill the Finished Good Items and Service Items table based on the Purchase Order.
2. The user is now allowed to edit the quantity of each Finished Good Item as per their needs.
3. If you create a partial Subcontracting Order and then try to create a new one against the same PO, ERPNext will automatically calculate the remaining quantity left to subcontract and fill out the new document accordingly.

Note:

1. Once the PO is fully subcontracted ie. no items in the PO are left to be subcontracted, user will not be allowed to create new Subcontracting Orders from the PO.
2. The quantity entered by the user cannot exceed the available quantity to subcontract (fetched from the PO).

In both the above cases, an error will be thrown accordingly.

### Stock Reservation

In ERPNext v16, you can now reserve the Raw Materials to be sent to the Supplier.

Just above the Raw Materials table, you will now see the checkbox `Reserve Stock`. If you check this option and submit the Subcontracting Order, the stock will be reserved against the Subcontracting Order which will essentially make sure that the committed stock is not used anywhere else by mistake. The reserved stock will be automatically utilised if and when Raw Material is sent to the Supplier by using the `Send to Subcontractor` Stock Entry made against the Subcontracting Order.

![](/files/image3fc0a5.png)

Note that if the `Auto Reserve Stock` option is enabled in `Stock Settings`, this option will be checked by default.



## Related Topics

---

1. [Purchase Order](/erpnext/purchase-order)
2. [Purchase Receipt](/erpnext/purchase-receipt)
3. [Quality Inspection](https://docs.erpnext.com/docs/user/manual/en/quality-inspection)


---
title: "Subcontracting Inward"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/subcontracting-inward"
updated: "2026-07-22"
---

**In Subcontracting Inward, a customer employs you to carry out tasks for their organization, especially manufacturing.**

Not to be confused with the [standard Subcontracting module in ERPNext](https://docs.frappe.io/erpnext/user/manual/en/subcontracting). This is an extension of that module, which allows you to do the exact inverse of it, that is, instead of you outsourcing your manufacturing process to a third party (Supplier), a third party (Customer) outsources their manufacturing process to you.

While this was already possible in ERPNext even before v16, this heavily streamlines the entire process, thereby making it very easy to use.

## Features

1. Receive Raw Materials from Customer without impacting your books
2. Track Raw Materials that you have received from the customer
3. Use extra Raw Materials given by the customer on a per transaction basis if needed
4. Use Raw Materials sourced by you along side the Raw Materials given by the customer and bill them to the customer
5. Reserve the Raw Materials received by the customer to prevent accidental use of the stock committed against another order
6. Create additional Work Orders incase of process loss during manufacturing
7. Optionally, deliver overproduced quantity incase of overproduction
8. Return Raw Materials to customer if required (for ex. QC failure, sent by mistake etc.)
9. Optionally, deliver secondary items produced during manufacturing to the customer
10. Incase of serial or batch Finished Good item, deliver items with the same serial and/or batches that were produced against the order
11. Receive the Finished Goods from the Customer if required (ex. QC fail)

## Prerequisites

1. Every Customer needs to have their own warehouse (dummy) in the masters. This is done by creating a new Warehouse and setting the newly added Customer Link field.
  ![](/files/image311f04.png)
2. While optional, we strongly recommend you to create a group warehouse which will hold all the customer warehouses in it as it will make data analysis much easier. Note that a Group Warehouse does not need the `Customer` Link field set however if your Customer has multiple warehouses, we recommend you to structure the warehouses accordingly.
  ![](/files/image5313b0.png)
3. The Raw Materials provided by the Customer in the Item master. Each Customer Provided Item needs to have the field set in the master. Conversely, Customer Provided Items cannot be purchased so the `Allow Purchase` field has to be unchecked (checked by default in ERPNext).

![](/files/image68b05b.png)

4. The non-stock/service item that will be sold or billed to the Customer. The `Maintain Stock`  field has to be unchecked (checked by default in ERPNext) for this.
  ![](/files/image608243.png)
5. The Finished Good to be produced needs to be marked as a Subcontracted Item

![](/files/image7b1ac7.png)

6. A standard ERPNext [Bill of Materials or ‘BOM’](https://docs.frappe.io/erpnext/user/manual/en/bill-of-materials) for the finished good to be produced.
7. A Subcontracting BOM which specifies the relationship between the non-stock/service item and the Finished Good to be produced. Note that it is also possible to create a Subcontracted Sales Order even without a Subcontracting BOM provided that the Finished Good to be produced has a default BOM set in it’s master.

![](/files/imageecae7c.png)

## How to use

1. Start by creating a Sales Order and check the “Is Subcontracted” checkbox. The Sales Order will now be subcontracted and the schema/form of the child table will change. Proceed by setting the service item in the `Item Code` field. If you have a Subcontracting BOM for this service item, the Finished Good field will be set automatically. Upon changing the quantity of the Service Item, the quantity of the Finished Good will also change based on the conversion factor in the Subcontracting BOM. If you have multiple Subcontracting BOMs for the same service/non-stock item, a dialog box will popup asking you to select the Finished Good from the Subcontracting BOMs present against that service/non-stock item. Save and submit once done.
  ![](/files/image002276.png)

![](/files/image5cd122.png)

2. From the Sales Order, click on `Create > Subcontracting Inward Order`. This DocType holds the list of Finished Goods, Raw Materials required, Service Items and secondary items (if produced). Start by selecting the Customer warehouse you created at the start of the process. If only a single Customer warehouse exists against the Customer, the field will be pre-filled with it. Then select a Delivery Warehouse for each of the Finished Goods to be produced. This will be where the Finished Goods produced by you will be delivered. If all the Finished Goods are to be delivered to the same warehouse, use the `Set Delivery Warehouse` field to set the delivery warehouse for all the Finished Goods in one go.

![](/files/image24b2d8.png)

3. If you need to “explode” the BOM, click on the Finished Good (pencil icon towards the right of the row) and check the `Include Exploded Items` field and click on save. You will see that the Raw Materials in the “Required Items” table will be updated with the exploded items. You may also additionally alter the quantity of the Finished Goods. This will allow you to create another Subcontracting Inward Order against the same Subcontracted Sales Order until the item is fully subcontracted should you need that.

![](/files/image85b6ee.png)

4. Save and submit the Subcontracting Inward Order. You can now receive Raw Materials from the Customer which will be used for the manufacturing process by clicking on Receive -> Raw Material from Customer. This will create a Stock Entry and the Raw Materials will be filled automatically upon creation. You may also additionally add extra Customer Provided Items here should you need it. The extra items, if added, will also be visible in the Required Items table of the Subcontracting Inward Order upon submission of the Stock Entry. Note that for additional Customer Provided Items, you will mandatorily need to specify the Finished Good against which you will be using the Raw Material using the `Against Finished Good` field in the child table.
  ![](/files/image9daef2.png)
5. In this Stock Entry, you may enter the basic rate for each item. Note that this is done purely for taxation purposes and will have no accounting impact on the valuation of your stock. You may verify this by clicking on `View> Accounting Ledger` after submission of the Stock Entry. You will see that everything will be 0.
  ![](/files/image710092.png)
6. It is also possible to create more Stock Entries to receive additional Customer Provided Items at any time, even after receiving the required quantity of the Raw Materials as per the Finished Good’s BOM.
7. Go back to the Subcontracting Inward Order and reload the page. You will now see two new buttons at the top right, “Return” and “Create”. By clicking on `Return > Raw Materials` to Customer, you can return the Raw Material to the customer if needed. By clicking on `Create > Work Order`, a standard Work Order will be created for each of the Finished Good(s) based on the quantity of Raw Materials available for production. Use this Work Order to produce the Finished Good(s) then go back to the Subcontracting Inward Order and reload the page.
  ![](/files/image33a853.png)

:::note
Additional Raw Materials used in the Manufacturing Stock Entry against Work Orders will also be added to the Required Items table in the Subcontracting Inward Order.
:::



8. You will now see the option for “Subcontracting Delivery” under the “Create” button. A new Stock Entry will be created upon clicking it which you can use to deliver the Finished Good(s) to the Customer.

Notes

1. By default, ERPNext will not add the generated secondary Item(s) to this Stock Entry. If you need to deliver the secondary Item(s) generated as well, enable the `Deliver secondary items` in the `Selling Settings` Single DocType.
2. ERPNext by default will only you to deliver the agreed upon quantity if Finished Good(s) as specified in the Subcontracted Sales Order. If you have produced more than the required quantity and want to deliver the overproduced quantity as well, enable the `Allow Delivery of Overproduced Qty` in the `Selling Settings` Single DocType.

![](/files/imagef78089.png)

9. Go back to the Subcontracting Inward Order and reload the page. You will now see the option “Subcontracting Return” under the “Return” button. On clicking it, a new Stock Entry will be created which will allow you to receive the Finished Good(s) that you have produced and delivered to the Customer should you need it.
10. Since the Finished Goods have been produced and delivered, it is time to bill the Customer. Go to the Sales Order created in the first step, from here you can deliver the service/non-stock item by creating a Delivery Note and bill it as well as all the Raw Materials you have used in the process. The Raw Materials procured by you (not provided by the Customer) will already be present in the child table when you create the Sales Invoice against the Subcontracted Sales Order.

Note You can deliver and bill the service/non-stock items even without creating a single Subcontracting Inward Order.

![](/files/imageec69eb.png)

## Important Notes

1. [Stock Reservation](https://docs.frappe.io/erpnext/user/manual/en/stock-reservation) Entries will be created and used extensively by default in this process even if its disabled in `Stock Settings`.
2. If the Raw Material received from the Customer goes unused, it cannot be directly used in another Subcontracting Inward Order. We recommend you to return the unused Raw Material to the Customer and receive it again using another Subcontracting Inward Order where it is to be reused. You do not need to move the Raw Material physically for this and it will be a pure dummy transaction.
3. For any Subcontracting Inward transaction where multiple batches are involved for an item, the Serial and Batch Bundle feature is to be used. Duplicating of child tables is not recommended or even permitted in various transaction types throughout.
4. It is mandatory for the Finished Good BOM to have atleast 1 Customer Provided Item.
5. Do not cancel any Stock Reservation Entries related to the Subcontracting Inward process, doing so will most definitely cause unintended consequences.
6. Using [Alternative Items](https://docs.frappe.io/erpnext/user/manual/en/item-alternative) in Work Orders created against Subcontracting Inward Orders is currently not supported and the checkbox is hidden for the same.
7. While you *can* use [Inventory Dimension](https://docs.frappe.io/erpnext/user/manual/en/inventory_dimension) in this process, it is not officially supported as of yet.
8. [Continuous Raw Material Consumption](https://docs.frappe.io/erpnext/user/manual/en/manufacturing-settings#1-allow-continuous-material-consumption) and [Disassembly Order](https://docs.frappe.io/erpnext/user/manual/en/disassembly-order) are also not supported as of yet.
9. To accurately reflect the value of the finished goods, a *batched item* is recommended. For example: if you have purchased stock of the finished good in the past and its sitting in the same warehouse as your manufactured batch, FIFO will consider the value of the purchased good in the `Deliver to Customer` Stock Entry instead of the batch you manufactured against the Subcontracting Inward Order. A batched item with `Batch-wise Valuation` enabled will ensure that this does not happen.
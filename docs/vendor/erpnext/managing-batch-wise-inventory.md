---
title: "Managing Batch wise Inventory\n"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/managing-batch-wise-inventory"
updated: "2026-02-27"
---


Set of items which has same properties and attributes can be group in a single Batch. For example, pharmaceuticals items are batch, so that it's manufacturing and expiry date can be tracked together.

To maintain batches against an Item you need to mention 'Has Batch No' as yes in the Item Master.

![Batch Item](/files/batchwise-stock-1.png)

You can create a new Batch from:

`Stock > Documents > Batch > New`

Read [Stock batch](/erpnext/batch.html) to learn more.

For the Batch item, updating Batch No. in the stock transactions (Purchase Receipt &amp; Delivery Note) is mandatory.

#### Purchase Receipt

When creating Purchase Receipt, you should create new Batch, or select one of the existing Batch master. One Batch can be associated with one Batch Item.

![Batch in Purchase Receipt](/files/batchwise-stock-2.png)

#### Delivery Note

Define Batch in Delivery Note Item table. If Batch item is added under Product Bundle, you can update it's Batch No. in the Packing List table as well.

![Batch in Delivery Note](/files/batchwise-stock-3.png)

#### Batch-wise Stock Balance Report

To check batch-wise stock balance report, go to:

Stock > Standard Reports > Batch-wise Balance History

![Batchwise Stock Balance](/files/batchwise-stock-4.png)

<iframe allowfullscreen="" frameborder="0" src="https://www.youtube.com/embed/J0QKl7ABPKM?rel=0">
</iframe>



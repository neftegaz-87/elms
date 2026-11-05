---
title: "Bulk Update\n"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/bulk-update"
updated: "2026-04-14"
---

**Bulk Update allows you to update a particular field of a DocType for all documents.**

To access Bulk Update, go to:

> Home > Bulk Update

Consider that you have 20 quotations in which you had selected 'All Territories' and now you want to change the Territory to France. Instead of updating the individual quotations manually, you can use Bulk Update to update all 20 Quotations at once.

To do this,

1. Go to Bulk Update.
2. Select the Document Type, like Quotation.
3. Select the field to update, like territory.
4. Enter a **valid** new value to be updated.
5. Enter any conditions that apply, for example: {"status":"Draft"} will only affect documents in the Draft stage.
6. Select the limit, i.e. number of documents (Quotations) to be updated.
7. Click on Save

![](/files/imagea8e50c.png)

:::note
You can only update fields that can be updated normally in a particular stage. For example, valid till date cannot be updated for submitted Quotations.
:::




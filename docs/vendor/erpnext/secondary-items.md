---
title: "Secondary Items"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/secondary-items"
updated: "2026-08-26"
---

:::note
**Available only in version 16 of ERPNext**
:::



Starting from version 16, Scrap Items table in the BOM DocType has been renamed to Secondary Items table. The secondary items table now includes items of 3 more types: `Co-Product`, `By-Product` and `Additional Finished Good` . Using this table, users can now specify the distribution of the outgoing cost (or raw material cost) amongst all the outputs based on a percentage system.

Let's first understand the difference between `Scrap`, `Co-Product` , `By-Product` and `Additional Finished Good`.

1. Scrap: An item which is produced alongside the Finished Good which, in most cases, does not have much value.
2. Co-Product: Item produced alongside the main Finished Good which is planned and has significant value.
3. By-Product: This item is produced alongside the finished good which is not planned. This item may or may not have significant value.
4. Additional Finished Good: This item is planned and has significant value. It is usually produced separately from extra materials, leftover capacity or further processing.

In ERPNext, there is virtually no difference on how these secondary items' value and quantity is calculated. The different names are merely for distinction purposes.

You can specify the process loss percentage and cost allocation percentage of each secondary item in the table.

![](/files/image01125b.png)

In this example, we are saying that in manufacturing petrol, 10% of the outgoing (raw material) cost should be allocated to LPG and 5% to Bitumen. The remaining 85% will be allocated to the actual finished good (Petrol).

Let's see it in action:

![](/files/CleanShot 2026-03-11 at 12.31.02@2x.png)

Here, the outgoing cost is Rs. 100. 10% of 100 is 10 which is allocated to LPG and 5% is 5 which is allocated to Bitumen. Since we specified a 5% process loss for Bitumen, it's quantity has been calculated as 9.5 ( `10 - (5% * 10)`).

:::note
**If you are migrating from earlier versions of ERPNext, the scrap items table will stay as it was. The calculations in Manufacture Entry and Subcontracting Receipt will stay the same as it was before migrating.**
:::
---
title: "Item Group"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/item-group"
updated: "2026-03-06"
---

**An Item Group is a way to classify items based on types.**

Depending on the type of product, you can categorize an item under its respective field. If the product is service-oriented, assign it under the Item Group - service. If the product is used as a raw-material, assign it under the Raw Material category. In case, an item is used only in trading, you can categorize it under an Item Group called Trading.

To access the Item Group list, go to: 

> Home > Stock > Items and Pricing > Item Group

This is what the Item Group tree looks like: 

![](/files/item_groups.png)

## How to create an Item Group

---

1. Go to the Item Group list, click on New.
2. Select a group node under which you wish to create the Item Group, the default root is 'All Item Groups'.
3. Select 'Add Child' or click on the New button.
4. To make this child a category/group node, tick on Group Node.
5. Click on Create New.

Note:

- Nodes in different parts of the tree cannot have the same name.
- The child notes get alphabetically arranged

![](/files/item-group-new2af55d.gif)

### 1.2 Delete an Item Group

1. Select the Item Group you want to delete.
2. Select 'Delete'.
3. Click on Yes.
4. Features

---

To see the following options, click on an Item Group, click on Edit.

### 2.1 Parent Item Group

You can change the parent Item Group of an item by choosing another one under General Settings.

### 2.2 Defaults

- **Default Price List**: A default price list that'll determine the Item Prices for this Item Group.
- **Default Warehouse**: The default Warehouse is set in transactions for the items that belong to this group.
- **Default Buying/Selling Cost Centre**: The default Buying/Selling Cost Centre to which items in this group will be billed against.
- **Default Expense/Income Account**: The default accounts for items that belong to this group.
- **Default Supplier**: On setting a Supplier here, this supplier will be chosen in purchase transactions by default for items in this group.

### 2.3 Item Tax

A default item tax template will be applied to all items belonging to this group. Similarly a Tax Category can also be selected, visit [Quotation](/erpnext/quotation) to know more about Tax Categories.

### 2.4 Website Settings

- **Show in Website**: Items belonging to this group will be shown on your website under the Item Group.
- **Weightage**: This is the weight for the Item Groups themselves, item groups with higher weights will be shown first.
- **Slideshow**: A slideshow for the Item Group, just like in an Item. Visit the [Homepage](/erpnext/homepage) page in Website module to know more.
- **Description**: This will appear on the Item Group page.
- **Website Specifications**: Label and its description for an item group.


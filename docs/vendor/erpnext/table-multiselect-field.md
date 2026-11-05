---
title: "Table MultiSelect Field"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/table-multiselect-field"
updated: "2026-03-04"
---

The Table MultiSelect field is very similar to Link Field. The key difference is that Table MultiSelect field allows you to select multiple values.

Let us consider an example to understand the same. Let's say you want to assign a ToDo to multiple users, as shown below:

![Screenshot 2024-06-25 at 4.58.41 PM](/files/Screenshot 2024-06-25 at 4.58.41 PM.png)  


You can add a Table MultiSelect Field by using the following steps:

Step 1: Create a child DocType.
-------------------------------

Create a new DocType, enable 'Is Child Table' and 'Editable Grid' check-boxes and add a field with 'Link' type as shown below.

Set the link field as mandatory. Ensure that the field within the child table has "In List View" ticked.

![Screenshot 2024-06-25 at 4.55.49 PM](/files/Screenshot 2024-06-25 at 4.55.49 PM.png)  


Step 2: Add a field with type 'Table MultiSelect'.
--------------------------------------------------

Create a field with type 'Table MultiSelect' and add the DocType created in first step in 'options'.

![Screenshot 2024-06-25 at 4.57.08 PM](/files/Screenshot 2024-06-25 at 4.57.08 PM.png)  


You can remove any selected value by clicking on the cross sign next to selected value or by placing the cursor next to the value and pressing Backspace.

This field allows one value to be selected only once.

> Note: Table MultiSelect fields cannot be added in child DocTypes.


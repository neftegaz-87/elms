---
title: "Delete Company Transactions"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/delete_company_transactions"
updated: "2026-03-12"
---

ERPNext allows you to delete all the transactions like Sales Invoices, Sales Order, Payment Entries etc associated with a company, while keeping the master data intact.



Often, users setup all the master data and then create a few dummy records to test/explore the system. Then, they want to delete the dummy records and start over again.

### Transaction Deletion Record

---

This feature allows you to delete all the records associated with a specified company, except for the ones belonging to the DocTypes listed in the **Excluded DocTypes** table.

If you really want to wipe out the transactions, then follow these steps. However, the deleted transactions can't be restored.

1. Create a new "Transaction Deletion Record" document.
2. Enter the name of the Company whose records you wish to delete.
3. Modify the "Excluded DocTypes" table if needed.
4. Save and Submit.

![](/files/imageaf22f8.png)

The **Summary** table displays the names of the DocTypes whose records were deleted as well as the number of records that were deleted.



## Delete Transactions

---

1. Go to **Home > Accounting > Company** and find your company.
2. On the top right, you'll find the **Delete Transactions** button under **Manage**.
3. Enter your password.
4. Enter the company name to confirm.

![](/files/imagef7bec2.png)

This will submit a record in the Transaction Deletion Record DocType.

:::note
To perform this action, the user must have the role of System Manager.
:::




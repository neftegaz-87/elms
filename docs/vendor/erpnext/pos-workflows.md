---
title: "POS Workflows"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/pos-workflows"
updated: "2026-09-29"
---

### **POS Workflows**

#### **Open POS Session**

1. Go to **Point of Sale** workspace.
2. Select a **POS Profile**.
3. Select Customer.
4. Add items from the item list.
5. Edit quantities as needed.

*Note:* You need to set a default Warehouse for stock impact. If both Item and POS Profile define a Warehouse, the POS profile warehouse gets priority. 



 **How to Create a POS Invoice**

1. Add items to cart in the POS screen.
2. If editing rate/discount is needed, enable options in the POS Profile.
3. Click **Pay** and select payment mode.
4. Submit — a **POS Invoice** is created.

**POS Opening Entry**

Before selling, open a session with an **Opening Entry**.  
This sets the session start and can capture opening cash if required. 



**POS Closing Entry**

At the end of the session:

1. Go to **POS Closing Entry**
2. Select the POS Profile and closing period
3. Submit — stock and accounting postings occur.

**Loyalty Integration**

ERPNext supports linkage of loyalty programs to customers, allowing:

- Earning points on POS invoices
- Redemption during checkout  
To set up the loyalty program, follow the [Loyalty Program](https://docs.frappe.io/erpnext/user/manual/en/loyalty-points-redemption-in-pos) documentation.
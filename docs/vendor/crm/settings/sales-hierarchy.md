---
title: "Sales Hierarchy"
space: "CRM"
url: "https://docs.frappe.io/crm/settings/sales-hierarchy"
updated: "2026-06-02"
---

Arrange your sales team into a reporting tree so managers see the leads and deals owned by their team while everyone else sees only their own.

> Only Admins Can edit the Sales Hierarchy. For others, they can only view it in read-only mode

### Enable Sales Hierarchy

Go to Settings > User Management >  Click on "Enable" button to enable sales hierarchy for your site.

![](/files/image5c50e8.png)
*Enable Sales Hierarchy*

Once enabled:

- Sales Managers see leads and deals owned by themselves and anyone below them in the tree
- Sales Users see only what they own

Note:

- A user with Sales Manager Role cannot directly report to a Sales User
- A Sales Manager who has reportees cannot be demoted to Sales User from the frontend

---

### Adding Users

Click on the "Add User" button from the top right corner to select the users which you want to add to the hierarchy. These users will be added at the top level of the tree. 

![](/files/imaged83629.png)
*Add users*

**Add direct reports**

Reportees can be added to a manager by clicking the `+` icon. Using this you can bulk assign reportees to a manager to create a hierarchy. 

![](/files/Screen Recording 2026-05-22 at 3.46.28 PM.mov)



---

### Removing Users from hierarchy

The are three ways to remove users from the hierarchy. The options depend based on whether the user has someone reporting to them or not. 

#### **Delete**

A user who does not have any reportee can be removed without unlinking by clicking on the delete button

![](/files/Screen Recording 2026-05-22 at 3.47.53 PM.mov)



#### **Reassign And remove**

Moves their direct reports up to their own manager and then removes them from the hierarchy

![](/files/Screen Recording 2026-05-22 at 3.50.25 PM.mov)



#### **Remove with reports**

Removes the user and everyone reporting to them from the hierarchy. 

![](/files/Screen Recording 2026-05-22 at 3.52.30 PM.mov)



---

### **Managing users**

Quickly drag and drop users you want to change reporting for.

![](/files/Screen Recording 2026-05-22 at 3.54.57 PM.mov)



#### **Move a user to top level**

A Manger who reports to another manager can be moved to top level along with their reportees. 

![](/files/Screen Recording 2026-05-22 at 3.56.30 PM.mov)




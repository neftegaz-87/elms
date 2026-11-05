---
title: "Difference Between System User and Website User"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/difference-between-system-user-and-website-user"
updated: "2026-03-04"
---

**Question:** I have added my Employee as a User and have assigned them Roles as well. Still, they are not able to view Dashboard on the login.

**Answer:**

There are two type of Users in ERPNext.

* **System Users**: They are typically internal users such as employees, managers, and administrators who need extensive access to the ERPNext system to perform various business operations. They have a higher level of access and more detailed permissions, allowing them to interact with multiple modules, generate reports, and customize workflows.
* **Website Users**: They are typically external users like customers or suppliers who interact with the ERPNext system through a web portal. Their access is limited to functionalities relevant to their needs, such as placing orders, viewing order status, or managing their account information. Their interface is simpler compared to the comprehensive backend interface used by system users.

Here is the tabular comparison between System User and Website User in ERPNext



| **System User** | **Website User** |
| --- | --- |
| This type is useful for managing internal activities and operations | It is useful for managing external operations and transactions |
| It provides full access to ERPNext modules and features | It provides restricted access to ERPNext modules and features |
| Typical users in this category are internal employees  | The user persona in this type includes external parties such as customers, clients etc |
| They are created by an administrator within ERPNext | They can be self-registered or created by an administrator |
| It provides access to company-wide data and reports | It provides access to only personal data and limited reports |
| They can view, create, edit, and delete records | They can mostly view and create records relevant to them |
| They have full data entry capabilities across all modules | They have limited to data entry relevant to their role |


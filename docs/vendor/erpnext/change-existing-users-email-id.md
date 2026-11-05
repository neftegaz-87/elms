---
title: "Change existing user's email ID or Rename User"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/change-existing-users-email-id"
updated: "2026-07-02"
---

The User ID is created based on the email address. When a user is renamed, its value is updated in all existing records, including change logs. As a result, this is a resource-intensive action. If you encounter time-out issues while renaming a user, consider creating a new User ID using the updated email address and disabling the old user.

If you need to change a user's email address or username, use ERPNext's built-in **Rename** tool. This updates the user's unique ID across all linked records while preserving assignments, permissions, and historical data.



To change a User's Email Id, follow the steps: 

> **User List -> Open the User** **> Click on Menu -> Rename > Enter the New Email Id . Save** 

#### Prerequisites

You must have **Administrator** privileges to rename a user.

#### Steps

1. Go to **Settings > Users and Permissions > User**.
2. Open the user you want to rename.
3. Click **Menu** (⋮) in the top-right corner of the form.
4. Select **Rename**.
5. Enter the new email address or username.
6. Click **Save**.

#### What Happens After Renaming?

ERPNext automatically updates all references to the user across the system. This ensures that:

- Existing document links remain intact.
- Assignments continue to work.
- User permissions are preserved.
- Historical records continue to reference the renamed user correctly.

![](/files/7yWI427.gif)


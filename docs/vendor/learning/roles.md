---
title: "User Roles & Permissions"
space: "Learning"
url: "https://docs.frappe.io/learning/roles"
updated: "2026-05-12"
---

Frappe Learning uses specific roles to balance ease of use with system security. 

![](https://docs.frappe.io/files/Screenshot%202025-02-06%20at%203.25.51%E2%80%AFPM.png)
*User Profile Page*



There are 4 user roles in Frappe Learning:


| Role                | Permissions                                                    | Best For                             |
| ------------------- | -------------------------------------------------------------- | ------------------------------------ |
| **LMS Student**     | Can browse courses, enroll in batches, and view content.       | All students.                        |
| **Course Creator**  | Can create, edit, and manage courses, chapters, and lessons.   | Course authors and teachers.         |
| **Batch Evaluator** | Can create batches/live classes and grade student assignments. | Teaching assistants and instructors. |
| **Moderator**       | Full access to all content, users, and system-wide settings.   | System Administrators.               |


To manage roles, admins can navigate to the **Profile** (`Settings` > `My Profile`) page of the member in the portal or the `User`DocType in the Desk.

:::caution
**Assign roles carefully. Moderators have full permission to create, edit, and delete anything in the system. Course Creators can upload SCORM files, which may execute code on the system, so only grant this role to trusted users.**
:::




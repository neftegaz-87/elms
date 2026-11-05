---
title: "Add a Chapter\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t"
space: "Learning"
url: "https://docs.frappe.io/learning/add-a-chapter"
updated: "2026-05-12"
---

**A chapter** forms the second layer in the hierarchy. It is used to group lessons that belong to the same topic. You can upload [SCORM](https://scorm.com/scorm-explained/one-minute-scorm-overview/) (Sharable Content Object Reference Model) as chapters in Frappe Learning if you are migrating content from other LMS platforms.

---

## Types of Chapters

In Frappe Learning, you can create two types of chapters:

- **Chapter with Lesson content**
- **SCORM Chapters**

---

### Chapter with Lesson Content

This is the standard chapter used to group individual lessons.

1. Inside your Course, click the `+ Add` button on the right side of the screen.

![](https://docs.frappe.io/files/Screenshot%202026-02-23%20at%2011.08.53%E2%80%AFAM.png)
*Add Chapter Modal *

2. Enter the `Title` for your chapter.
3. Click `Create` to save. You can now start adding lessons to this chapter.

---

### SCORM Chapter

:::caution
SCORM packages typically include HTML and JavaScript that run with the user's session, which introduces inherent security risks from scripted content. This can't be fully mitigated for the Course Creator role, as session access is required for SCORM to function.
:::



Use this option if you have an existing SCORM Chapter you wish to add.

1. Click the `+ Add` button.
2. Toggle the `SCORM Package` switch.
3. Enter your `Title` and upload your **SCORM ZIP file**.

![](https://docs.frappe.io/files/Screenshot%202026-02-23%20at%2011.14.44%E2%80%AFAM.png)
*Uploading SCORM Chapter *

4. Click `Create` and visit your chapter to see it.

![](https://docs.frappe.io/files/Screenshot%202026-02-23%20at%2011.14.26%E2%80%AFAM.png)
*SCORM Chapter View *

:::note
In SCORM Chapters, you cannot add individual lessons; the uploaded package serves as the entire content for that chapter.
:::




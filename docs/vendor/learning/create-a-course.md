---
title: "Create a Course\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t"
space: "Learning"
url: "https://docs.frappe.io/learning/create-a-course"
updated: "2026-04-08"
---

A **course** is the primary entity of the Learning app. 

You can make your courses in 2 ways:

1. Using the Learning Portal.
2. Importing them from a spreadsheet (Data Import)
3. Importing from ZIP (not a SCORM Package)

---

### Using the Learning Portal

1. Go to `Courses` on the sidebar, click the `+ Create` button, and select `New Course` from the menu.

![](https://docs.frappe.io/files/Screenshot%202026-02-23%20at%209.37.40%E2%80%AFAM.png)
*Step 1: Courses -> New Course -> New Course*

2. Fill in the basic details (Title, Short Introduction, etc.).

![](https://docs.frappe.io/files/Screenshot%202026-02-23%20at%2010.11.38%E2%80%AFAM.png)
*Course Creation Modal*

3. Click the `Create` button. You will be redirected to the `Course Settings` page, where you can fill out the [remaining details](#course-fields-reference) like metadata, images, and pricing.

---

### Importing from a Spreadsheet

Use this method to upload multiple courses at once. Note that this imports course metadata (Title, Description, etc.) but **cannot** import course content like Chapters or Lessons.

1. Go to `Courses` on the sidebar, click `+ Create`, and select `Import Course`.

![](https://docs.frappe.io/files/Screenshot%202026-02-23%20at%209.37.40%E2%80%AFAM.png)
*Step 1: Courses -> New Course -> Import Course*

2. Download Template:

- **All Fields:** To fill in every available detail.
- **Mandatory:** To get only the required fields.
- **Custom:** To select specific fields.

:::note
In custom templates, fields with Red Text are mandatory.
:::



![](https://docs.frappe.io/files/Screenshot%202026-02-23%20at%209.47.25%E2%80%AFAM.png)
*Download CSV Template options*

![](https://docs.frappe.io/files/Screenshot%202026-02-23%20at%209.48.09%E2%80%AFAM.png)
*Custom Template Download Modal*

3. Fill in your data in the spreadsheet. Leave the **ID** column empty; the system will auto-generate these.
4. Upload your Excel/CSV file. Or click the Google Sheet option and paste your URL. Make sure to copy the URL from your browser address bar. *The Google Sheet Link must end with a **gid=** parameter*.

![](https://docs.frappe.io/files/Screenshot%202026-02-23%20at%209.46.07%E2%80%AFAM.png)
*Importing from Google Sheet*

5. Map your columns if the headers don't match exactly.

![](https://docs.frappe.io/files/Screenshot%202026-02-23%20at%209.53.01%E2%80%AFAM.png)
*Map your columns*

6. Review your data and if everything is okay, click the `Import` button.

![](https://docs.frappe.io/files/Screenshot%202026-02-23%20at%2010.05.58%E2%80%AFAM.png)
*Review and Import*

7. Now scroll down to see which rows succeeded and review any errors for failed rows.

![](https://docs.frappe.io/files/Screenshot%202026-02-23%20at%2012.03.25%E2%80%AFPM.png)
*View Import Logs*

:::caution
Note that mandatory fields are compulsory and the import would fail without them (except for ID fields).
:::



---

## Course Fields Reference


| Field                        | Description                                                                                                                                                                          | Mandatory |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------- |
| **Title**                    | Name of the course displayed on the course page and listings.                                                                                                                        | ✅         |
| **Short Introduction**       | Brief summary shown in course cards and search results.                                                                                                                              | ✅         |
| **Course Description**       | Detailed explanation of course content, objectives, and outcomes.                                                                                                                    | ✅         |
| **Instructors**              | Email IDs of instructors authorized to manage and teach the course.                                                                                                                  | ✅         |
| **Category**                 | Grouping category (e.g., Programming, Design) used for filtering.                                                                                                                    | ❌         |
| **Tags**                     | Keywords indicating difficulty or prerequisites to help users decide if it's right for them.                                                                                         | ❌         |
| **Course Image**             | Thumbnail image representing the course visually.                                                                                                                                    | ❌         |
| **Color**                    | Background color of the course card; fallback if no image is uploaded.                                                                                                               | ✅         |
| **Published**                | Toggle to make the course visible on the website to users. A course will appear on the website to the users only when it is published. This setting is only visible to Moderators.   | ❌         |
| **Published On**             | The date shown to learners indicating when the course went live.                                                                                                                     | ❌         |
| **Upcoming**                 | If a course is about to become available to users soon but not yet, mark it as Upcoming. Note that even for an upcoming course to be visible on the website, it should be published. | ❌         |
| **Featured**                 | Highlights the course in designated "Featured" sections of the portal.                                                                                                               | ❌         |
| **Disable Self Enrollment**  | Enable this if you don't want users to enroll themselves into the course directly but instead want the Administrator to enroll them.                                                 | ❌         |
| **Preview Video**            | Introductory video or teaser accessible before a student enrolls.                                                                                                                    | ❌         |
| **Related Courses**          | Linked courses shown as recommendations on the course page.                                                                                                                          | ❌         |
| **Paid Course**              | If enabled, students must complete payment to access the course content.                                                                                                             | ❌         |
| **Paid Certification**       | Requires an additional fee to be paid before the certificate is issued.                                                                                                              | ❌         |
| **Amount**                   | The cost of the course (only applicable if Paid Course or Paid Certification is enabled).                                                                                            | ✅*        |
| **Currency**                 | The currency in which the course price is listed (only applicable if Paid Course or Paid Certification is enabled).                                                                  | ✅*        |
| **Evaluator**                | Evaluators for course certification (only applicable if Paid Certification is enabled).                                                                                              | ✅*        |
| **Time Zone**                | Time Zone for Evaluation Schedule (only applicable if Paid Certification is enabled).                                                                                                | ✅*        |
| **Completion Certification** | Issues a certificate to the student automatically upon finishing the course.                                                                                                         | ❌         |
| **Meta Description**         | SEO-friendly description used by search engines.                                                                                                                                     | ❌         |
| **Meta Keywords**            | SEO-friendly keywords used by search engines.                                                                                                                                        | ❌         |


*Mandatory only if the related Paid/Certification features are enabled.
---
title: "Assignment Rule"
space: "CRM"
url: "https://docs.frappe.io/crm/assignment-rule"
updated: "2026-09-30"
---

Assignment Rules automate the process of assigning leads and deals to specific agents based on predefined conditions. This streamlines your workflow and ensures leads and deals are directed to the most qualified agents for faster resolution and improved customer experience.

## **Creating an Assignment Rule**

1. Go to **Settings > Assignment Rules** and click on **+New**.
  ![](/files/image253100.png)
2. **Define the Rule:** Fill in the following mandatory fields:
  - **Name:** A label to identify the rule
  - **Description:** Describe in short what the rule does
  - **Apply for:** Select for which doctype(Lead or Deal) the rule will apply
  - **Assignment condition:** Define the condition using the conditions builder for the assignment rule
    ![](/files/image7712f7.png)
  - **Users:** Choose the user(s) to whom Lead or Deal meeting the condition will be assigned.

## **Lead or Deal Routing**

Assignment Rules offer two rules for assigning Lead or Deal:

1. **Auto-rotate:** This method distributes Lead or Deal evenly among the selected users. Each user receives one assignment at a time, and the cycle repeats once all users have been assigned.
2. **Assign by workload:** This method assigns Lead or Deal to the user with the least workload, ensuring a fair distribution and preventing any single user from being overloaded.

## **Additional Fields**

**Unassignment condition:** Define a condition using the conditions builder for the unassignment rule, complex nested conditions are also supported. This will be used to unassign a Lead or Deal based on the condition specified

**Assignment Schedule:** Select the days you want the assignment rule to be active

---

By effectively utilizing Assignment Rules, you can significantly improve the efficiency and organization of your lead and deal management process.
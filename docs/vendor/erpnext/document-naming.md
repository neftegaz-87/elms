---
title: "Document Naming Rule"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/document-naming"
updated: "2026-03-04"
---

In ERPNext, managing naming conventions systematically helps maintain consistency and traceability across your records. The Document Naming Rule feature allows you to set up dynamic naming based on conditions, offering more flexibility than the standard Document Naming Settings (Series).

✨ Key Differences from Traditional Naming Settings
While Document Naming Settings apply a prefix or pattern globally to a doctype, Document Naming Rule introduces conditional logic to apply naming series based on specific field values within the document.

🛠️ How to Set Up a Document Naming Rule
Follow the steps below to configure a Document Naming Rule:

**Steps:**

1. Select the Document Type
Choose the Doctype (e.g., Sales Invoice, Customer, etc.) where the rule will apply.


2. Set Priority
Assign a Priority number to the rule.

🔹 Higher priority rules (e.g., 10) are applied before lower ones (e.g., 5).
🔹 If multiple rules match, the one with the highest priority is used.

![Selsct a DocType](/files/Screenshot%202025-06-16%20at%205.19.58%E2%80%AFPM.png)

3. Add Rule Conditions
➕ You can add multiple conditions per rule. The rule is applied only when all conditions are satisfied.

🔍 Example Use Case
Scenario: You want to name Customers based on their location.

If the customer's Country is India, the naming format should be:
CUST-INDIA-00001, CUST-INDIA-00002, ...

This can be achieved using two Document Naming Rules:

Rule 1: Prefix = CUST-INDIA-, Condition = Country = India

Rule 2: Prefix = CUST-USA-, Condition = Country = USA

If the Country is USA, the format should be:
CUST-USA-00001, CUST-USA-00002, ...

4. Define the Prefix
Enter the desired prefix in the Prefix field under the Naming section.
Example: PSI/


5. Set the Serial Number Start
Specify the starting serial number in the field next to the prefix.
Example: 5 → The first document will be named PSI/00005

![](/files/Screenshot%202025-06-19%20at%203.44.10%E2%80%AFPM.png)

Here is an Example:


✅ Benefits
Automates naming based on document fields

Reduces manual selection and human error

Supports multiple naming patterns within the same Doctype

Useful for companies with multi-branch, multi-country, or multi-category document types

📝 Notes
Always ensure the conditions are specific enough to avoid conflicts between rules.

If no rule matches, the system will fall back to the default Naming Series (if configured).
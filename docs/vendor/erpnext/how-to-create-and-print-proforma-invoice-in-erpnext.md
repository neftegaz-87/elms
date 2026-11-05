---
title: "How to create and print proforma invoice in ERPNext"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/how-to-create-and-print-proforma-invoice-in-erpnext"
updated: "2026-07-02"
---

ERPNext does not have a dedicated "Proforma Invoice" document. To print one, you can simulate it by opening a **Quotation** or **Sales Order**, changing the document's Print Heading to "Proforma Invoice", and printing the document.

Follow these exact steps to print a proforma invoice for a customer:

**1. Create and Open the Document**

- Navigate to the Quotation or Sales Order you wish to send.
- Open the specific document record you want to print.

**2. Update the Print Heading**

- Scroll down to the Printing Settings section in the Quotation or Sales Order.
- In the Print Heading field, click the dropdown and select Create a new Print Heading.
- Type Proforma Invoice as the new heading name and save.
- Select this newly created Proforma Invoice heading from the dropdown and save your document.

**3. Print or Save as PDF**

- Click the Menu button (three dots) or the Print icon at the top left of the screen.
- Ensure you have the proper Letterhead selected if you need your company logo and contact details.
- Click PDF to download it to your computer, or click Print to send it directly to your hardware.

---

**Additional Customization Resources**

- **[ERPNext Print Designer Tutorial (Video Guide)](https://www.youtube.com/watch?v=-wH9jAUP4CE)**
- **[Frappe Customize Print Format Guide (Official Documentation)](https://docs.frappe.io/erpnext/records-print-format)**
---
title: "Procurement Cycle Overview"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/procurement-cycle-overview"
updated: "2026-09-29"
---

For a beginner-level understanding of the procurement cycle in ERPNext, the process has a total of 7 stages:

1. Material Request
2. Request for Quotation
3. Supplier Quotation
4. Purchase Order
5. Purchase Receipt
6. Purchase Invoice
7. Payment Entry

In a standard purchase cycle, you first raise a **Material Request** for the items to be purchased.

Once a Material Request is raised, you may want multiple suppliers to bid for the same items. In this case, you create a **Request for Quotation** (RFQ) and send it to the suppliers.

Suppliers respond to the RFQ with their rates for the required quantities. Their rates can be entered by users within ERPNext, or submitted by suppliers through the web portal, and are recorded as a **Supplier Quotation**. You can compare the quotations received from different suppliers using the Supplier Quotation Comparison report.

After selecting the best quote, you create a **Purchase Order** against it. Once the Purchase Order is submitted, you can create a **Purchase Receipt** when the goods are received, and a **Purchase Invoice** for billing, depending on your organization's process. Finally, you record the payment to the supplier with a **Payment Entry**.
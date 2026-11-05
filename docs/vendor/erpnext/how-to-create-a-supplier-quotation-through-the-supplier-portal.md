---
title: "Create Supplier Quotation through Supplier Portal"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/how-to-create-a-supplier-quotation-through-the-supplier-portal"
updated: "2026-09-27"
---

In ERPNext, Supplier Quotations can either be created manually or by the Supplier through the Supplier Portal. Suppliers can submit their quotations on the portal once they have logged in.

## 1. Prerequisites

- The Supplier must be a registered **Website User** with the **Supplier** role.
- The Supplier user's [Contact](/erpnext/contact) must be linked to the [Supplier](/erpnext/supplier), and the **User Id** must be set in the Contact.
- There should be a submitted [Request for Quotation](/erpnext/request-for-quotation) (RFQ) with the Supplier added to it.

When you submit a Request for Quotation with **Send Email** enabled for a Supplier, ERPNext automatically creates the Website User with the Supplier role for the Supplier's Contact, if it does not already exist.

![Supplier user with the Supplier role](/files/sq-portal-user-roles.webp)

![Supplier Contact with User Id](/files/sq-portal-contact-user.webp)

![Supplier Contact linked to the Supplier](/files/sq-portal-contact-links.webp)

## 2. How the Supplier Creates a Quotation

1. Create and submit a Request for Quotation for the Supplier. In this example, a Request for Quotation is created for "Apex Devices".

![Submitted Request for Quotation](/files/rfq3-submitted.webp)

2. The Supplier logs into the Supplier Portal using their login credentials. In the **Request for Quotations** list, the Supplier can view the Requests for Quotation sent to them.

![Request for Quotations on the Supplier Portal](/files/sq-portal-rfq-list.webp)

3. The Supplier opens the Request for Quotation, enters the **Rate** for each Item, adds any **Notes** (like validity, delivery and payment terms) and clicks on **Make Quotation**.

![Supplier entering rates on the portal](/files/sq-portal-rfq-rates.webp)

4. On clicking **Make Quotation**, a Supplier Quotation is automatically created in **Draft** state against this Request for Quotation. The Supplier can view it on the portal.

![Supplier Quotation created from the portal](/files/sq-portal-quotation-view.webp)

In ERPNext, the new Supplier Quotation is linked to the Request for Quotation. Click on **Supplier Quotation** at the top of the Request for Quotation to view it.

![Supplier Quotation linked to the Request for Quotation](/files/sq-portal-rfq-linked-sq.webp)

5. Review the Supplier Quotation and submit it. The Supplier can see their quotations and their status in the **Supplier Quotation** list on the portal.

![Draft Supplier Quotation](/files/sq-portal-draft-sq.webp)

![Supplier Quotation list on the portal](/files/sq-portal-quotation-list.webp)

## 3. Related Topics

- [Request for Quotation](/erpnext/request-for-quotation)
- [Supplier Quotation](/erpnext/supplier-quotation)
- [Supplier](/erpnext/supplier)
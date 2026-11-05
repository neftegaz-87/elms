---
title: "Frappe CRM <> WhatsApp"
space: "CRM"
url: "https://docs.frappe.io/crm/whatsapp"
updated: "2026-09-29"
---

WhatsApp integration allows you to send and receive WhatsApp messages from within the lead and deal pages in Frappe CRM. This streamlines communication and keeps all interaction history centralised for better customer relationship management.

![wiki-hero2](https://frappe.io/files/CRMWhatsApp.png)

A dedicated WhatsApp tab is available on both Lead and Deal pages, providing a real-time chat window for efficient communication.

- **Lead:** The mobile number field of a Lead is used to initiate and receive WhatsApp messages.
- **Deal:** The primary contact number associated with a Deal is used for WhatsApp communication.

## Installation

WhatsApp integration requires a separate app called "Frappe WhatsApp" developed by [Shridhar](https://github.com/shridarpatil/frappe_whatsapp/commits?author=shridarpatil).

- **Frappe Cloud Marketplace:** The app is available on the Frappe Cloud marketplace for easy installation.
  ![](/files/kB9ij9C.png)
- **Manual Installation:** Clone the app's repository from Github: [[https://github.com/shridarpatil/frappe_whatsapp](https://github.com/shridarpatil/frappe_whatsapp)]

## Configuration Steps

To enable WhatsApp integration in Frappe CRM, follow these steps:

1. **Obtain WhatsApp Business Credentials:** Refer to the official WhatsApp guide for creating a WhatsApp Business account and acquiring the necessary credentials [WhatsApp Business Account Creation Guide](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started).
  ![](/files/Bq2cxlF.png)
2. **Configure WhatsApp Settings:**
  ![](/files/aN42xJe.png)
   Click the dropdown menu on the top left logo and select "Settings."
   Locate the **WhatsApp Settings**.
   Enter the credentials obtained in step 1.
   Enable the WhatsApp integration.
3. **Set up the Webhook:**
  ![](/files/RyzN5w3.png)
    A webhook URL is required to establish communication between Frappe CRM and WhatsApp Business. Use the following URL format, replacing `` with your actual Frappe CRM site name and including the **Webhook Verify Token** you created in the **WhatsApp Settings** in **Verify token** field

  ![](/files/YWmf85N.png)
4. **Subscribe to webhook fields**:
  Subscribe all webhook fields (recommended - whatsapp docs) but atleast subscribe to `messages` & `message_template_status_update`

  ![](/files/Screenshot%202025-03-05%20at%202.18.24%E2%80%AFPM.png)

## Creating WhatsApp Templates

To ensure compliance and streamline communication, Frappe CRM utilizes WhatsApp templates. These pre-approved messages can be created and managed within the system.

![](/files/vWv1LiQ.png)

![](/files/mNauYNf.png)

1. Navigate to the **WhatsApp Templates** DocType.
2. Click on **Add WhatsApp Template**.
3. Fill in the required details for your template message.
4. Save the template.

With these configurations in place, you're ready to leverage WhatsApp Business for efficient communication with your leads and deal contacts directly within Frappe CRM.

> **Important Note:** Due to WhatsApp Business limitations, you can only initiate communication by sending a pre-approved WhatsApp template. You can only send regular messages after receiving a reply from the customer.
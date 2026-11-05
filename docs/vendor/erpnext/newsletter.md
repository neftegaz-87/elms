---
title: "Newsletter | ERPNext Documentation"
description: "Learn how to create, test, schedule, and send Newsletters to subscribed Email Groups in ERPNext."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/newsletter"
updated: "2026-07-23"
---

**Newsletter is an email which is sent to a specific group of subscribers periodically.**

In the context of CRM, its is an informational and product-focused email that is sent to existing and potential customers with an intention of softly pushing the subscriber to do required actions.

Newsletter can also be used to share information to employees, investors etc.

You need to create [Email Groups](/erpnext/email_group) before sending the newsletters.

To access the Newsletter list, go to:

> Home > Settings > Email > Newsletter

## How to Create a Newsletter

- Go to the Newsletter list and select New.
- Select the Email Group in RECIPIENT table.
- Enter 'Subject'.
- Enter 'Message'.
- 'Publish' the newsletter to make it available on the web.
- Tick 'Send Unsubscribe Link' if you would like to include unsubscribe link in the email.
- 'Send Web View Link' will include a link in the email to open the newsletter on the web. This option is only visible when the newsletter is published.

![Newsletter](/files/newsletter-doc.png)

Below is the screenshot of the email received with link to unsubscribe and a link to open the email on the web.

![Newsletter With Unsubscribe Link](/files/newsletter-doc-web-link.png)

## Features

### Create Subscriber Groups

You can manage subscribers by grouping them into different [Email Groups](/erpnext/email_group).

You can select multiple email groups in the 'RECIPIENT' tables in the newsletter.

### Schedule Send

You can choose to send your newsletter at any future datetime by specifying time in hourly steps.

![Scheduled Newsletter](/files/scheduled-newsletter.png)

### Test Newsletter Before Sending to Subscribers

Once the newsletter is ready you can provide a 'Test Email Address' and select 'Test'.

You can review the newsletter received in the test email, verify it and then send it to all subscribers by clicking on 'Send'.

![Newsletter Test](/files/newsletter-test.png)
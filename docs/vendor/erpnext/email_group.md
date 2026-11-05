---
title: "Email Group | ERPNext Documentation"
description: "Learn how to create and manage Email Groups and subscribers for ERPNext newsletters and campaigns."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/email_group"
updated: "2026-07-23"
---

**An Email Group is a list of subscriber email IDs to which you send newsletters.**

You can manage subscribers by grouping them into different groups.

You can group existing and potential customers into different groups based on their territory or products they are interested in. You can group the email ID of all employees so that you can share information with them.

To access the Email Group list, go to:

> Home > Settings > Email > Email Group

## How to Create an Email Group

- Go to the Email Group list and select New.
- Enter 'Title'.
- select 'Save'
- select Action > Add Subscribers.
- Enter Email Addresses.
- select 'Add'

## Features

### Import Email IDs from Transactions

You can import email IDs from existing transactions.

select Action > Import Subscribers and select a transaction like Lead. select Import and all the email IDs mentioned in the email IDs will be imported.

### Email Templates

You can specify the confirmation email and welcome email template for the email group. A confirmation email will be sent to confirm a person's subscription to your newsletter. The welcome email is sent when the person confirms their subscription to your email newsletter.

**Confirmation Email Template:** This email template is used to replace the default template sent for newsletter subscription. The confirmation email generated via this template is sent when someone subscribes to the Email Group Website.  
**Welcome Email Template:** Whenever a subscriber is added to an email group after confirmation, the email template set here will be sent to them.

![Email Group Templates](/files/email-group.png)
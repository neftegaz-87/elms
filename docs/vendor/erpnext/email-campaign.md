---
title: "Email Campaign | ERPNext Documentation"
description: "Learn how to create an Email Campaign in ERPNext using email templates, schedules, and recipient records."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/email-campaign"
updated: "2026-07-23"
---

**An Email Campaign is a coordinated set of emails sent to leads or contacts according to a particular schedule.**

Email Campaigns are still one of the most effective ways to reach your Customers, Contacts or Leads and keep them engaged. For example, you could set up Email Campaigns for introducing your product to the customers, with every email revealing an interesting feature of your product.

To create an Email Campaign, go to:

> Home > CRM > Campaign > Email Campaign

## Prerequisites

Before creating and using Email Campaign, these need to be created first:

- [Campaign](/erpnext/campaign)
- [Lead](/erpnext/lead) or [Contact](/erpnext/contact) or [Email Group](/erpnext/email_group)

## How to Create an Email Campaign

- Go to the Email Campaign list, select New.
- Select the [Campaign](/erpnext/campaign) for which you want to set up an Email Campaign.
- Set the 'Start Date' for the Email Campaign.
- In 'Email Campaign For', select whether you want to set up Email Campaign for a Lead or a Contact or for an Email Group to send to multiple email contacts.
- In 'Recipient', select the respective Lead or Contact or Email Group for whom you want to start the Email Campaign.
- In 'Sender', select the user of the system who should be the sender of the emails.
- Save[Email Campaign](/files/email-campaign.png)

he above Email Campaign is for the following Campaign:

[Campaign Schedule](/files/campaign-email-schedule.png)

*Note**: The **Send After (days)** field in Campaign specifies the day on which email is to be sent relative to the **Start Date** of **Email Campaign**. Notice the 'End Date' in the above Email Campaign. It is '26-07-2019', which is 4 days after the 'Start Date', '22-07-2029', as the Campaign Schedule ends on day 4.

### Create multiple Email Campaigns for a Campaign

You can also create new Email Campaigns for different Leads or Contacts for the same Campaign though the Campaign Dashboard.

- Go to the Campaign for which you want to create Email Campaigns.
- select + in front of Email Campaigns to create a new Email Campaign for the Campaign.[Email Campaigns from Dashboard](/files/campaign-dashboard.png)

## Features

### Linked Communication

When emails are sent to the respective leads or contacts, Communication is linked to the Email Campaign document. You can view all the emails sent in your document.

![Linked Communication](/files/email-campaign-linked-comm.png)

### Unsubscribe from Email Campaign

If a lead or contact does not want to continue getting emails regarding the campaign, he or she can unsubscribe from the Email Campaign via the unsubscribe link sent with the email.

![Unsubscribe Link](/files/unsubscribe-link.png)

When the lead or contact unsubscribes, the status of the Email Campaign document changes to 'Unsubscribed'.

![Unsubscribed](/files/email-campaign-unsubscribed.png)

### Use Lead or Contact fields in Email Template

 The Email Template has the context of the document you have specified in the 'Email Campaign For' field. If you want to display the fields from your Lead or Contact document in your Email Template you will have to use doc.fieldname for the same.  
 For example, if 'Email Campaign For' is 'Contact', you can mention the 'first name' of your Contact as doc.first_name in the Email Template as shown below:

![Email Template Document](/files/email-template-doc.png)

Then the emails sent would look like this:

![Email Campaign Doc Data](/files/email-campaign-doc-data.png)

### Status indication

Status indicates the state of the Email Campaign, the various Statuses are:

- **Scheduled**: When the Email Campaign has not yet started but scheduled on a future 'Start Date'.
- **In Progress**: The campaign would be marked as 'In Progress' between 'Start Date' and 'End Date' of the campaign.
- **Completed**: After the 'End Date' of the campaign, the status will be changed to 'Completed'.
- **Unsubscribed**: When the Lead or Contact unsubscribes from the Campaign.

![Email Campaign Status](/files/email-campaign-status.png)

## Related Topics

- [Campaign](/erpnext/campaign)
- [Lead](/erpnext/lead)
- [Contact](/erpnext/contact)

Next: [Newsletter](/erpnext/newsletter)
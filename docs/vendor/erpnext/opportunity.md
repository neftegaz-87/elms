---
title: "Opportunity | ERPNext Documentation"
description: "Learn how to create, track, quote, and close sales Opportunities in ERPNext CRM."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/opportunity"
updated: "2026-07-23"
---

**Opportunity is a qualified lead.**

When you get a hint that lead is looking for a product/service that you offer, you can convert that lead into an opportunity. You can also create an opportunity against an existing customer. Multiple Opportunities can be collected against a lead or a customer.

To access the Opportunity list, go to:

> Home > CRM > Sales Pipeline > Opportunity

## How to Create an Opportunity

- Go to the Opportunity list and select 'Add Opportunity'.
- In 'Opportunity From', select Lead if opportunity is from a lead.[Creating New Opportunity](/files/creating-opportunity.gif)
- You can also go to a Lead with 'Open' status and select “Opportunity” under **Create** dropdown as shown below.

[Create Opportunity From Lead](/files/lead-to-opportunity.png)

- In 'Opportunity From', select Customer if opportunity is from a customer.
- Select Opportunity Type. This indicates the broad category of opportunity like Sales, Support, Maintenance etc.
- You can add more details like Opportunity Amount, Probability (of conversion), Currency in 'SALES' section.
- You can capture the details of the products/services needed by clicking on 'With Items' checkbox and adding the item and quantity details in 'Items' section.

[Item Details in Opportunity](/files/item-details-in-opportunity.png)

- Enter the Source of the opportunity in the SOURCE section.

## Features

### Reminders to Follow Up on Opportunities

It is important to reach out to opportunities from time to time and build the relationship. You can set the 'Next Contact Date' and 'Next Contact By' fields and a calendar event will be added for the user chosen in 'Next Contact By' field and a notification is shown on the that Date.

### Auto-assign Opportunities to Sales Executives

> Introduced in Version 12

You can define [Assignment Rules](/erpnext/assignment-rule) to automatically assign the opportunities to sales executives.

![Opportunity Assignment](/files/opportunity-assignment-rule.png)

### Auto-close Opportunities

If you do not receive a response from an opportunity for a certain number of days, you may want that opportunity to be closed automatically.

You can set the number of days in [Selling Settings](/erpnext/selling-settings).

![Auto Close Opportunities](/files/auto-close-opportunities.png)

### Create a Quotation

You can create a [Quotation](/erpnext/quotation) from the **Make** dropdown. Relevant field values will be copied over.

![Create Quotation From Opportunity](/files/create-quotation-from-opportunity.png)

### Create a Supplier Quotation

You may need to get a quotation from your supplier against the customer requirement and based on that, prepare the quotation for your customer. With ERPNext, you can make a [Supplier Quotation](/erpnext/supplier-quotation) from the opportunity itself.

> Best Practice: Leads and Opportunities are often referred as your “Sales  
> Pipeline” this is what you need to track if you want to be able to predict how  
> much business you are going to get in the future. Its always a good idea to be  
> able to track what is coming in order to adjust your resources.

### 6 Capture the Reasons and Competitors for Lost Opportunities

When an opportunity is lost, you can capture the reasons, competitors and detail reason for losing. This will help you to analyse the trends over a long period of time and identify the insights needed for improvements at various areas in the organisation.

![Opportunity Lost Reason](/files/opportunity-lost-reason.png)

### Minutes to First Response

When you send the first reply(email) to an Opportunity, it calculates Mins to First Response and is displayed in a field.

A report is generated called 'Minutes to First Response for Opportunity'. Read [CRM Reports](/erpnext/crm_reports) for more details.

### Related Topics

- [Quotation](/erpnext/quotation.html)
- [Customer](/erpnext/customer)
- [Lead](/erpnext/lead)
- [Supplier Quotation](/erpnext/supplier-quotation)
- [Difference between Lead, Contact, and Customer](/erpnext/difference_between_lead_contact_and_customer)
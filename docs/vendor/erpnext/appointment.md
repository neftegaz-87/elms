---
title: "Appointment | ERPNext Documentation"
description: "Learn how to schedule and manage customer Appointments in ERPNext CRM."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/appointment"
updated: "2026-07-23"
---

**An appointment is a prearranged meeting between a Lead and an Employee of your Company.**

Appointment document type can be used to schedule and manage interaction with a [Lead](/erpnext/lead) or an [Opportunity](/erpnext/opportunity).

To access Appointment list, go to:

> Home > CRM > Sales Pipeline > Appointment

## Prerequisites

- [Appointment Booking Settings](/erpnext/appointment-booking-settings)
- [Holiday List](/hr/holiday-list)
- [Employee](/hr/employee)
- [Lead](/erpnext/lead)
- [Email](/erpnext/email-account)

## How to create an Appointment

- Go to Appointment list, select New
- Select scheduled time of the appointment
- Enter customer details
- In linked documents, if you have already created a Lead for the Customer you can set it here. Otherwise the system will automatically create a new lead with the customer details from previous step.
- Save.[New Appointment](/files/new-appointment.png)

### Creating appointments via website

Your Customers/Leads can create appointment using the webpage yoursitename.com/book_appointment.

First they need to set a date, time.

![Appointment Webform](/files/appointment-webform.png)

Then, add more details:

![Appointment Details](/files/appointment-details.png)

It'll match the customer email with leads in the system and if one is found, it is linked with the document.  
If no lead is found, the appointment is marked as "Unverified" and an email is sent to the customer to confirm their email

## Features

### Autoassign

Appointments are automatically assigned to employees as per the Agents list in [Appointment Booking Settings](/erpnext/appointment-booking-settings). The agent with the least number of assignments for the day of the appointment and who is free in the scheduled time is assigned to the appointment.

### Email confirmation

If there is no matching lead in your system, an email will be sent to the email address in the appointment to confirm if the email address is valid. Upon confirmation, a new Lead will also be created in the system along with the Appointment.
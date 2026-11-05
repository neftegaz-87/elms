---
title: "Booking Customer Deducted TDS in Payment Entry in ERPNext | ERPNext Documentation"
description: "Record customer-withheld tax and clear the related ERPNext invoice correctly."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/booking-customer-deducted-tds-in-payment-entry-in-erpnext"
updated: "2026-10-13"
---

## Issue

:::tip
For an Indian business, TDS is a synonum for Tax Withholding, which is a standard feature in ERPNext.
:::



  
A Customer deducted TDS (Tax Deducted at Source) while making payment, and deposited the same against the supplier’s PAN in the Income Tax portal.

As per the accounting process followed by the organization:

- TDS should be accounted for at the time of payment receipt
- The deducted amount should flow into the “TDS Receivable” account
- Customer outstanding should get fully reconciled

However, users are unable to identify the correct method to record the TDS deduction during Payment Entry in ERPNext.



# Resolution

In ERPNext, customer deducted TDS can be accounted for directly during Payment Entry using the **Deductions** section.



## Example:

Let's say there is a submitted Sales Invoice of 1,00,000/-

**Now the organization wants to record the deducted TDS in the Payment Entry**

### Steps to Record the Payment Entry

Create Payment Entry:

- Payment Type: Receive
- Party Type: Customer
- Party: Select Customer

### Enter Actual Amount Received

If the customer deducts TDS before payment:

Example:

- Invoice Amount: ₹1,00,000
- TDS Deducted by Customer: ₹10,000
- Amount Received in Bank: ₹90,000

**Enter the Paid Amount = ₹90,000**

![](/files/Screenshot 2026-05-29 at 10.50.47 AM.png)

### Add TDS in Deductions & Loss Table

![](/files/Screenshot 2026-05-29 at 10.51.31 AM.png)


| Account        | Amount  |
| -------------- | ------- |
| TDS Receivable | ₹10,000 |


This adjustment will automatically reconcile the invoice for the complete amount.



# Accounting Impact

The following accounting entries will be created after submitting the Payment Entry

![](/files/Screenshot 2026-05-29 at 10.51.59 AM.png)

# Result

After the Payment Entry Submitted:

- The Customer outstanding becomes zero
- TDS amount is tracked separately in “TDS Receivable”
- Bank receives only the net payment

---


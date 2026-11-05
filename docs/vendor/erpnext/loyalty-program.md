---
title: "Configure Customer Loyalty Programs | ERPNext Documentation"
description: "Set up ERPNext Loyalty Program tiers, earning and redemption factors, customer enrollment, point expiry, and Sales Invoice redemption."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/loyalty-program"
updated: "2026-07-25"
---

A Loyalty Program awards points from submitted sales and lets eligible Customers redeem those points on later [Sales Invoices](/erpnext/sales-invoice). Programs can use one tier or several tiers based on a Customer's cumulative eligible spend.

## Before you begin

Confirm:

- Eligible [Customers](/erpnext/customer), Customer Groups, and Territories.
- The Company currency and loyalty expense account.
- A Cost Center for redemption when required.
- A policy for earning, redemption value, expiry, returns, and tier upgrades.

Test point creation and accounting on the demo Company before enrolling Customers.

## Create a Loyalty Program

1. Open the Loyalty Program list and select **Add Loyalty Program**.
2. Enter the Program Name.
3. Select **Single Tier** or **Multiple Tier**.
4. Set From Date and To Date.
5. Restrict the Customer Group and Territory when required.
6. Enable **Auto Opt In** only when all eligible Customers should join automatically.
7. Add the tier rows.
8. Configure redemption and expiry.
9. Save.

![An ERPNext Loyalty Program with dates, eligibility, and enrollment settings.](https://novacompanies.m.frappe.cloud/files/loyalty-program-form.png)

## Configure tiers

![The Loyalty Program tier table with collection factors and thresholds.](https://novacompanies.m.frappe.cloud/files/loyalty-program-tiers.png)


| Field             | What it means                                           |
| ----------------- | ------------------------------------------------------- |
| Tier Name         | Label assigned when the Customer reaches the threshold  |
| Collection Factor | Eligible amount required to earn one point              |
| Minimum Amount    | Cumulative spend required for the tier                  |
| Auto Opt In       | Enrolls all Customers that match the program conditions |


Example: with a Collection Factor of $100, an eligible $1,000 invoice earns 10 points.

Minimum Amount is evaluated from cumulative eligible sales for the Customer, not only the current invoice.

## Configure redemption

Set:

- **Conversion Factor** for the monetary value of one point.
- **Expense Account** used for the loyalty benefit.
- **Cost Center** where required.
- **Expiry Duration** in days.

Keep earning and redemption factors distinct. A Customer might spend $100 to earn one point while each redeemed point is worth $1.

## Enroll a Customer

If Auto Opt In is disabled:

1. Open the Customer.
2. Select the Loyalty Program.
3. Save.

![A Customer assigned to the Nova Rewards Loyalty Program.](https://novacompanies.m.frappe.cloud/files/loyalty-program-customer.png)

## Earn points

Create and submit an eligible Sales Invoice. ERPNext creates a Loyalty Point Entry linked to the Customer and invoice.

Open **Loyalty Point Entry** to audit earned and redeemed points. Returns and cancellations can affect the available balance, so use the ledger rather than a manually maintained total.

## Redeem points

1. Create a Sales Invoice for the enrolled Customer.
2. Add the Items.
3. Open the Loyalty Points section.
4. Enable **Redeem Loyalty Points**.
5. Enter the number of points.
6. Confirm the Redemption Account and Cost Center.
7. Review the invoice total and submit.

The dot before an Item Code shows stock availability at a glance: green means in stock and red means out of stock.

## Troubleshooting


| Problem                              | What to check                                                                      |
| ------------------------------------ | ---------------------------------------------------------------------------------- |
| No points are earned                 | Confirm enrollment, program dates, eligibility, submitted invoice, and tier factor |
| Redeem Loyalty Points is unavailable | Confirm that the Customer has a program and available points                       |
| The tier is unexpected               | Review cumulative eligible spend and minimum thresholds                            |
| Points expired earlier than expected | Check Expiry Duration and the Loyalty Point Entry dates                            |
| Redemption accounting is incorrect   | Review the program's Expense Account and Cost Center                               |


## Frequently asked questions

### Can a program have several tiers?

Yes. Use Multiple Tier and add each threshold in ascending order.

### Are points awarded on draft invoices?

No. The earning workflow depends on submitted eligible invoices.

### Can every Customer be enrolled automatically?

Yes. Enable Auto Opt In and define the eligible Customer Group and Territory.

### Where can I audit a Customer's points?

Use Loyalty Point Entry and the Customer's linked records.

## Related topics

- [Customer](/erpnext/customer)
- [Sales Invoice](/erpnext/sales-invoice)
- [Sales Return](/erpnext/sales-return)
- [Applying a Discount](/erpnext/applying-discount)
- [Point of Sale](/erpnext/point-of-sale)
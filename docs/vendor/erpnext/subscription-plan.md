---
title: "Subscription Plan | ERPNext Documentation"
description: "Create an ERPNext Subscription Plan to define the item, price, billing interval, payment gateway, and accounting dimensions used for recurring invoices."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/subscription-plan"
updated: "2026-08-14"
---

A Subscription Plan defines what ERPNext bills on a recurring basis, how much it charges, and how often it charges it. You add one or more plans to a [Subscription](/erpnext/subscription), and ERPNext uses them when it creates recurring Sales Invoices or Purchase Invoices.



Use a separate plan for each distinct combination of item, price, currency, and billing frequency. For example, Nova Industries can use **Nova Device Care Monthly** for a USD 199 monthly warranty service and a separate yearly plan for customers who pay in advance.

![Subscription Plan for a monthly warranty service](https://novacompanies.m.frappe.cloud/files/sales-receivables-subscription-plan-subscription-plan-overview.png)

## Before you begin

Create the following records first:

- An [Item](/erpnext/item) for the product or service being billed. Use a non-stock service Item when no stock delivery is involved.
- An [Item Price](/erpnext/item-price) and [Price List](/erpnext/price-lists) if the plan will obtain its rate from a Price List.
- A [Payment Gateway Account](/erpnext/payment-gateway) if an external payment integration will collect the recurring charge.
- A [Cost Center](/erpnext/cost-center) or other accounting dimensions if subscription income or expense must be reported separately.

Accounts Users, Accounts Managers, and System Managers can create Subscription Plans when their role permissions have not been customized.

## Create a Subscription Plan

1. Go to **Accounting &gt; Subscriptions &gt; Subscription Plan**.
2. Select **Add Subscription Plan**.
3. Enter a unique **Plan Name**. Use a name that communicates the service and interval, such as `Nova Device Care Monthly`.
4. Select the **Currency** and the **Item** being billed.
5. Choose how ERPNext determines the subscription price and enter the corresponding rate or Price List.
6. Set the **Billing Interval** and **Billing Interval Count**.
7. Add payment and accounting details when required.
8. Save the plan.

Saving a plan does not create an invoice. Add the saved plan to a Subscription to begin the recurring billing workflow.

## Choose how the price is determined

The highlighted fields control the rate ERPNext uses when it generates an invoice from the Subscription.

![Subscription pricing method and cost fields](https://novacompanies.m.frappe.cloud/files/sales-receivables-subscription-plan-subscription-plan-pricing.png)


| Subscription Price Based On | How ERPNext calculates the rate                                                                                                                                                              | Use it when                                                                                                 |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **Fixed Rate**              | Uses the value entered in **Cost**.                                                                                                                                                          | The charge remains the same for every billing cycle.                                                        |
| **Based On Price List**     | Reads the Item rate from the selected Price List. The applicable customer or supplier context can affect the returned Item Price.                                                            | You maintain recurring rates through standard Item Prices.                                                  |
| **Monthly Rate**            | Treats **Cost** as the monthly rate and calculates the charge for the covered number of months. Proration can apply when enabled in [Subscription Settings](/erpnext/subscription-settings). | The billing period may span one or more months and you want the amount calculated from a monthly base rate. |


Changing a plan does not rewrite invoices that have already been generated. Review the next invoice after changing a rate, Price List, or billing interval.

## Set the billing frequency

The **Billing Interval** supplies the unit: Day, Week, Month, or Year. The **Billing Interval Count** tells ERPNext how many of those units make one billing cycle.

![Billing Interval and Billing Interval Count](https://novacompanies.m.frappe.cloud/files/sales-receivables-subscription-plan-subscription-plan-billing-interval.png)

Examples:


| Billing Interval | Count | Result                   |
| ---------------- | -----: | ------------------------ |
| Month            | 1     | Bills every month        |
| Month            | 3     | Bills every three months |
| Week             | 2     | Bills every two weeks    |
| Year             | 1     | Bills every year         |


The count must be at least 1. The Subscription's start date and invoice-generation settings determine the actual billing dates. Calendar-month alignment, invoice timing, trial periods, and renewal behavior belong on the Subscription rather than the plan.

## Important fields and what they mean


| Field                           | What it controls                                                                                                                                  |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Plan Name**                   | The unique name shown when you add the plan to a Subscription.                                                                                    |
| **Currency**                    | The currency used for the plan's rate and generated invoice line. Keep it consistent with the party and transaction currency.                     |
| **Item**                        | The product or service added to the generated invoice. ERPNext uses the Item's accounting defaults when it builds the invoice line.               |
| **Subscription Price Based On** | Selects the fixed-rate, Price List, or monthly-rate calculation.                                                                                  |
| **Cost**                        | Stores the fixed or monthly base rate. It appears only when the selected pricing method requires it.                                              |
| **Price List**                  | Supplies the Item Price when pricing is based on a Price List.                                                                                    |
| **Billing Interval**            | Defines whether the cycle is measured in days, weeks, months, or years.                                                                           |
| **Billing Interval Count**      | Defines how many intervals make one billing cycle.                                                                                                |
| **Product Price ID**            | Stores an external payment provider's price identifier when an integration requires it. Leave it blank for ordinary ERPNext invoicing.            |
| **Payment Gateway**             | Links the plan to a configured Payment Gateway Account for integrated collection workflows.                                                       |
| **Cost Center**                 | Assigns the generated invoice line to the selected Cost Center when the integration and Subscription flow carry the accounting dimension forward. |


## Use the plan in a Subscription

Open a new Subscription, select the Customer or Supplier, set the service dates, and add the plan in the **Subscription Plans** table. A customer Subscription generates [Sales Invoices](/erpnext/sales-invoice), while a supplier Subscription generates [Purchase Invoices](/erpnext/purchase-invoice).

One Subscription can contain multiple plans. This is useful when the same Customer receives a base service plus separately priced support, storage, or add-ons. Keep each charge as its own plan so rates and intervals remain understandable.

## Troubleshooting

### The generated invoice rate is zero

For **Based On Price List**, confirm that the selected Price List contains an active Item Price for the plan's Item, currency, quantity, party context, and invoice date. If no applicable price is found, ERPNext can return a zero plan rate.

### The plan bills at the wrong frequency

Check both **Billing Interval** and **Billing Interval Count**. A Month interval with a count of 3 means one invoice every three months, not three invoices each month. Then verify the Subscription's start date and invoice-generation settings.

### The plan cannot be saved

Confirm that the Plan Name is unique, all required fields are present, and Billing Interval Count is 1 or higher.

### The payment gateway does not collect payment

Linking a gateway on the plan does not complete the integration by itself. Verify the Payment Gateway Account, provider credentials, Product Price ID when required, and the Subscription payment workflow.

## Frequently asked questions

### Can I use one plan for several customers?

You can reuse a Subscription Plan. Add the same plan to multiple customer Subscriptions when the item, currency, pricing method, and billing interval are identical.

### Can one Subscription contain several plans?

You can add several plans. Each plan becomes a separate recurring invoice line. Use this for a base service with optional add-ons.

### Should I create separate monthly and yearly plans?

Usually, yes. Separate plans make the price and billing commitment explicit and reduce the chance of selecting the wrong interval.

### Does saving a plan create an invoice?

Saving the plan does not create an invoice. The plan is a reusable billing definition, and invoice generation begins only after it is added to an active Subscription.

## Related topics

- [Subscription](/erpnext/subscription)
- [Subscription Settings](/erpnext/subscription-settings)
- [Item](/erpnext/item)
- [Price Lists](/erpnext/price-lists)
- [Sales Invoice](/erpnext/sales-invoice)
- [Purchase Invoice](/erpnext/purchase-invoice)
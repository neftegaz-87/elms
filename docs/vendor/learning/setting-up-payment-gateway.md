---
title: "Setting Up Payment Gateway\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t"
space: "Learning"
url: "https://docs.frappe.io/learning/setting-up-payment-gateway"
updated: "2026-02-24"
---

Frappe Learning uses the [Payments app](https://frappecloud.com/marketplace/apps/payments) to handle payments. So if you want to accept payments from the system, make sure this app is installed on your site.

Once the payments app is installed, you need to setup the Payment Gateway of your choice.  
The Payment Gateways supported are:

1. Razorpay
2. Stripe
3. PayPal
4. Braintree
5. GoCardless
6. Mpesa
7. PayTM

Each of these payment gateways has a respective Settings DocType. You can search for the same in the desk view. For example: the settings for Razorpay can be done in Razorpay Settings DocType.

Once the payment gateway is set, open the Settings dialog from the portal. There go to the Payment Gateway section. There select the Payment Gateway you want. You can also set the **Default Currency** and other such details here.

![](/files/Screenshot%202025-02-07%20at%208.02.53%E2%80%AFPM.png)

Once the Payment Gateway is set, you can configure your courses and batches to accept payments.
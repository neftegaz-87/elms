---
title: "Customer Portal"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/customer-portal"
updated: "2026-09-27"
---

The Customer Portal gives your Customers easy access to their information in ERPNext.

Customers can log in to the portal to check the status of their Orders, Invoices and Shipments, and raise Issues and follow the conversation on them.

## 1. Giving Customers Access to the Portal

A Customer can access the portal using a **Website User** that is added to the Customer's **Portal Users** table.

### 1.1 Adding a Portal User to a Customer

1. Create a **Contact** for the Customer, linked to the Customer, and set a Website User with the **Customer** role as the Contact's **User Id**.
2. Open the Customer and go to the **Portal Users** tab.
3. Add the user in the **Customer Portal Users** table and **Save**.

![Portal Users tab in Customer](/files/cp3-customer-portal-users.webp)

:::note
The portal shows a Customer's Orders, Invoices and Shipments only to the users listed in the Customer's Portal Users table.
:::

### 1.2 Signup

If signup is enabled in **Website Settings** (the **Disable Signup** checkbox is unticked), Customers can create their own account using the **Sign up** option on the Login page.

![Sign Up page](/files/cp4-signup.webp)

After signing up, an email is sent to the Customer's email address with a link to set their password. You can then add the new user to the Customer's **Portal Users** table.

## 2. Portal Login

To log in to the portal, the Customer uses their email address and password on the Login page. They can also use **Login with Email Link** to receive a login link on their email address.

![Login page](/files/cp4-login.webp)

After logging in, the Customer lands on the portal home page. The menu on the left links to their Quotations, Orders, Invoices, Shipments, Issues, Addresses and more.

![Customer Portal home](/files/cp3-portal-home.webp)

## 3. Orders, Invoices and Shipping Status

Once an order is created, either from the Shopping Cart or within ERPNext, the Customer can view the order on the portal and keep an eye on its billing and delivery status. When invoices and payments against these orders are submitted, the Customer can see the updated status on the portal at a glance.

### 3.1 Orders

![Orders on the Customer Portal](/files/cp3-orders.webp)

Click on an order to view its details.

![Sales Order on the Customer Portal](/files/cp3-order-detail.webp)

### 3.2 Invoices

The Invoices list shows the status of each Sales Invoice, such as Overdue or Paid.

![Invoices on the Customer Portal](/files/cp3-invoices.webp)

#### Outstanding Sales Invoice

![Overdue Sales Invoice on the Customer Portal](/files/cp3-invoice-overdue.webp)

#### Paid Sales Invoice

![Paid Sales Invoice on the Customer Portal](/files/cp3-invoice-paid.webp)

## 4. Issues

The Customer Portal makes it easy for a Customer to raise concerns. A simple interface lets them report their concerns as Issues and view the complete conversation on them.

1. Go to **Issues** in the portal menu and click on **New**.
2. Enter the **Subject** and **Description** of the issue, and click on **Submit**.

![New Issue on the Customer Portal](/files/cp4-new-issue.webp)

3. The Issue is created in ERPNext and is listed in the Customer's **Issue** list.

![Issue list on the Customer Portal](/files/cp3-issue-list.webp)

4. Click on the Issue to view its details.

![Issue on the Customer Portal](/files/cp4-issue-open.webp)

5. The Customer can add a comment on the Issue from the **Comments** section, and see the complete conversation.

![Comments on an Issue](/files/cp4-issue-comment.webp)

## 5. Related Topics

1. [Customer](/erpnext/customer)
2. [Contact](/erpnext/contact)
3. [Sales Order](/erpnext/sales-order)
4. [Sales Invoice](/erpnext/sales-invoice)
5. [Issue](/erpnext/issue)
6. [Website Settings](/erpnext/website-settings)
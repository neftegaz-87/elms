---
title: "Restrict Sales Users to Their Customers and Transactions | ERPNext Documentation"
description: "Learn how to use ERPNext roles and User Permissions so sales users see only assigned Leads, Customers, and transactions linked to those Customers."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/salesperson-permissions"
updated: "2026-07-25"
---

Use [User Permissions](/erpnext/user-permissions) when a sales user should work only with named Leads, Customers, and the sales transactions connected to those Customers. A [Sales Person](/erpnext/sales-person) record is useful for targets, commissions, and the Sales Team table, but assigning a Sales Person does not by itself create record-level access restrictions.

This guide uses Avery Stone as a sales user. Avery can work with Northstar Retail, Summit Digital Stores, and two assigned Leads, but not the rest of the sales portfolio.

## Before you begin

- You need System Manager or equivalent permission to manage Users and User Permissions.
- The user must be a System User with the roles required for their work.
- Create the relevant [Customers](/erpnext/customer) and [Leads](/erpnext/lead) first.
- Decide whether access will be maintained customer by customer or through a grouping master such as [Territory](/erpnext/territory).

> **Roles and User Permissions do different jobs.** A role grants access to a document type. A User Permission limits which records of that type the user can access.

## 1. Give the user the required sales role

1. Open **User** and select the sales user.
2. Open **Roles &amp; Permissions**.
3. Enable **Sales User**.
4. Add another role only when the person needs the corresponding actions. For example, do not assign Sales Manager merely to make the workspace visible.
5. Save the User.

![Avery Stone User form with the Sales User role highlighted.](/files/01-sales-user-role.webp)

The Sales User role normally provides access to sales masters and transactions according to the configured [Role Permission Manager](/erpnext/permissions). User Permissions added in the following steps narrow that access.

## 2. Open User Permission

Go to **Users and Permissions &gt; User Permission**, then select **Add User Permission**.

![User Permission list with Add User Permission highlighted.](/files/02-open-user-permissions.webp)

You can also open the User and use **Permissions &gt; Set User Permissions**. Both routes create the same User Permission records.

## 3. Allow the Customers assigned to the sales user

Create one User Permission for each Customer in the user's portfolio:

1. In **User**, select the sales user.
2. Set **Allow** to **Customer**.
3. In **For Value**, select an allowed Customer.
4. Save the User Permission.
5. Repeat for each additional Customer.

![User Permission for Avery Stone allowing access to Northstar Retail, with User, Allow, and For Value highlighted.](/files/03-customer-user-permission.webp)

For example, Avery has separate permissions for Northstar Retail and Summit Digital Stores. ERPNext combines permissions for the same master, so Avery can access either Customer.

### Why this also restricts sales transactions

A Customer is linked from documents such as a [Quotation](/erpnext/quotation), [Sales Order](/erpnext/sales-order), [Delivery Note](/erpnext/delivery-note), and [Sales Invoice](/erpnext/sales-invoice). When the user's role applies User Permissions, the Customer restriction is carried into those linked documents.

This means you normally do not create separate User Permissions for every Sales Order or Sales Invoice. Maintain the Customer portfolio, and the restriction follows the Customer link.

## 4. Add Lead permissions separately

A Lead is not yet a Customer. A Customer permission therefore cannot decide which unconverted Leads the user may access.

Create a separate User Permission for each assigned Lead:

1. Select the same sales user.
2. Set **Allow** to **Lead**.
3. Select the permitted Lead in **For Value**.
4. Save and repeat for the user's other Leads.

When a Lead is converted, add the resulting Customer to the user's Customer permissions. Review the old Lead permission according to your retention policy.

## 5. Apply the restriction to linked document types

Keep **Apply To All Document Types** enabled when the Customer permission should restrict every supported document containing a Customer link.

![Apply To All Document Types highlighted on a Customer User Permission.](/files/04-apply-to-all-doctypes.webp)

Clear this option only when the permission must apply to one specific document type. After clearing it, select that document type in **Applicable For**. For example, limiting a Customer permission to Sales Order would not provide the same restriction across Quotations, Delivery Notes, and Sales Invoices.

## 6. Review the complete portfolio

Open the User Permission list and filter by the user. Confirm that every permitted Customer and every unconverted Lead appears once.

![User Permission list showing two Customers and two Leads allowed for Avery Stone.](/files/05-customer-and-lead-permissions.webp)

In this example, Avery can access:

- Northstar Retail and Summit Digital Stores;
- the sales transactions linked to those Customers; and
- Leads CRM-LEAD-2026-00001 and CRM-LEAD-2026-00002.

Avery should not receive a broad Customer, Customer Group, or Territory permission that includes the rest of the portfolio. A broader permission expands access rather than overriding the individual Customer permissions.

## 7. Verify access before handing over the account

Do not assume that a saved permission produces the intended result.

1. Open the User.
2. Select **Permissions &gt; View Permitted Documents**.
3. Check Customer, Lead, Quotation, Sales Order, Delivery Note, and Sales Invoice.
4. Confirm that permitted records appear and an unrelated Customer does not.
5. Test list views and the reports the user will actually use.

![Permissions menu with View Permitted Documents highlighted on the Avery Stone User form.](/files/06-view-permitted-documents.webp)

For a final security check, sign in with a non-administrator test user that has the same roles and permissions. System Manager and Administrator accounts can bypass restrictions and are not suitable for validating a salesperson's experience.

## How access is determined


| Configuration                 | What it controls                                                        |
| ----------------------------- | ----------------------------------------------------------------------- |
| Sales User role               | Which sales document types and actions are available                    |
| Customer User Permission      | Which Customers and Customer-linked transactions the user can access    |
| Lead User Permission          | Which specific unconverted Leads the user can access                    |
| Apply To All Document Types   | Whether the allowed value restricts all supported linked document types |
| Applicable For                | Limits one User Permission to a selected document type                  |
| Apply Strict User Permissions | Controls whether records with a blank restricted link remain visible    |


## When there are many Customers

Individual Customer permissions are precise and easy to audit, but they require maintenance when portfolios change. If Customers and Leads are cleanly divided by region, create a User Permission for the appropriate Territory instead. A parent Territory can also include descendants unless **Hide Descendants** is enabled.

Use a grouping master only when it matches the real access boundary. Do not use [Customer Group](/erpnext/customer-group) for access if the group exists mainly for pricing or reporting and contains Customers belonging to several salespeople.

## Records with a blank Customer or Territory

Review **Apply Strict User Permissions** in [System Settings](/erpnext/system-settings). When strict permissions are enabled, a record with a blank restricted link is hidden. When they are not enabled, records whose restricted link is blank may remain visible.

Before enabling this setting, review integrations and older data for missing Customer or Territory values. Test the effect on all teams because it is a system-level setting.

## Troubleshooting


| Problem                                             | What to check                                                                                                                      |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| The user can still see every Customer               | Check for a broader Customer, Customer Group, or Territory permission. Confirm the user's role has Apply User Permissions enabled. |
| The user cannot open any sales transactions         | Confirm the Sales User role grants Read access and that the transaction contains an allowed Customer.                              |
| The user can see unrelated records with blank links | Review missing Customer or Territory values and the Apply Strict User Permissions setting.                                         |
| Assigned Leads are missing                          | Create Lead User Permissions separately. Customer permissions do not cover unconverted Leads.                                      |
| A report shows more data than expected              | Test the report with the restricted user. Review custom or script reports to confirm they apply permission-aware queries.          |
| A manager cannot see a salesperson's portfolio      | Add the required broader permissions to the manager. A Sales Person hierarchy does not automatically replace User Permissions.     |


## Frequently asked questions

### Is linking a User to a Sales Person enough?

Sales Person assignment supports sales attribution, targets, and commission reporting. Use User Permissions for record-level restrictions.

### Must I add every Sales Order to User Permissions?

Allow the Customer and keep Apply To All Document Types enabled. Supported Customer-linked transactions inherit that restriction.

### Can one salesperson have several Customers and Leads?

Y

es. Create one User Permission for each allowed value, or use a suitable Territory when the portfolio follows that hierarchy.

### Can sales managers see all records?

Yes, if their roles and User Permissions grant the broader access. Test managers separately instead of assuming the Sales Person tree controls visibility.

## Related topics

- [User Permissions](/erpnext/user-permissions)
- [Role Based Permissions](/erpnext/permissions)
- [Adding Users](/erpnext/adding-users)
- [Sales Person](/erpnext/sales-person)
- [System Settings](/erpnext/system-settings)
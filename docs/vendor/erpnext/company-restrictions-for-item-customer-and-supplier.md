---
title: "Company Restrictions for Item, Customer and Supplier"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/company-restrictions-for-item-customer-and-supplier"
updated: "2026-09-09"
---

:::note
This feature is available only on v17 and above
:::



Company Restrictions limit an Item, a Customer, or a Supplier to a set of companies. A restricted record works only in the companies that you list. ERPNext blocks the record in every other company.

Use this in a multi-company site where a master record belongs to one company only. Examples are a product that only one company sells, or a supplier that only one company buys from.

## The fields

The **Company Restrictions** section of Item, Customer, and Supplier has two fields.


| Field                 | Type              | Description                               |
| --------------------- | ----------------- | ----------------------------------------- |
| Restrict to Companies | Check             | Turns the restriction on for this record. |
| Allowed Companies     | Table MultiSelect | The companies that can use this record.   |


**Allowed Companies** is required when **Restrict to Companies** is checked. If you clear the check box, ERPNext empties the list.

## Who can change the restriction

The section is on permission level 1. Only these roles can read and write the two fields.


| Document | Role                    |
| -------- | ----------------------- |
| Item     | Item Manager            |
| Customer | Sales Master Manager    |
| Supplier | Purchase Master Manager |


Other users do not see the section. If another user saves the record, ERPNext keeps the old restriction values.

## Restrict a record

1. Open the Item, the Customer, or the Supplier.
2. Go to the **Company Restrictions** section.
3. Check **Restrict to Companies**.
4. Add one or more companies to **Allowed Companies**.
5. Save the record.

The **Allowed Companies** field shows only the companies that you can access. If you have a User Permission on Company, you cannot add or remove a company that is outside that permission.

## What the restriction does

### Transactions

ERPNext checks the restriction when you save a document that has a Company field. The check reads every link to an Item, a Customer, or a Supplier in the document and in its child tables. If a linked record is restricted, and the company of the document is not in the allowed list, the save fails with this message:

> Item ITEM-0001 cannot be used with Company Wind Power LLC because of Company Restrictions

The check covers all transactions, such as Sales Order, Purchase Invoice, Stock Entry, and Material Request. It also covers masters that have a Company field, such as BOM and Pricing Rule.

### Party selection

When you select a restricted Customer or Supplier on a transaction, ERPNext raises the same error while it fetches the party details. You do not have to save the document to see the error.

### Link searches

The Item, Customer, and Supplier searches on sales and purchase transactions send the company of the document. These searches hide records that the company cannot use. Searches that do not send a company show all records. The save-time check still blocks the wrong record.

### List views and reports

List view filtering starts only when a user has a User Permission on Company. Such a user sees a restricted Item, Customer, or Supplier only when the allowed list contains one of the permitted companies. The user also cannot open a restricted record that is outside the permitted companies.

A user without a User Permission on Company sees all records in the list. The transaction check still applies to that user.

## Limits

- The check runs on save. A submitted document stays valid after you change the restriction. You can still cancel that document.
- An amended document runs the check again. The amendment fails if the restriction now blocks the company.
- The restriction does not disable the record. The record stays active in its allowed companies.

## Messages


| Message                                                                                    | Cause                                                                   | Action                                                                        |
| ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Allowed Companies is required when Restrict to Companies is checked                        | The check box is on and the list is empty.                              | Add at least one company, or clear the check box.                             |
| `<Doctype> <name>` cannot be used with Company `<company>` because of Company Restrictions | The document uses a restricted record in a company that is not allowed. | Remove the record from the document, or add the company to Allowed Companies. |
| You are not permitted to add or remove Company `<company>` in Allowed Companies            | Your User Permission on Company does not cover that company.            | Ask an administrator to change the list.                                      |
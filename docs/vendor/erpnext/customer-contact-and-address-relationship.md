---
title: "Customer, Contact and Address Relationship | ERPNext Documentation"
description: "Understand how ERPNext links Customers, Contacts, and Addresses, why they are separate, and how primary contact, billing, and shipping records are selected."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/customer-contact-and-address-relationship"
updated: "2026-07-25"
---

A [Customer](/erpnext/customer), [Contact](/erpnext/contact), and [Address](/erpnext/address) describe different parts of the same business relationship. The Customer is the party you sell to, a Contact is a person you communicate with, and an Address is a location used for billing, shipping, or another purpose.

Keeping these as separate linked records lets one Customer have several people and locations without creating duplicate customer accounts.

## How the three records fit together


| Record       | Represents                                                                                          | Example                        |
| ------------ | --------------------------------------------------------------------------------------------------- | ------------------------------ |
| **Customer** | The commercial party used for quotations, orders, invoices, payments, credit control, and reporting | Summit Digital Stores          |
| **Contact**  | A person you communicate with                                                                       | Morgan Lee, Purchasing Manager |
| **Address**  | A physical or mailing location                                                                      | Harbor Avenue billing office   |


The usual relationship looks like this:

> **Customer**  
> ↳ linked to one or more **Contacts**  
> ↳ linked to one or more **Addresses**

The Contact and Address are not stored inside the Customer. They are independent records connected through **Links**. This matters because the same Contact or Address can be linked to another supported party when the relationship is genuine.

## Why are they separate?

A company can remain the same Customer even when its people or locations change. Separating the records reflects that reality.

- **One Customer can have several Contacts.** A purchasing manager may receive quotations, while an accounts-payable contact receives invoices.
- **One Customer can have several Addresses.** The head office may be used for billing, while goods are delivered to a warehouse or retail branch.
- **People and locations can change independently.** You can replace a Contact or add a delivery location without creating another Customer and splitting the sales history.
- **Transactions can use the appropriate combination.** A Sales Order can use one Contact and shipping Address, while a later order for the same Customer uses another.

Create another Customer only when the party must be treated as a separate commercial or accounting relationship. Do not create a new Customer merely for a new employee, office, or delivery point.

## Example

Nova Electronics Trading sells to **Summit Digital Stores**. ERPNext can model the relationship as follows:

- **Customer:** Summit Digital Stores
- **Primary Contact:** Morgan Lee, Purchasing Manager
- **Other Contact:** Taylor Brooks, Accounts Payable
- **Preferred Billing Address:** Harbor Avenue office
- **Preferred Shipping Address:** Meridian Parkway warehouse

When a user creates a [Quotation](/erpnext/quotation) or [Sales Order](/erpnext/sales-order) for Summit Digital Stores, ERPNext can fetch Morgan Lee and the preferred Addresses. The user can still select Taylor Brooks or another linked Address when that transaction requires it.

## How primary records are selected

Primary settings tell ERPNext which linked record to use as the normal default. They do not prevent users from selecting another linked record.

### Primary Contact

Enable **Is Primary Contact** on the Contact that should normally be fetched for the linked Customer. If a Customer has several Contacts, use this for the person who usually receives sales communication.

A Contact also has primary email and primary phone selections. These answer a different question:

- **Is Primary Contact** chooses the preferred person for the linked party.
- **Primary email** and **primary phone** choose the preferred details within that person's Contact record.

### Preferred billing and shipping Addresses

An Address can be marked as the **Preferred Billing Address**, the **Preferred Shipping Address**, or both.

- The preferred billing Address is the normal location for invoices and billing communication.
- The preferred shipping Address is the normal delivery destination.

These may be different locations. For example, a Customer may pay invoices from its head office but receive goods at a warehouse.

### Selection on a transaction

When the Customer is selected on a supported sales transaction, ERPNext uses eligible linked records and their primary or preferred settings to provide defaults. A user can replace those defaults with another Contact or Address linked to the same Customer.

Set the primary flags explicitly when a Customer has multiple linked records. This avoids relying on whichever eligible record happens to be available.

Changing a primary Contact or preferred Address affects the defaults used on future documents. It does not rewrite the Contact, Address, or rendered address text already stored on submitted transactions.

## Common mistakes


| Mistake                                              | Better approach                                                                             |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Creating a new Customer for every branch             | Use linked Addresses unless each branch is a separate commercial or accounting party.       |
| Putting a person's details in the Customer name      | Create a Contact and link it to the Customer.                                               |
| Using Address Type alone to choose defaults          | Set the preferred billing and shipping flags explicitly.                                    |
| Assuming the primary Contact is the only Contact     | Keep all relevant Contacts linked and select the appropriate one per transaction.           |
| Editing a submitted document after a default changes | Use the new default on future documents. Submitted documents retain their recorded details. |


## Frequently asked questions

### Can one Customer have multiple Contacts and Addresses?

Y

es. This is the normal setup for organizations with several employees, offices, warehouses, or delivery locations.

### Can a Contact or Address exist without a Customer?

Y

es. Both can exist independently and be linked later.

### Can the same Contact be linked to more than one Customer?

Yes, when the person genuinely represents more than one party. Review the primary setting carefully because it belongs to the Contact record.

### Can users override the primary selection?

Y

es. Primary and preferred records provide defaults. Users can select another eligible linked record for a particular transaction.

## Related topics

- [Customer](/erpnext/customer)
- [Contact](/erpnext/contact)
- [Address](/erpnext/address)
- [Address Template](/erpnext/address-template)
- [Difference between Lead, Contact, and Customer](/erpnext/difference_between_lead_contact_and_customer)
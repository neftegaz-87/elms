---
title: "Concepts and Terms"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/concepts-and-terms"
updated: "2026-08-14"
---

Lets get familiar with the terminology that is used and some basic concepts in ERPNext.

### Basic Concepts

#### Company

This represents the Company records for which ERPNext is setup. With this same setup, you can create multiple Company records, each representing a different legal entity. The accounting for each Company will be different, but they will share the Customer, Supplier and Item records.

> Setup &gt; Company

#### Customer

Represents a customer. A Customer can be an individual or an organization. You can create multiple Contacts and Addresses for each Customer.

> Selling &gt; Customer

#### Supplier

Represents a supplier of goods or services. Your telephone company is a Supplier, so is your raw materials Supplier. Again, a Supplier can be an individual or an organization and has multiple Contacts and Addresses.

> Buying &gt; Supplier

#### Item

A Product, sub-product or Service that is either bought, sold or manufactured and is uniquely identified.

> Stock &gt; Item

#### Account

An Account is a heading under which financial and business transactions are carried on. Examples of accounts are "Debtors", "Creditors", "VAT Payable", “Travel Expenses”, "Sales", "Share Capital", etc. ERPNext keeps track of your customers' and suppliers' balances in the background, so you don't need to create dedicated Accounts for them.

> Accounting &gt; Chart of Accounts

#### Address

An address represents location details of a Customer or Supplier. These can be of different locations such as Head Office, Factory, Warehouse, Shop etc.

> Selling &gt; Address

#### Contact

An individual Contact belongs to a Customer or Supplier or is just an independent. A Contact has a name and contact details like email and phone number.

> Selling &gt; Contact

#### Communication

A list of all Communication with a Contact or Lead. All emails sent from the system are added to the Communication table.

> Support &gt; Communication

#### Price List

A Price List is a place where different rate plans can be stored. It’s a name you give to a set of Item Prices stored under a particular List.

> Selling &gt; Price List

> Buying &gt; Price List

---

### Accounting

#### Fiscal Year

Represents a Financial Year or Accounting Year. You can operate multiple Fiscal Years at the same time. Each Fiscal Year has a start date and an end date and transactions can only be recorded in this period. When you “close” a fiscal year, it's balances are transferred as “opening” balances for the next fiscal year.

> Setup &gt; Company &gt; Fiscal Year

#### Cost Center

A Cost Center is like an Account, but the only difference is that its structure represents your business more closely than Accounts. For example, in your Chart of Accounts, you can separate your expenses by its type (i.e., travel, marketing, etc.). In your Chart of Cost Centers, you can separate them by product line or business group (e.g., online sales, retail sales, etc.).

> Accounting &gt; Chart of Cost Centers

#### Journal Entry

A document that contains General Ledger (GL) entries and the sum of Debits and Credits of those entries is the same. In ERPNext you can update Payments, Returns, etc., using Journal Entries.

> Accounting &gt; Journal Entry

#### Sales Invoice

A bill sent to Customers for delivery of Items (goods or services).

> Accounting &gt; Sales Invoice

#### Purchase Invoice

A bill sent by a Supplier for delivery of Items (goods or services).

> Accounting &gt; Purchase Invoice

#### Currency

ERPNext allows you to book transactions in multiple currencies. There is only one currency for your book of accounts though. While posting your Invoices with payments in different currencies, the amount is converted to the default currency by the specified conversion rate.

> Setup &gt; Currency

---

### Selling

#### Customer Group

A classification of Customers, usually based on market segment.

> Selling &gt; Setup &gt; Customer Group

#### Lead

A person who could be a future source of business. A Lead may generate Opportunities. (from: “may lead to a sale”).

> CRM &gt; Lead

#### Opportunity

A potential sale. (from: “opportunity for a business”).

> CRM &gt; Opportunity

#### Quotation

Customer's request to price an item or service.

> Selling &gt; Quotation

#### Sales Order

A note confirming the terms of delivery and price of an Item (product or service) by the Customer. Deliveries, Work Orders and Invoices are made on basis of Sales Orders.

> Selling &gt; Sales Order

#### Territory

A geographical area classification for sales management. You can set targets for Territories and each sale is linked to a Territory.

> Selling &gt; Setup &gt; Territory

#### Sales Partner

A third party distributer / dealer / affiliate / commission agent who sells the company’s products usually for a commission.

> Selling &gt; Setup &gt; Sales Partner

#### Sales Person

Someone who pitches to the Customer and closes deals. You can set targets for Sales Persons and tag them in transactions.

> Selling &gt; Setup &gt; Sales Person

---

### Buying

#### Purchase Order

A contract given to a Supplier to deliver the specified Items at the specified cost, quantity, dates and other terms.

> Buying &gt; Purchase Order

#### Material Request

A request made by a system User, or automatically generated by ERPNext based on reorder level or projected quantity in Production Plan for purchasing a set of Items.

> Buying &gt; Material Request

---

### Stock (Inventory)

#### Warehouse

A logical Warehouse against which stock entries are made.

> Stock &gt; Warehouse

#### Stock Entry

Material transfer from a Warehouse, to a Warehouse or from one Warehouse to another.

> Stock &gt; Stock Entry

#### Delivery Note

A list of Items with quantities for shipment. A Delivery Note will reduce the stock of Items for the Warehouse from where you ship. A Delivery Note is usually made against a Sales Order.

> Stock &gt; Delivery Note

#### Purchase Receipt

A note stating that a particular set of Items were received from the Supplier, most likely against a Purchase Order.

> Stock &gt; Purchase Receipt

#### Serial Number

A unique number given to a particular unit of an Item.

> Stock &gt; Serial Number

#### Batch

A number given to a group of units of a particular Item that may be purchased or manufactured in a group.

> Stock &gt; Batch

#### Stock Ledger Entry

A unified table for all material movement from one warehouse to another. This is the table that is updated when a Stock Entry, Delivery Note, Purchase Receipt, and Sales Invoice (POS) is made.

#### Stock Reconciliation

Update Stock of multiple Items from a spreadsheet (CSV) file.

> Stock &gt; Stock Reconciliation

#### Quality Inspection

A note prepared to record certain parameters of an Item at the time of Receipt from Supplier, or Delivery to Customer.

> Stock &gt; Quality Inspection

#### Item Group

A classification of Item.

> Stock &gt; Setup &gt; Item Group

---

### Manufacturing

#### Bill of Materials (BOM)

A list of Operations and Items with their quantities, that are required to produce another Item. A Bill of Materials (BOM) is used to plan purchases and do product costing.

> Manufacturing &gt; BOM

#### Workstation

A place where a BOM operation takes place. It is useful to calculate the direct cost of the product.

> Manufacturing &gt; Workstation

#### Work Order

A document signaling production (manufacture) of a particular Item with specified quantities.

> Manufacturing &gt; Work Order

#### Production Planning Tool

A tool for automatic creation of Work Orders and Purchase Requests based on Open Sales Orders in a given period.

> Manufacturing &gt; Production Planning Tool

---

### Setup / Customization

#### Custom Field

A user defined field on a form / table.

> Setup &gt; Customize ERPNext &gt; Custom Field

#### Global Defaults

This is the section where you set default values for various parameters of the system.

> Setup &gt; Data &gt; Global Defaults

#### Print Heading

A title that can be set on a transaction just for printing. For example, you want to print a Quotation with a title “Proposal” or “Pro forma Invoice”.

> Setup &gt; Branding and Printing &gt; Print Headings

#### Terms and Conditions

Text of your terms of contract. In Sales/Purchase transactions there might be certain Terms and Conditions based on which the Supplier provides goods or services to the Customer. You can apply the Terms and Conditions to transactions and they will appear when printing the document. To know about Terms and Conditions, click here

> Selling &gt; Setup &gt; Terms and Conditions

#### Unit of Measure (UOM)

How quantity is measured for an Item. E.g., Kg, No., Pair, Packet, etc.

> Stock &gt; Setup &gt; UOM
---
title: "E-commerce Integrations for ERPNext"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/e-commerce-integrations-for-erpnext"
updated: "2026-07-04"
---

ERPNext is easy to integrate with recommerce and ecommerce platforms because business data in ERPNext is available through the Frappe Framework REST API. Products, customers, orders, invoices, payments, shipments, returns, and stock movements are stored as DocTypes, and DocTypes can be read or updated through standard API endpoints.

This makes ERPNext a practical backend for recommerce platforms that handle refurbished, pre-owned, rental, buyback, resale, or reverse-logistics workflows. The storefront can focus on customer experience, while ERPNext manages inventory, accounting, fulfillment, purchasing, returns, and reporting.

## Why Integration Is Straightforward

- **REST APIs are available by default:** External systems can create and update ERPNext records without direct database access.
- **Commerce records already exist:** Items, Customers, Sales Orders, Sales Invoices, Delivery Notes, Payment Entries, Stock Entries, and Warehouses are standard ERPNext records.
- **Recommerce data can be added:** Fields such as condition, grade, serial inspection, refurbishment status, warranty, buyback source, and resale channel can be added with custom fields or DocTypes.
- **Sync can be automated:** Webhooks, scheduled jobs, and background workers can sync orders, stock, payment status, shipment updates, and returns between systems.

## Common Integration Flows

- **Catalog sync:** Send item details, prices, images, condition, and stock availability from ERPNext to the platform.
- **Order sync:** Create Sales Orders or Sales Invoices in ERPNext when orders are placed.
- **Inventory sync:** Update the platform when stock is reserved, sold, returned, refurbished, or made available again.
- **Fulfillment sync:** Send shipment and tracking details from ERPNext back to the platform.
- **Returns and buybacks:** Track incoming goods using Stock Entries, Purchase Receipts, Quality Inspections, or custom DocTypes.

## Ready-Made Marketplace Options

Before building a custom connector, check whether an existing Frappe Marketplace app already covers the workflow:

- [Ecommerce Integrations](https://cloud.frappe.io/marketplace/apps/ecommerce_integrations): E-commerce marketplace integrations for ERPNext.
- [WooCommerce Connector](https://cloud.frappe.io/marketplace/apps/woocommerceconnector): Synchronizes items, stock, customers, addresses, sales orders, sales invoices, and payment entries with WooCommerce.
- [ERPNext Shipping](https://cloud.frappe.io/marketplace/apps/erpnext_shipping): Shipping integration for ERPNext, useful for fulfillment and tracking.
- [Frappe Paystack](https://cloud.frappe.io/marketplace/apps/frappe_paystack): Payment gateway integration for ERPNext and Frappe.

## When To Build A Custom Connector

Build a custom connector when the recommerce platform has unique flows such as device grading, serialized refurbishment, trade-in pricing, warranty tracking, marketplace-specific listing rules, or reverse logistics. In most cases, the connector maps platform events to ERPNext documents and calls the REST API securely.

## Best Practices

- Keep ERPNext as the source of truth for stock and accounting.
- Use stable external IDs to match ERPNext records with platform records.
- Log every sync attempt so failed updates can be retried.
- Use API keys with limited permissions and test on a staging site before going live.

## Related Topics

- [Frappe REST API](/framework/user/en/api/rest)
- [Sales Order](/erpnext/sales-order)
- [Item](/erpnext/item)
- [Stock Entry](/erpnext/stock-entry)
- [Frappe Cloud Marketplace](https://cloud.frappe.io/marketplace)
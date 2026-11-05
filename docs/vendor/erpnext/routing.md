---
title: "Routing\n"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/routing"
updated: "2026-02-27"
---

**Routing is a template of BOM Operations.**

A Routing stores all Operations along with the description, hourly rate, operation time, batch size, etc. Creating a Routing for your BOM Operations is useful when similar Operations are used for manufacturing different items.

---

### Prerequisites

- [Operation](/erpnext/operation)
- [Workstation](/erpnext/workstation)

---

## How to Create a Routing

1. Go to the Routing list, click on New.
2. Enter a name for the Routing.
3. Enter the Operations in the BOM Operation table:
  1. Select the Operation.
  2. The default Workstation will be fetched.
  3. Enter the Hourly Rate for running this Operation.
  4. Enter the Operation Time in minutes.
  5. Enter the Batch Size, i.e. the number of units processed in this Operation.
  6. The Operating Cost will be calculated based on the Hourly Rate and the Operation Time.
  7. Save.

Once created, a Routing can be selected in a BOM to fetch the Operations stored in the Routing.

![](/files/CleanShot 2026-02-19 at 12.31.10@2x.png)

---

## Sequence ID in Routing

![](/files/image2679eb.png)

Sequence ID enforces the users to complete the operations sequentially via Job Card. In case a user tries to complete an operation before completing any of its precedent operations as per the Sequence ID, the system throws a validation error.

---

### Related Topics

1. [Work Order](/erpnext/work-order)
2. [Bill Of Materials](/erpnext/bill-of-materials)


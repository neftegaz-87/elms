---
title: "Unit of Measure (UoM)\n"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/uom"
updated: "2026-03-06"
---

**A UoM is a unit using which an Item is measured.**

By default, there are many UoMs created in ERPNext. However, more can be added depending on your business use case.  
In the UoM there is an option 'Must be Whole Number'. If this is checked, you cannot use fraction numbers in this UoM. To know more about fractions and UoMs, check out [this page](/erpnext/managing-fractions-in-uom).

The UoM list by itself only stores the name. The actual conversion rates are stored in a document called 'UoM Conversion Factor'. If you add new UoMs and plan to use it in transactions where it'll be converted to other UoMs, it is advised that you add it to this list.

For example, here 1 Kg is approximately 2.2 Pounds and the exact conversion factor is stored:

![](/files/uom-conversion.png)


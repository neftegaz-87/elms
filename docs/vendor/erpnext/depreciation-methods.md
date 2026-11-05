---
title: "Depreciation Methods | ERPNext Documentation"
description: "Choose and configure Straight Line, Double Declining Balance, Written Down Value, or Manual depreciation in ERPNext."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/depreciation-methods"
updated: "2026-08-15"
---

Imagine Nova Industries buys two assets for the same price: an office table and a production machine. The table may provide roughly the same value every year. The machine may lose more value in its early years because it works hardest when it is new. Using one depreciation pattern for both may not reflect how they are actually used.



Depreciation Methods let the accountant choose how an asset's cost is spread over its useful life. ERPNext supports methods such as Straight Line and declining balance so the schedule can follow the company's accounting policy and the asset's pattern of use.

## Depreciation methods at a glance


| Method                       | How it works                                                                                    | Best suited for                                                                                                               |
| ---------------------------- | ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **Straight Line**            | Records an equal depreciation expense in every complete period.                                 | Assets that provide a similar benefit throughout their life, such as office furniture, air conditioners, and basic equipment. |
| **Double Declining Balance** | Records a larger expense in the early years and a smaller expense later.                        | Assets that lose usefulness or value quickly when new, such as computers, mobile devices, and rapidly ageing machinery.       |
| **Written Down Value**       | Applies a fixed percentage to the asset's opening book value, so the expense reduces over time. | Assets for which the company's accounting or tax policy prescribes depreciation on the remaining book value.                  |
| **Manual**                   | Uses depreciation dates and amounts entered by the accountant instead of a standard formula.    | Assets with a contract-based, valuation-based, or specially approved depreciation schedule.                                   |


Treat this table as a practical starting point. The method used in the accounts should ultimately follow the organization's approved accounting policy and applicable reporting rules.

## Use one example to compare the methods

Assume Nova Industries buys a packaging machine for $50,000. It expects to use the machine for five years and sell it for $5,000 at the end. The amount to depreciate is therefore:



**Depreciable value = $50,000 cost - $5,000 residual value = $45,000**



Every method eventually allocates the same $45,000. What changes is how much expense appears in each year.

## Straight Line

Straight Line records the same expense in every complete year.



**Annual depreciation = $45,000 / 5 years = $9,000**


| Year | Opening book value | Depreciation | Closing book value |
| ---- | ------------------: | ------------: | ------------------: |
| 1    | $50,000            | $9,000       | $41,000            |
| 2    | $41,000            | $9,000       | $32,000            |
| 3    | $32,000            | $9,000       | $23,000            |
| 4    | $23,000            | $9,000       | $14,000            |
| 5    | $14,000            | $9,000       | $5,000             |


Use this method when the asset provides a similar benefit each year. Office furniture, air conditioners, and basic production equipment often fit this pattern.

## Double Declining Balance

Double Declining Balance records more depreciation while the asset is new. For a five-year life, the Straight Line rate is 20 percent. Double Declining uses twice that rate, or 40 percent, on each year's opening book value.



**Year 1 depreciation = $50,000 x 40% = $20,000**



The final expense is limited so the asset never falls below its $5,000 residual value.


| Year | Opening book value | Calculation               | Depreciation | Closing book value |
| ---- | ------------------: | ------------------------- | ------------: | ------------------: |
| 1    | $50,000            | $50,000 x 40%             | $20,000      | $30,000            |
| 2    | $30,000            | $30,000 x 40%             | $12,000      | $18,000            |
| 3    | $18,000            | $18,000 x 40%             | $7,200       | $10,800            |
| 4    | $10,800            | $10,800 x 40%             | $4,320       | $6,480             |
| 5    | $6,480             | Limited to residual value | $1,480       | $5,000             |


Use this method when an asset loses usefulness or market value faster in its early years. Computers, mobile devices, and some high-use machinery are common examples.

## Written Down Value

Written Down Value applies a chosen rate to the opening book value. Assume Nova's policy uses 30 percent per year for this machine.



**Year 1 depreciation = $50,000 x 30% = $15,000**



Because the opening value becomes smaller each year, the depreciation expense also becomes smaller. The last year is again limited so the closing value does not fall below $5,000.


| Year | Opening book value | Calculation               | Depreciation | Closing book value |
| ---- | ------------------: | ------------------------- | ------------: | ------------------: |
| 1    | $50,000            | $50,000 x 30%             | $15,000      | $35,000            |
| 2    | $35,000            | $35,000 x 30%             | $10,500      | $24,500            |
| 3    | $24,500            | $24,500 x 30%             | $7,350       | $17,150            |
| 4    | $17,150            | $17,150 x 30%             | $5,145       | $12,005            |
| 5    | $12,005            | Limited to residual value | $7,005       | $5,000             |


Use this method when the company's accounting or tax policy specifies a percentage on the remaining value. The example rate is illustrative. Use the rate approved for your organization.

## Manual

Manual depreciation lets the accountant define the dates and amounts instead of relying on a standard formula. Nova might use the following schedule when an equipment contract expects heavier use in its first two years.


| Year | Opening book value | Depreciation entered | Closing book value |
| ---- | ------------------: | --------------------: | ------------------: |
| 1    | $50,000            | $15,000              | $35,000            |
| 2    | $35,000            | $10,000              | $25,000            |
| 3    | $25,000            | $8,000               | $17,000            |
| 4    | $17,000            | $7,000               | $10,000            |
| 5    | $10,000            | $5,000               | $5,000             |


Use Manual only when a documented policy, valuation, or contract requires a custom pattern. The entered amounts should still total the $45,000 depreciable value.

## Compare the result


| Method                        | Expense pattern        | Year 1 expense | Year 5 expense                    | Closing value after year 5 |
| ----------------------------- | ---------------------- | --------------: | ---------------------------------: | --------------------------: |
| **Straight Line**             | Equal                  | $9,000         | $9,000                            | $5,000                     |
| **Double Declining Balance**  | Highest in early years | $20,000        | $1,480                            | $5,000                     |
| **Written Down Value at 30%** | Reduces each year      | $15,000        | $7,005 after residual-value limit | $5,000                     |
| **Manual example**            | Set by policy          | $15,000        | $5,000                            | $5,000                     |


## Set the method in ERPNext

Set the default method, useful life, frequency, and residual value in the Asset Category Finance Book row. The Asset can then use those defaults when ERPNext builds its depreciation schedules.

![Different depreciation methods by Finance Book](https://novacompanies.m.frappe.cloud/files/03-asset-category-finance-books.png)

The submitted schedule below uses Straight Line for Nova's packaging equipment. ERPNext has calculated $760 per month, accumulated the amount, and linked each posted row to its Journal Entry.

![Submitted depreciation schedule with calculated amounts](https://novacompanies.m.frappe.cloud/files/26-asset-depreciation-schedule-v2.png)

## Verify the result

Before submission, compare total scheduled depreciation plus residual value with the capitalized value. Also check the last date and the first full or prorated period.

## Troubleshooting

### The last schedule row is unexpectedly small

ERPNext may be limiting the final row so carrying value does not fall below the configured residual value.

### Two Finance Books show different carrying values

That is expected when they use different methods, useful lives, or start dates. Review reports with the intended Finance Book filter.

## Frequently asked questions

### Which method is best?

There is no universal best method. Use the method approved by the organization's accounting policy and reporting requirements.

### Can the method be changed after entries are posted?

A policy change may require cancellation or adjustment of linked schedules and entries. Review the accounting impact before changing a submitted asset.

### Can statutory and management reporting differ?

Separate Finance Books can keep different depreciation policies for the same asset.

## Related topics

- [Asset Category](https://docs.frappe.io/erpnext/asset-category)
- [Asset Location](https://docs.frappe.io/erpnext/asset-location)
- [Asset](https://docs.frappe.io/erpnext/asset)
- [Purchasing an Asset](https://docs.frappe.io/erpnext/purchasing-an-asset)
- [Depreciation](https://docs.frappe.io/erpnext/asset-depreciation)
- [Asset Movement](https://docs.frappe.io/erpnext/asset-movement)
- [Asset Repair](https://docs.frappe.io/erpnext/asset-repair)
- [Asset Reports](https://docs.frappe.io/erpnext/asset-reports)
---
title: "Custom Statuses"
space: "CRM"
url: "https://docs.frappe.io/crm/custom-statuses"
updated: "2026-05-26"
---

# Custom Statuses

Custom statuses let you filter which status options appear in the  Lead or Deal dropdown. You can define different status lists based on  any field value on the document.

## How it works

Set `this.statuses` to an array of status **name strings**. Only statuses whose name appears in the array will be shown in the dropdown. The names must exist in the **CRM Lead Status** or **CRM Deal Status** master — add new ones in **CRM Settings → Statuses** first.

The array is set inside a CRM Form Script class for your doctype.  Because the list is just JavaScript, you can conditionally choose  statuses based on any field or logic.

## Basic Example — Static List

```js
class CRMLead {
    onLoad() {
        this.statuses = [
            "New",
            "Contacted",
            "Qualified",
            "Nurturing",
            "Lost"
        ]
    }
}
```

The dropdown will only show these five statuses, in this order.  


![](/files/Screenshot 2026-05-26 at 6.21.39 PM.png)

## Dynamic Example — Per Deal Type

Different products or services often need different sales pipelines.  Use a field change handler to swap the status list when the user changes  a field.

The deal statuses that ship by default are:


| Status             | Included in Product | Included in Service |
| ------------------ | ------------------- | ------------------- |
| Qualification      | ✓                   | —                   |
| Demo/Making        | ✓                   | —                   |
| Proposal/Quotation | —                   | ✓                   |
| Negotiation        | ✓                   | ✓                   |
| Ready to Close     | —                   | ✓                   |
| Won                | ✓                   | ✓                   |
| Lost               | ✓                   | ✓                   |




```js
class CRMDeal {
  onLoad() {
    this._updateStatuses();
  }

  custom_deal_type() {
    this._updateStatuses();
    // Reset status if the current value isn't in the new pipeline
    if (this.doc.status && !this.statuses.includes(this.doc.status)) {
      this.doc.status = this.statuses[0];
    }
  }

  _updateStatuses() {
    if (this.doc.custom_deal_type === "Product") {
      this.statuses = [
        "Qualification",
        "Demo/Making",
        "Negotiation",
        "Won",
        "Lost",
      ];
    } else {
      this.statuses = [
        "Proposal/Quotation",
        "Negotiation",
        "Ready to Close",
        "Won",
        "Lost",
      ];
    }
  }
}

```

The helper `_updateStatuses` runs on load and whenever `custom_deal_type` changes. Switching pipelines also resets `this.doc.status` to the first entry if the current value no longer exists in the new list.

## Adding Custom Status Names

If the default statuses don't fit your process, add new ones in **CRM Deal Status / CRM Lead Status**  in Desk. For example, the Product pipeline might need "Evaluation" and  the Service pipeline might need "Consultation/Inquiry". Create those  status entries first, then reference them in your script:

```js
class CRMDeal {
  onLoad() {
    this._updateStatuses();
  }
  _updateStatuses() {
    this.statuses = [
      "Consultation/Inquiry", // custom — create in CRM Settings first
      "Proposal/Quotation",
      "Negotiation",
      "Won",
      "Lost",
    ];
  }
}

```

A status name that doesn't exist in the master is silently ignored — it won't appear in the dropdown, and no error is shown.  


![](/files/Screenshot 2026-05-26 at 6.57.01 PM.png)
*New status in CRM Deal Status*

![](/files/Screenshot 2026-05-26 at 6.56.55 PM.png)

## Default Statuses

### CRM Lead Status


| Name        | Type    | Position |
| ----------- | ------- | -------- |
| New         | Open    | 1        |
| Contacted   | Ongoing | 2        |
| Nurture     | Ongoing | 3        |
| Qualified   | Won     | 4        |
| Converted   | Won     | 5        |
| Unqualified | Lost    | 6        |
| Junk        | Lost    | 7        |


### CRM Deal Status


| Name               | Type    | Position | Probability |
| ------------------ | ------- | -------- | ----------- |
| Qualification      | Open    | 1        | 10%         |
| Demo/Making        | Ongoing | 2        | 25%         |
| Proposal/Quotation | Ongoing | 3        | 50%         |
| Negotiation        | Ongoing | 4        | 70%         |
| Ready to Close     | Ongoing | 5        | 90%         |
| Won                | Won     | 6        | 100%        |
| Lost               | Lost    | 7        | 0%          |


## Reference


| Property        | Type       | Description                                                                                                |
| --------------- | ---------- | ---------------------------------------------------------------------------------------------------------- |
| `this.statuses` | `string[]` | Array of status names to show in the dropdown. Readable and writable at any point in the script lifecycle. |


### Behaviour notes

- **Order**: Statuses appear in the dropdown in the order you specify in the array.
- **Missing statuses**: Names that don't exist in the  master are silently ignored — they won't appear as options. Check your  spelling or add them in CRM Settings → Statuses.
- **Reactivity**: Updating `this.statuses` after the form has loaded (e.g. in a field change handler) re-renders the dropdown immediately.
- **Status reset**: When switching pipelines, the current `this.doc.status` is **not** automatically cleared — use the `includes` check pattern shown above to reset it explicitly.






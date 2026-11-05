---
title: "Custom Actions"
space: "CRM"
url: "https://docs.frappe.io/crm/custom-actions"
updated: "2026-05-26"
---

# Custom Actions

Custom actions let you add buttons to the Lead or Deal page header.  You can add single buttons, group them under a dropdown, or create  labeled dropdown menus — each running your own logic when clicked.

## Creating Custom Actions

Custom actions live inside a CRM Form Script. Open **CRM Form Script** in Desk, pick your DocType (Lead or Deal), and write a class. Set `this.actions` inside `onLoad()`:

```js
class CRMDeal {
    onLoad() {
        this.actions = [
            {
                label: "Open in Desk",
                onClick: (close) => {
                    let URL = `https://frappecrm.frappe.cloud/app/crm-deal/${this.doc.name}`
                    window.open(URL, '_blank')
                }
            }
        ]
    }
}

```

This adds a button labelled "Open in Desk" that opens the current deal in a new tab.  


![](/files/Screenshot 2026-05-26 at 5.51.52 PM.png)
*"Open In Desk" Button in Top Right of the header *

### Grouped Actions (three-dot menu)

Use `group` to nest items under a single `more-horizontal` icon dropdown. Set `hideLabel: true` to hide the group heading from the dropdown menu.



```js
class CRMDeal {
    onLoad() {
        this.actions = [
            {
                group: "Add",
                hideLabel: true,
                items: [
                    { label: "Create Quotation", onClick: (close) => {} },
                    { label: "Create Sales Order", onClick: (close) => {} },
                ]
            },
            {
                group: "Delete",
                items: [
                    { label: "Delete Quotation", onClick: (close) => {} },
                    { label: "Delete Sales Order", onClick: (close) => {} },
                ]
            }
        ]
    }
}

```

![](/files/Screenshot 2026-05-26 at 5.50.39 PM.png)

### Grouped Actions with Label (dropdown button)

Add `buttonLabel` to turn the three-dot icon into a labelled dropdown button.



```js
class CRMDeal {
    onLoad() {
        this.actions = [
            {
                buttonLabel: "Create",
                group: "Add",
                hideLabel: true,
                items: [
                    { label: "Create Quotation", onClick: (close) => {} },
                    { label: "Create Sales Order", onClick: (close) => {} },
                ]
            }
        ]
    }
}

```

![](/files/Screenshot 2026-05-26 at 5.53.36 PM.png)

### Mixing Single Buttons and Groups

You can combine both styles in one array:

```js
class CRMDeal {
    onLoad() {
        this.actions = [
            {
                label: "Refresh Score",
                icon: "refresh-cw",
                onClick: (close) => { /* ... */ }
            },
            {
                group: "More",
                hideLabel: true,
                items: [
                    { label: "Export PDF", onClick: (close) => {} },
                    { label: "Duplicate", onClick: (close) => {} },
                ]
            }
        ]
    }
}
```

![](/files/Screenshot 2026-05-26 at 5.54.11 PM.png)

## What You Have Access To

Inside your script, these helpers are available without any imports:

- `this.doc` — the current document. Read and write fields directly: `this.doc.status = "Lost"`, `this.doc.deal_name`.
- `call(method, params)` — call any server-side Python method. Returns a Promise.
- `createDialog(options)` — show a confirmation dialog. Provide `title`, `message`, and `actions`.
- `formDialog(options)` — show a dialog with form fields to collect input from the user.
- `toast.success(msg)`, `toast.error(msg)`, `toast.info(msg)` — show notifications.
- `router.push(location)`, `router.replace(location)` — navigate to a different page.
- `throwError(msg)` — show a red toast and stop execution immediately.

## Examples

### Create Quotation (only for Won Deals)

This action checks if the deal is Won, then calls the server to  create a quotation. If successful, it navigates to the new quotation  page.

```js
class CRMDeal {
  onLoad() {
    this.actions = [
      {
        label: "Create Quotation",
        icon: "file-text",
        onClick: (close) => {
          if (this.doc.status !== "Won") {
            toast.info("This action is only available for Won deals");
            return;
          }

          call("crm.api.quotation.create_from_deal", {
            deal: this.doc.name,
            customer: this.doc.organization,
          }).then((data) => {
            if (data?.name) {
              router.push({ name: "Quotation", params: { name: data.name } });
              toast.success("Quotation created successfully");
            } else {
              toast.error("Could not create quotation");
            }
          });
        },
      },
    ];
  }
}

```

### Mark as Lost (with confirmation)

Asks the user to confirm, then updates the deal status directly.

```js
class CRMDeal {
  onLoad() {
    this.actions = [
      {
        label: "Mark as Lost",
        icon: "x-circle",
        onClick: (close) => {
          createDialog({
            title: "Mark Deal Lost",
            message: "Are you sure you want to mark this deal as Lost?",
            actions: [
              {
                label: "Mark Lost",
                theme: "red",
                variant: "solid",
                onClick: async ({ close: dialogClose }) => {
                  this.doc.status = "Lost";
                  toast.success("Deal marked as Lost");
                  dialogClose();
                },
              },
              {
                label: "Cancel",
                variant: "outline",
                onClick: ({ close: dialogClose }) => dialogClose(),
              },
            ],
          });
        },
      },
    ];
  }
}

```

### Schedule a Follow-up (with form dialog)

Opens a dialog with date and notes fields. When submitted, calls the server to save the follow-up.

```js
class CRMDeal {
  onLoad() {
    this.actions = [
      {
        label: "Schedule Follow-up",
        icon: "calendar",
        onClick: (close) => {
          formDialog({
            title: "Schedule Follow-up",
            fields: [
              {
                fieldname: "date",
                fieldtype: "Date",
                label: "Follow-up Date",
                reqd: 1,
              },
              { fieldname: "notes", fieldtype: "Small Text", label: "Notes" },
            ],
            submitLabel: "Schedule",
            cancelLabel: "Cancel",
            onSubmit: async (data) => {
              await call("crm.api.deal.schedule_followup", {
                deal: this.doc.name,
                date: data.date,
                notes: data.notes,
              });
              toast.success("Follow-up scheduled for " + data.date);
            },
          });
        },
      },
    ];
  }
}

```

### Delete Deal (with confirmation and redirect)

Confirms before deleting, then redirects back to the deals list.

```js
class CRMDeal {
  onLoad() {
    this.actions = [
      {
        label: "Delete Deal",
        icon: "trash-2",
        onClick: (close) => {
          createDialog({
            title: "Delete Deal",
            message: `Are you sure you want to delete "${this.doc.deal_name}"? This cannot be undone.`,
            actions: [
              {
                label: "Delete",
                theme: "red",
                variant: "solid",
                onClick: async ({ close: dialogClose }) => {
                  await call("frappe.client.delete", {
                    doctype: "CRM Deal",
                    name: this.doc.name,
                  });
                  dialogClose();
                  router.push("/deals");
                  toast.success("Deal deleted");
                },
              },
              {
                label: "Cancel",
                variant: "outline",
                onClick: ({ close: dialogClose }) => dialogClose(),
              },
            ],
          });
        },
      },
    ];
  }
}

```



## Showing and Hiding Actions Based on Field Values

Sometimes you only want certain actions to appear in certain situations. Re-set `this.actions` whenever the relevant field changes:

```js
class CRMDeal {
  onLoad() {
    this._updateActions();
  }

  // Re-run whenever status changes
  status() {
    this._updateActions();
  }

  _updateActions() {
    const isLost = this.doc.status === "Lost";

    this.actions = [
      {
        label: "Create Quotation",
        onClick: (close) => {
          /* ... */
        },
      },
      // Only show "Mark as Lost" if the deal isn't already lost
      ...(!isLost
        ? [
            {
              label: "Mark as Lost",
              icon: "x-circle",
              onClick: (close) => {
                /* ... */
              },
            },
          ]
        : []),
    ];
  }
}

```


---
title: "Custom List Actions"
space: "CRM"
url: "https://docs.frappe.io/crm/custom-list-actions"
updated: "2026-02-05"
---

Similar to Custom Actions, Custom List Actions allows you to add custom actions that you can perform directly from the list view of various Frappe CRM masters (e.g., Leads, Deals, Organizations). These actions enhance your workflow by allowing quick execution of specific tasks without needing to open individual records.

## Types of List Actions

There are two main categories of custom list actions:

1. **Actions:** These resemble the custom actions you find on individual lead/deal pages. They appear as buttons in the list view header beside the create button.
  Example:
    
  ![](/files/uYxvLR7.png)
    
  ![](/files/i75wZ8b.png)
    In this example, the "Delete junk deals" button was added on listview which will automatically delete all the junk deals.

You can create all types of actions (Normal Button, Grouped Actions, Grouped Actions with label and combination of all).
2. **Bulk Actions:** These are designed for performing specific tasks on multiple selected rows in the list view. This caters to situations where you need to apply the same action to a group of records simultaneously.

```
Example:

![](/files/95SvEcH.png)
![](/files/TgJvk5C.png)  


```
{
  "label": "Mark Won",
  "onClick": async ({ list, selections, unselectAll, call }) => {
    let docs = Array.from(selections)
    for (const doc of docs) {
        // Update the status of each selected Lead/Deal to "Won"
        let updated = await call('frappe.client.set_value', {
            doctype: 'CRM Deal',
            name: doc,
            fieldname: 'status',
            value: 'Won',
        })
    }
    unselectAll()
    list.reload()
  }
}
```

In this example, the "Mark Won" button iterates through each selected Lead/Deal name (`selections`) and updates its status to "Won" using the `call` method. Finally, it unselects all rows using `unselectAll` method and reloads the list view using `list.reload()`.
```

## Adding Custom List Actions

You can define custom list actions using Frappe CRM's Form Script functionality. Here's a step-by-step guide:

1. **Navigate to Desk:** Switch to Desk and navigate to CRM Form Script.
2. **Select Doctype and Apply To:** Choose the Doctype (e.g., Customer) for which you want to create the list actions. In the "Apply To" field, select "List" and save the configuration. This will generate a boilerplate code snippet.
3. **Define Actions:** The boilerplate code provides two options:
  **actions:** Here, you can specify a list of action buttons similar to custom actions on individual record pages (refer to the documentation for custom actions for detailed guidance on defining button functionality [link](https://docs.frappe.io/crm/custom-actions)). These buttons will be visible in the list view header.
   **bulk_actions:** This section allows you to define action buttons specifically designed for bulk operations on selected rows.
4. **List Context:** Both action types utilize JavaScript code to perform the desired functionalities. You'll have access to a `list` object as a parameter on `setupList` and also on `onClick` event, which provides valuable context about the list view. This object offers functionalities like reloading the list (`list.reload()`) and accessing additional information.
  Other than `list` other contexts are also passed like `$dialog`, `router`, `createToast`, and `call`. (for more details check                 [here](https://docs.frappe.io/crm/custom-actions#using-context-and-actions))
5. **Bulk Action Context:** When defining bulk actions, the `onClick` event receives additional context besides the standard parameters. This context includes:
  **selections:** This is a Set object containing the names of all currently selected rows in the list view.
   **unselectAll:** This is a function that allows you to deselect all currently chosen rows.

By effectively utilizing these custom list actions, you can streamline your workflow and enhance your data management experience within Frappe CRM.

## Leveraging Custom List Actions

Custom List Actions offer a powerful way to automate repetitive tasks on multiple Leads or Deals. You can leverage them for various purposes, such as:

- Updating statuses for a group of Leads/Deals
- Sending mass emails or notifications
- Exporting selected data for further analysis
- Triggering custom workflows based on bulk actions


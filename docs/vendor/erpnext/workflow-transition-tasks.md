---
title: "Workflow Transition Tasks"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/workflow-transition-tasks"
updated: "2026-03-02"
---

> Note: To be added in version 16
>
>

## Introduction
Workflow Transition Tasks are actions that can be run during state transitions in workflows. Each Workflow Transition can link to a set of transition tasks.
![Link to Workflow Transition Tasks](/files/Screenshot 2025-07-20 at 2.06.27 PM.png)

![A Typical set of transition tasks](/files/Screenshot 2025-07-20 at 2.08.23 PM.png)

Each Workflow Transition Task can have tasks of the following types:

1. App-Defined Actions (specified by each Frappe app through hooks.py)
2. [Server Scripts](/framework/user/en/desk/scripting/server-script)
3. [Webhooks](/framework/user/en/guides/integration/webhooks)

![A server script transition task](/files/Screenshot 2025-07-20 at 2.38.43 PM.png)

On top of this, each transition task can be either:

1. **Synchronous**: This is the default mode of transition tasks. All of the transition tasks run one-by-one when the state transition is initiated. Even if one of them fails, the transition is reversed.
2. **Asynchronous**: This mode can be enabled using the 'Asynchronous' checkbox. Each asynchronous transition task runs after the state transition is completed, meaning it has zero influence over state completion, and is run in a separate background job of its own.

### App-Defined Actions
Each Frappe app defines them using the 'workflow_methods' [hook](/framework/user/en/python-api/hooks).

Any dotted path method defined through the workflow_methods hook has to accept `doc: Document` as the parameter, which is the document on which the transition is being applied.

An example of an app-defined task is:

```python 
# hooks.py
workflow_methods = [{"name": "Create a customer", "method":
					 "myapp.shop.doctype.kirana.create_customer"}]

# myapp/shop/doctype/kirana.py
def create_customer(doc):
    customer = frappe.new_doc("Customer")
    customer.customer_name = "Customer " + doc.name
    customer.customer_type = "Individual"

    customer.save()
```

These will be available in the 'Tasks' drop-down if any of the apps has provided them.
![app-defined tasks](/files/Screenshot 2025-07-20 at 2.56.05 PM.png)

If you are an end user, you can not create app-defined actions on your own and will have to use server scripts as mentioned below.



### Server Scripts
These also take the `doc: Document` parameter and can be set using the 'Workflow Task' Script Type.
![server script tasks](/files/Screenshot 2025-07-20 at 3.00.48 PM.png)

And then these have to be linked to in the transition task:
![A server script transition task](/files/Screenshot 2025-07-20 at 2.38.43 PM.png)


### Webhooks
These can be created by setting the 'Doc Event' field of the webhook to 'workflow_transition':
![workflow_transition webhook](/files/Screenshot 2025-07-20 at 3.03.12 PM.png)

And then these have to be linked to in the transition task:
![link to webhook](/files/Screenshot 2025-07-20 at 3.13.25 PM.png)

### Related Topics
* [Workflow State](/erpnext/user/manual/en/workflow-state)
* [Workflow Actions](/erpnext/user/manual/en/workflow-actions)
* [Workflows](/erpnext/user/manual/en/workflows)
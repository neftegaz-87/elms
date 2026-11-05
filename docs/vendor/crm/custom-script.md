---
title: "Custom Script"
space: "CRM"
url: "https://docs.frappe.io/crm/custom-script"
updated: "2026-09-29"
---

In Frappe CRM, you can automate lead creation using the **Server Script** feature. The `Server Script` DocType allows you to write server-side Python code without creating a custom app or deploying anything.

There are four types of Server Scripts, but for this guide, we'll focus on:

1. **DocType Event**
2. **API**
3. **Scheduler Event**

## 1. Create Lead When an Email is Received (DocType Event)

Let’s say you want to create a Lead whenever an incoming email is received.

### Step 1: Go to Server Script

Navigate to:  
**Desk → Search Server Script → Add Server Script**

![](/files/Screenshot%202025-05-14%20at%204.22.39%E2%80%AFPM.png)

![](/files/Screenshot%202025-05-14%20at%204.24.06%E2%80%AFPM.png)

### Step 2: Fill in the following:


| Field           | Value         |
| --------------- | ------------- |
| **Script Type** | DocType Event |
| **Doctype**     | Communication |
| **Event**       | After Insert  |
| **Script**      | *(see below)* |


### Sample Script:

```python
if doc.communication_type == 'Communication' and doc.sent_or_received == 'Received':
    existing_lead = frappe.db.exists("CRM Lead", {"email": doc.sender})
    if not existing_lead:
        frappe.get_doc({
            "doctype": "CRM Lead",
            "first_name": doc.sender_full_name,
            "email": doc.sender,
            "source": "Email",
            "status": "New",
        }).insert(ignore_permissions=True)
```

This will automatically create a new Lead for each new incoming email, avoiding duplicates.

![](/files/Screenshot%202025-05-14%20at%204.21.07%E2%80%AFPM.png)

## 2. Create Lead via Custom API (API Script)

Sometimes you want to allow external systems to create leads by calling an API endpoint.

### Step 1: Go to Server Script

Navigate to:  
**Desk → Search Server Script → Add Server Script**

![](/files/Screenshot%202025-05-14%20at%204.22.39%E2%80%AFPM.png)

![](/files/Screenshot%202025-05-14%20at%204.24.06%E2%80%AFPM.png)

### Step 2: Fill in the following:


| Field           | Value             |
| --------------- | ----------------- |
| **Script Type** | API               |
| **API Method**  | `create_lead_api` |
| **Script**      | *(see below)*     |


### Sample Script:

```python
data = frappe.local.form_dict

if not data.get("email") or not data.get("name"):
    frappe.throw("Missing required fields: 'email' and 'name'")

existing_lead = frappe.db.exists("CRM Lead", {"email": data["email"]})
if existing_lead:
    frappe.response["message"] = f"Lead already exists: {existing_lead}"
else:
    lead = frappe.get_doc({
        "doctype": "CRM Lead",
        "first_name": data["name"],
        "email": data["email"],
        "status": "New",
        "source": "API"
    })
    lead.insert(ignore_permissions=True)
    frappe.response["message"] = f"Lead created: {lead.name}"
```

### How to Use:

Send a `POST` request to:

```
https://<your-site>/api/method/create_lead_api
```

With body:

```json
{
  "email": "someone@example.com",
  "name": "Someone"
}
```

![](/files/Screenshot%202025-05-14%20at%204.26.21%E2%80%AFPM.png)

## 3. Create Lead via Scheduled Job (Scheduler Event)

You may want to create leads periodically based on some logic — for example, leads from another table, or inactive users.

### Step 1: Go to Server Script

Navigate to:  
**Desk → Search Server Script → Add Server Script**

![](/files/Screenshot%202025-05-14%20at%204.22.39%E2%80%AFPM.png)

![](/files/Screenshot%202025-05-14%20at%204.24.06%E2%80%AFPM.png)

### Step 2: Fill in the following:


| Field               | Value                    |
| ------------------- | ------------------------ |
| **Script Type**     | Scheduler Event          |
| **Cron Expression** | `0 * * * *` (Every hour) |
| **Script**          | *(see below)*            |


### Sample Script:

```python
# Example: Create a test lead every hour for demo
frappe.get_doc({
    "doctype": "CRM Lead",
    "first_name": "Auto Generated Lead",
    "email": f"demo_{frappe.utils.now_datetime().strftime('%H%M%S')}@example.com",
    "source": "Scheduled Script",
    "status": "New"
}).insert(ignore_permissions=True)
```

You can replace this logic with any query, filter, or custom rule to generate leads.

![](/files/Screenshot%202025-05-14%20at%204.27.12%E2%80%AFPM.png)

## Permission Query (Skipped)

The **Permission Query** type is used to control record visibility dynamically. It’s not used for lead creation, so we’re skipping it in this guide.

## Tips

- Always test your script in a **Test Site** before using it in production.
- Use `ignore_permissions=True` cautiously.
- Use `frappe.throw()` for input validation in API scripts.

## Learn More

- [Server Scripts in Frappe Docs](https://docs.frappe.io/framework/user/en/desk/scripting/server-script)
- [CRON Format Guide](https://crontab.guru/)


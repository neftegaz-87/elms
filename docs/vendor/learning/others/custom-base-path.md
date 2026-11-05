---
title: "Configuring Custom Base Path"
space: "Learning"
url: "https://docs.frappe.io/learning/others/custom-base-path"
updated: "2026-02-24"
---

By default, your portal is accessible at `your-site.com/lms`. If you prefer a different directory (e.g., `/school` or `/academy`), you can change the **Base Path**.

1. Access your server's terminal.
2. Open your `site_config.json` file.
3. Add the `lms_path` key:
  ```
  {
    "lms_path": "school"
  }

  ```
4. **Important:** Clear cache and restart to apply changes. You can do it by running the following commands:
  ```
  bench clear-cache
  bench restart

  ```

The dashboard will now be accessible at `/school` instead.
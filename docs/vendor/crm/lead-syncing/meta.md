---
title: "Facebook / Instagram"
space: "CRM"
url: "https://docs.frappe.io/crm/lead-syncing/meta"
updated: "2026-03-09"
---

### Prerequisites

Before you begin, you must have atleast one Facebook page and a lead generation form. You can follow [this guide](https://developers.facebook.com/docs/facebook-login/guides/access-tokens/) to obtain an access token for your account.

> Note: This feature is in beta, if you find any bugs, please report [here](https://github.com/frappe/crm).

### Adding a new Lead Sync Source

Open **Settings** from the dropdown menu on top-left corner of the CRM dashboard:

![Settings from Sidebar](/files/CleanShot%202025-11-11%20at%2017.09.58@2x.png)

Click on the **Lead Syncing** tab and then click on the `+ New` button to add a new Source:

![Lead Syncing Settings](/files/CleanShot%202025-11-11%20at%2017.15.57@2x4d3c60.png)

### Configuring Lead Sync Source

Now follow these steps:

1. Select **Facebook** as the source type
2. Give your source a relevant name
3. Select a frequency for scheduled syncing: how frequently the leads should be automatically synced
4. Paste the Access token obtained from Meta

![New Lead Sync Source](/files/CleanShot%202025-11-11%20at%2017.18.55@2x047f4a.png)

Now click **Create**. It will take a few seconds since we are pulling the pages and forms from Facebook. But once it is done, you can select the page and the form from where the leads will be pulled in from:

![Select Page and corresponding form](/files/CleanShot%202025-11-11%20at%2018.00.30@2x.png)

As soon as you select the form, you will see a mapping table:

![CRM Mapping Table](/files/CleanShot%202025-11-11%20at%2018.00.49@2x.png)

This table let's you easily map fields of your Facebook form to fields in Frappe CRM. Apart from this, we also store the Lead ID and Form ID in CRM Lead document. Once you are done configuring the field mapping, click on **Update**, and that is it! Your leads will start syncing in the background in some time.

:::tip
You can use Meta's [Graph API Explorer](https://developers.facebook.com/tools/explorer/) to test your token.
:::





### Sync Now

You can also manually trigger a lead sync by clicking on the **Sync Now** button.

### Failure Logs & Retry

If your leads don't appear in your CRM, go to the **Failure Logs** tab, and check the logs. The failure log contains the reason for failure (e.g. Duplicate), the lead data we received from Facebook, and also error traceback if available:

![Sync Failure Log](/files/CleanShot%202025-11-11%20at%2018.16.07@2xc169ec.png)

You can click on the **Retry Sync** button to retry syncing of this particular lead. 

> Note: A new failure log will get created if a resync fails too.


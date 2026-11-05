---
title: "Twitter Settings | ERPNext Documentation"
description: "Configure the legacy Twitter integration settings in ERPNext and understand current availability limitations."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/twitter-settings"
updated: "2026-07-23"
---

> Note: This integration doesn't work anymore due to Twitter's API changes. This has been removed from ERPNext starting from v15.

Twitter related settings like OAuth can be configured here. ERPNext needs access to the API through which the post is shared and achieved using OAuth 2.0 Authentication Protocol.

- How to set up Twitter App

You must have Twitter App for your company. ERPNext interacts with this App for sharing Tweet.

### Create Twitter Developer App

Create App by link [https://developer.twitter.com/](https://developer.twitter.com/) and check that the App has **Read and write** Access permission. 

![Twitter App Permission](/files/twitter-app-permission.png)

### Configure Callback URL

- Select your App and go to **App Details**.
- Then go to **Edit** and click **Edit Details**.
- Add your website URL in **Callback URLs** like: https://{yoursite}/api/method/erpnext.crm.doctype.twitter_settings.twitter_settings.callback
- Click **Save** to make changes.

![Twitter App Callback URL](/files/twitter-callback-url.png)

- How to set up Twitter Settings

To access Twitter Settings, go to:

> Home > CRM > Settings > Twitter Settings

![Twitter Settings](/files/twitter-settings.png)

### API Key and API Key Secret

You get **API Key** and **API Key Secret** from your Twitter Developer account go to:

> [https://developer.twitter.com/](https://developer.twitter.com/) > My Apps > {Your App} > Keys and tokens

![Twitter Keys Tokens](/files/twitter-key-token.png)

Once you save the doc by filling **API Key** and **API Key Secret** it will redirect to Twitter's sign-in page by providing valid Twitter credentials and clicking **Authorize app**, the member approves your application's request to access their member data and interact with Twitter. 

![Twitter Authorize App](/files/twitter-authorize-app.png)
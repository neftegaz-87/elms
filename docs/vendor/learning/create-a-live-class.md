---
title: "Create a Live Class"
space: "Learning"
url: "https://docs.frappe.io/learning/create-a-live-class"
updated: "2026-05-06"
---

Moderators can host a live session from the batch page.

The live class can be done either through Zoom or Google Meet. Once a live class is created, all students who are a part of the batch will receive a calendar invite. All upcoming live classes will be listed on the batch page. Students can join the current session from the batch page itself.

Follow the steps below to start your own live class:

### Step 1: Configure your Google Calendar.

This is required for both Zoom and Google integration. This is what helps us send a calendar invite for the live class. You will also need to enable Google Settings and add the Google Calendar of the moderator. To enable Google Settings, follow the steps mentioned in [this document](https://docs.frappe.io/erpnext/google_calendar).

### Step 2: Connect your integration

You can either use [Zoom](#zoom-integration) or [Google Meet](#google-meet) for this.

#### Zoom Integration

To use this feature, you will have to create a Server-to-server OAuth App from the Zoom App Marketplace. You can follow [this document](https://marketplace.zoom.us/docs/guides/build/server-to-server-oauth-app/) for the same. Creating a Server-to-Server OAuth App provides you with an **Account ID**, **Client ID**, and **Client Secret**.



![Screenshot 2024-05-17 at 5.07.25 PM](/files/Screenshot 2024-05-17 at 5.07.25 PM.png)
*Zoom Settings Doctype*



You will then have to enter these values in the **Zoom Settings** DocType. Check out this video for more details.

![](/files/Zoom App.mp4)



For Auto Recording to work, ensure that Automatic Recording is enabled on your Zoom Account.

![Auto Recording](https://docs.frappelms.com/assets/auto-recording.9e7f3f7b.jpg)
*Automatic recording setting in Zoom Account*

Once the details are submitted, the live class gets saved in your Zoom Account as well as the system backend. A calendar invite also gets sent to all the students of the class.

#### Google Meet

To set up your Google Meet live class, after configuring your Google Calendar, follow the steps below

1. Go to  `Settings` -> `Google Meet` -> `+ New`
  ![](/files/image24f5ef.png)
  *New Google Meet Account Setup*
2. Enter your details in the modal

### Step 3: Create your live class

1. Navigate to the batch where you wish to add the live class and configure your `Conferencing Provider`. Fill `Google Meet Account` field for Google and `Zoom Account` field for Zoom.
2. Now, you can simply go to your `Classes` tab in your batch and create your live class
  ![](/files/imaged54fab.png)
  *Create Live Class Modal*


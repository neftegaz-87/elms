---
title: "Frappe CRM <> Exotel"
space: "CRM"
url: "https://docs.frappe.io/crm/exotel"
updated: "2026-09-29"
---

Exotel is a cloud telephony platform that enables businesses to manage voice calls, SMS, and communication workflows without traditional phone hardware. The integration with Frappe CRM combines these communication capabilities with customer relationship management to provide a unified system for handling customer interactions.

## Make call

- **Lead page:** A call button is available in the right section above lead details. Use this button to initiate a call, but ensure the **Mobile No** field in the **Person** section includes the country code.
  ![](/files/PBAkpiy.png)
- **Deal page:** In the **Contacts** section on the right side. You can add multiple contacts and designate a primary contact. The call button will utilize the primary contact's number.
  ![](/files/LKceTy6066660.png)
- **Contact page:** Directly initiate a call by clicking the **Mobile No** displayed below the contact's name.
  ![](/files/9YnXfPgc03eb0.png)

> Make sure to complete your KYC on Exotel before making calls [docs](https://support.exotel.com/support/solutions/articles/110606-trial-accounts-how-do-i-test-outbound-calling-)

## Call pop-up

Upon making or receiving a call, a pop-up window appears displaying:

- Caller name
- Mobile number
- Call status
- Call duration
- Note button
- Task button
- Lead/Deal button
- Action buttons (Close or Minimize)

![](/files/Screenshot%202025-01-20%20at%206.39.27%E2%80%AFPM607878.png)

This window can be minimized, allowing navigation to other screens, while remaining accessible in the far-right corner of the navbar.

![](/files/Screenshot%202025-01-20%20at%206.38.34%E2%80%AFPM.png)

## Take notes & task during a call

While on a call, you can take notes/task using the note/task button. These notes/task are saved in the Call Log for later viewing and editing.

![](/files/Screenshot%202025-01-20%20at%206.32.05%E2%80%AFPM38cf45.png)

![](/files/Screenshot%202025-01-20%20at%206.30.54%E2%80%AFPM2432c4.png)

## Exotel setup

To configure Exotel for use within the CRM, follow these steps:

1. **Exotel Subscription:** Obtain an active Exotel subscription (refer to Exotel's documentation for details).
2. **Exotel Credentials:** From your Exotel account, retrieve your Account SID, Subdomain, API Key, API Token and Exotel Mobile Number (Exophones).
![](/files/Screenshot%202025-01-20%20at%206.51.13%E2%80%AFPM.png)
![](/files/Screenshot%202025-01-20%20at%206.56.49%E2%80%AFPM.png)
3. **Settings**: Click the dropdown menu on the top left logo and select "Settings."
![](/files/LHGhoZR.png)
4. **Telephony Settings:** Navigate to Telephony Settings and enable Exotel. Add your Account SID, Subdomain, API Key, API Token and set Webhook verify token (it can be anything it will be used later in Exotel incoming call flow configuration). You can also enable call recording at this point.
![](/files/Screenshot%202025-01-20%20at%206.27.24%E2%80%AFPM.png)
5. **Telephony Agent:** Go to Telephony Agent (In Desk) and add users (agents) with Exotel mobile number designated for making calls and also personal number(do not forget to mark one number as primary).
  >  Make sure the email is same in both Telephony Agent and Exotel.
  ![](/files/Screenshot%202025-01-20%20at%206.41.03%E2%80%AFPM.png)

## Exotel incoming call flow configuration

For your CRM's API to connect with Exotel, perform the following configurations within Exotel:

1. Login to your Exotel account and go to App Bazar.
2. Create a new "App" for a new flow.
![](/files/Screenshot%202025-01-20%20at%207.02.50%E2%80%AFPM0a6a6d.png)
3. Setup the flow as you wish it to be.
  - [Dial Whom](https://support.exotel.com/support/solutions/articles/3000088074-working-with-connect-applet-dial-whom-)
    - [Passthru](https://support.exotel.com/support/solutions/articles/48283-working-with-passthru-applet)
    - Check the documentation to learn about all the applets in flow builder - [Link](https://developer.exotel.com/applet)
4. Set "Dial Whom" as user group. In user group there can be multiple agents. Incoming call will be redirected to agents in this group in the order they are added.
![](/files/Screenshot%202025-01-20%20at%207.19.44%E2%80%AFPM.png)
![](/files/Screenshot%202025-01-20%20at%207.37.38%E2%80%AFPM.png)
5. You can also set how you want to distribute calls.
![](/files/Screenshot%202025-01-20%20at%207.44.03%E2%80%AFPM.png)
6. In your connect API under "Create popup...", copy and paste URL (Callback API) mentioned below. Here use webhook verify token which was mentioned in **Exotel Setup (point 4)**.
  ```
    https://<yoursitename>/api/method/crm.integrations.exotel.handler.handle_request?key=<webhook-verify-token>
  ```
  ![](/files/Screenshot%202025-01-20%20at%207.08.08%E2%80%AFPM.png)
7. After that add a "Passthru applet" under "After Call Conversation ends" and paste the same URL.  
![](/files/Screenshot%202025-01-20%20at%207.20.05%E2%80%AFPM.png)
  ![](/files/Screenshot%202025-01-20%20at%207.20.46%E2%80%AFPM.png)
  > Note: Make sure to check "Make Passthru Async".
8. Similary, add another "Passthru applet" under "If nobody answers..." section and paste the same URL.  
![](/files/Screenshot%202025-01-20%20at%207.20.14%E2%80%AFPM.png)  
![](/files/Screenshot%202025-01-20%20at%207.24.51%E2%80%AFPM.png)
  > Note: Make sure to check "Make Passthru Async".
9. Save the flow.
10. Now assign this newly created "App" to your ExoPhone from which you receive your business calls.  
![](/files/Screenshot%202025-01-20%20at%207.26.56%E2%80%AFPM.png)

Once this is done, you should see all new incoming calls on your exotel phone number in the "Call Log" list in your CRM instance.

![](/files/Screenshot%202025-01-20%20at%207.30.13%E2%80%AFPM.png)
---
title: "Forms"
space: "CRM"
url: "https://docs.frappe.io/crm/capturing-leads/web-form"
updated: "2026-07-17"
---

Forms in Frappe CRM let you collect Leads or Deals directly from your website or by circulating web forms without writing a single line of code. 

![](/files/image99a4f3.webp)
*A sample form*

## Creating a form

Follow these simple steps to create one:

1. Open **Settings → Forms**. (You'll need the Sales Manager or System Manager role to see this.)
2. Click **New**.
3. Give it a title, choose whether submissions become a **Lead** or a **Deal**, and set the route. This becomes the last part of the form's public URL (`/crm-form/your-route`). The route fills itself in from the title until you edit it directly.
4. Click **Create form**.

![](/files/Screen Recording 2026-07-17 at 3.29.49 PM.mov)

It opens straight into the builder with a starting layout already in place – name, email, and phone for Leads, plus organization name for Deals, so there's something to look at and publish right away.

## Building the layout

The editor is a canvas of sections and columns, all drag-and-drop:

- **Add Section** starts a new labelled group. Click on the title to name it.
- Inside a section, **Add Field** searches every field on the Lead or Deal; you can select and add which you want to show on your form.
- Click a field to expand it and set:
  - **Required** - visitors can't submit without filling it in.
  - **Placeholder** - example text shown inside the empty field.
  - **Description** - helper text under the field.
- Drag the grip on the left of a section or field to reorder it.
- Remove a field with the **×**. Fields the record (Lead or Deal) itself requires (like Status) can't be removed outright — they move to a **Hidden required fields** panel instead, where you set the default value that gets applied automatically on submission. If fields are added to the hidden section, they aren't visible to the audience on the public form.

![](/files/Screen Recording 2026-07-17 at 3.38.06 PM.mov)

## Previewing

Click **Preview** to see the form as a visitor would, fill it out, and check that the success screen shows what you'd expect. Nothing here is actually saved. **Discard** or **Preview again** resets it, and **Edit** takes you back to the canvas.

![](/files/Screen Recording 2026-07-17 at 3.41.11 PM.mov)

## Settings

The Settings tab holds:

- **Route** - the public URL slug.
- **Maps to** - Lead or Deal.
- **Submit button label** -  you can edit this label as per your preference.
- **Success message** - shown after submission if there's no redirect.
- **Redirect URL** - send visitors somewhere else (a thank-you page, say) instead of showing the success message.

![](/files/image8e50bc.webp)
*Settings page in Forms*

## Publishing

Flip **Publish** on in the header to make the form live. It won't publish until every hidden required field has a default set.

Unpublishing doesn't delete anything. It just takes the public page down. As a manager, you can still open the link yourself to preview a draft; everyone else gets a 404 until it's published.

![](/files/Screenshot 2026-07-17 at 3.46.12 PM.webp)
*Enable "Publish" to make your form public*

## Sharing and embedding

Once published, the **Share** tab gives you:

- **Link** - the hosted form's own page, ready to send directly.
- **Embed** - an iframe snippet for dropping into your own site.
- **Allowed domains** - list the sites (one per line) allowed to embed the iframe. Leave it empty, and the embed only works on your CRM's own domain.

![](/files/Screenshot 2026-07-17 at 3.49.53 PM.webp)
*Share tab in Forms*

That's it. Once you have embedded the form in your website, your site visitors can fill it up and a Lead / Deal as configured will get created in your CRM with source = Web Form.

![](/files/Screen Recording 2026-07-17 at 4.15.11 PM.mov)

P.S. In case you want to add more automations and colour to your form like custom CSS, banner images, etc. you can check your form in the desk view by going to Desk -> Web form. Refer to [this link](https://docs.frappe.io/framework/user/en/web-form/customization) for more details.
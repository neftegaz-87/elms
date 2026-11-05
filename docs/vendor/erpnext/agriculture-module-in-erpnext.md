---
title: "Agriculture Module in ERPNext"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/agriculture-module-in-erpnext"
updated: "2026-07-04"
---

## Overview

The Agriculture module was created as an ERPNext domain app for farms and agriculture-focused organizations. It is intended to help users record crops and land, track agriculture activities, and maintain field-related observations such as plant, soil, water, weather, disease, and fertilizer information.

The app is available as a separate open-source repository under the Frappe organization. However, it should be evaluated carefully before use on a new ERPNext site.

## Maintenance And Compatibility Status

**Important:** The Agriculture app does not appear to be actively maintained at the same level as ERPNext core and other actively developed Frappe apps. The repository has no published releases, and users should not assume that it is compatible with the latest ERPNext or Frappe Framework versions.

If you plan to use it, test it on a staging site first and confirm compatibility with your exact ERPNext, Frappe Framework, and Python versions. For production use, be prepared to review the code, apply fixes, or maintain a fork if required.

## GitHub Repository

Source code: [github.com/frappe/agriculture](https://github.com/frappe/agriculture)

The repository describes the app as the Agriculture Domain for ERPNext.

## Basic Features

- **Crop records:** Maintain information related to crops grown by the organization.
- **Land records:** Track agricultural land or field information.
- **Plant analytics:** Record plant-related observations and measurements.
- **Soil, water, and weather tracking:** Maintain field-level environmental observations that may affect crop planning and operations.
- **Disease tracking:** Record crop or plant disease information for reference and follow-up.
- **Fertilizer tracking:** Track fertilizer-related information as part of agriculture operations.

## When To Use It

Consider this app only if you specifically need the agriculture domain objects and are comfortable validating or maintaining the app yourself. It may be useful as a starting point for custom agriculture workflows, but it should not be treated as a plug-and-play module for current ERPNext versions without testing.

## Installation

The repository README shows the standard Frappe app installation flow:

```
bench get-app agriculture
bench --site your-site-name install-app agriculture
```

Run these commands only on a development or staging bench until compatibility is confirmed.

## Recommended Approach

- Check the repository activity, open issues, and pull requests before installation.
- Install the app on a test site first.
- Run migrations and basic workflows before using it with real data.
- Confirm whether the DocTypes and reports meet your operational needs.
- If the app does not work with your ERPNext version, consider using it as a reference for a custom app instead of installing it directly in production.

## Related Link

- [Frappe Agriculture on GitHub](https://github.com/frappe/agriculture)
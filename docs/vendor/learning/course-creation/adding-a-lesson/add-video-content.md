---
title: "Video Integration (Cloudflare, Vimeo, YouTube, etc.)"
space: "Learning"
url: "https://docs.frappe.io/learning/course-creation/adding-a-lesson/add-video-content"
updated: "2026-04-08"
---

Frappe Learning allows you to embed videos in lessons using popular video hosting platforms. You don’t need to upload videos directly into Frappe Learning, simply **copy the video URL** from your preferred provider and **paste it into the Lesson Editor**.

Frappe Learning automatically detects the video source and embeds it for learners.

---

## Supported Video Platforms

### 1. YouTube

YouTube videos can be embedded using the standard watch URL.

#### Supported URL format

```
https://www.youtube.com/watch?v=<video-id>
```

#### Example

```
https://www.youtube.com/watch?v=SLNSSz41v_o
```

---

### 2. Vimeo

Vimeo videos are supported using the video URL.

#### Supported URL format

```
https://vimeo.com/<video-id>
```

#### Example

```
https://vimeo.com/825334862
```

---

### 3. Cloudflare Stream

Cloudflare Stream provides secure video hosting with adaptive streaming.

#### Supported URL format

```
https://customer-<account-id>.cloudflarestream.com/<video-id>/watch
```

#### Example

```
https://customer-f33zs165nr7gyfy4.cloudflarestream.com/6b9e68b07dfee8cc2d116e4c51d6a957/watch
```

---

### 4. Bunny Stream

Bunny Stream allows fast, global video delivery with built-in analytics.

#### Supported URL format

```
https://iframe.mediadelivery.net/play/<library-id>/<video-id>
```

#### Example

```
https://iframe.mediadelivery.net/play/579970/54b3e5a1-cf95-4f88-96d3-8387d93dc2f2
```

---

## Important Notes

- Paste **only the video URL**, not iframe embed code
- The URL must match one of the supported formats above
- Video privacy, access control, and streaming limits are managed by the video provider


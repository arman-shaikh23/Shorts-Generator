# Project: Property Video → Shorts Generator

**Company:** Groovy Technoweb
**Type:** Full-Stack AI Agent Web App

---

## What You're Building

A web app where someone pastes a property video URL, and the app automatically finds the best moments, writes a social media script for each, cuts them into vertical clips, and gives back ready-to-upload short-form video files.

No platform upload. The output is downloadable `.mp4` files — the user uploads manually to Instagram Reels, YouTube Shorts, or wherever.

---

## How It Works (Agent Flow)

```
User pastes video URL + property name
        ↓
App downloads the video
        ↓
Uploads to Gemini Files API → waits for processing
        ↓
Gemini analyzes the footage
→ returns 2–3 best segments with timestamps + why each works for social media
        ↓
Gemini generates for each segment:
→ caption/script  ·  suggested title  ·  hashtags
        ↓
ffmpeg cuts each segment · converts to 9:16 vertical
        ↓
Output: downloadable .mp4 files + scripts shown in UI
```

---

## Input

| Field | Example |
|---|---|
| Video URL | Dropbox direct file link |
| Property name | Ambrose — Luxury Apartments, Dallas TX |

> **Note:** The Dropbox links shared with you are folder links. When testing, open the folder, click a specific video file, and copy the direct download link for that file. Add `?dl=1` at the end to force download.

---

## Output

**Per video: minimum 2 clips, maximum 3 clips**

Each clip delivers:
- `.mp4` file — 9:16 vertical format, 15–60 seconds — download button in UI
- Caption / spoken script
- Suggested title
- Hashtags

---

## Tech Stack — Everything Free

| What | Tool | How to get it |
|---|---|---|
| Video analysis + script generation | Gemini API | `aistudio.google.com` → sign in → Create API key → free, no card |
| Video cutting + 9:16 conversion | ffmpeg | `sudo apt install ffmpeg` or `brew install ffmpeg` |
| Backend | FastAPI (Python) | `pip install fastapi` |
| Frontend | React or Next.js | your choice |
| Deployment | Railway | `railway.app` → free $5/month credit |

**Total cost: ₹0**

---

## One Thing to Read Before Writing Any Code

Gemini cannot receive a large video file directly in a prompt. You must use the **Gemini Files API**:

1. Upload the video file to Google using the Files API
2. Poll until the file status is `ACTIVE`
3. Pass the returned `file_uri` in your Gemini prompt

If you skip this and try to send the video inline, it will fail on any file larger than a few MB. Read the Gemini Files API documentation before touching the backend.

Also: processing takes 3–8 minutes per video. A standard HTTP request will timeout waiting that long. Use **Server-Sent Events (SSE)** to stream live progress to the frontend — you already built this in AgentForge, same pattern.

---

## Frontend

One page. Two sections only.

**Input section**
- Video URL field
- Property name field
- Submit button

**Output section** — appears after processing completes
- Live progress indicator showing the current agent step
- 2–3 result cards, each with: inline video preview · script text · download button

No extra pages. No settings. No dashboard. Input → output, that is it.

---

## Sample Videos for Testing

**AMC — Ambrose**
```
https://www.dropbox.com/scl/fo/7nfq4471lgbptsn8u78po/AAMJeN_JEDyf0rPmIvVvf6w?rlkey=mfnjdoqkgblbj2xnuc6lsmkxg&st=ox5gcjfn&dl=0
```

**Essex — Century Towers**
```
https://www.dropbox.com/scl/fo/0kdgy3apcbupkmieqoyi7/AKV4crpiFHk0WZGEFuUhL4U?rlkey=nozserstjgiagq8o4vlxy0kyz&st=k1wdpvih&dl=0
```

**Windsor — South Park by Windsor**
```
https://www.dropbox.com/scl/fo/kpqyt7tsnvrb60pp6tbmq/AFRBtr9oE7q-WyW2Ku0nU-U?rlkey=7gy6f0kobutoyqcuh12p9vcze&st=1xlfrjd5&dl=0
```

Test with one video during development. Test all three before final submission.

---

## Deliverables

- [ ] App deployed and live on Railway — share the public URL
- [ ] Tested against at least one real video from the links above
- [ ] GitHub repo — public, clean commit history
- [ ] `README.md` — setup steps, environment variables, how to run locally
- [ ] `CHANGELOG.md`
- [ ] `PROMPTS.md` — every Gemini prompt you wrote, what you changed, and why

---

## Done When

1. Paste a Dropbox video link into the app
2. App processes it end to end without you touching anything
3. 2–3 vertical `.mp4` clips appear with scripts and download buttons
4. App is live on Railway at a public URL
5. All files pushed to GitHub

---
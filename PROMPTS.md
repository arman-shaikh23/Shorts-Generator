# Prompts Documentation

> **Note:** If you experience issues with video upload to Gemini due to missing files, check the backend server logs. Deep debugging has been added to verify Dropbox video downloads (e.g. tracking URL redirects, HTTP status codes, and `Content-Type`).
> **Note:** If you experience issues with video upload to Gemini due to missing files, check the backend server logs. Deep debugging has been added to verify Dropbox video downloads (e.g. tracking URL redirects, HTTP status codes, and `Content-Type`).
> **Compatibility:** FFmpeg is executed synchronously via `asyncio.to_thread` instead of `asyncio.create_subprocess_exec` to avoid `NotImplementedError` on Windows (Python 3.13). High-end Sony XAVC camera footage is explicitly normalized to `yuv420p` and stripped of proprietary metadata streams (`rtmd`) so that Gemini can process the resulting preview flawlessly.
> **Routing Precedence:** Ensure `StaticFiles` is never mounted directly at the root `app.mount("/", ...)` before API routes, as this causes wildcard shadowing (yielding 404s for the API). Mount static assets cleanly under a subpath or define specific wildcard handlers.

## Prompt 1: Multi-Video Analysis & Content Generation

### The Prompt
```text
Property: '{property_name}'
Goal: Build ONE {style} style vertical reel targeting exactly {duration} duration.
You have been provided N video clips (indices 0 to N-1).

TASKS:
1. Detect Property Type (apartment, house, villa, penthouse).
2. Classify every clip (e.g. exterior, entrance, living_room, kitchen, bedroom, pool, drone_view, etc) and score its quality (0-100). Reject blurry, bad lighting, or duplicate footage.
3. Select ONLY the strongest 8-12 clips.
4. Smart Reel Ordering:
   - If House/Villa: Exterior -> Entrance -> Living Room -> Dining -> Kitchen -> Bedroom -> Bathroom -> Balcony -> Backyard -> Pool -> Closing.
   - If Apartment/Penthouse: Building Exterior -> Entrance -> Living Room -> Dining -> Kitchen -> Bedroom -> Bathroom -> Balcony -> Amenities -> View -> Closing.
   NEVER use upload order. Always sequence based on the property type logic above.
5. Provide a highly engaging social media hook, a 4-5 line description of the property, and hashtags.
```

### Context & Reasoning
- **Multi-Video Context**: The prompt receives a list of videos as Parts array before the prompt string. `video_index` maps decisions back to the original source videos.
- **Hook Strategy**: Generating a hook explicitly increases viral retention rates.
- **Flash Model**: Switched from `gemini-2.5-pro` to `gemini-2.5-flash` for 3-5x faster inference. Quality is comparable for structured extraction tasks.
- **Lower Temperature (0.5)**: Reduces generation randomness, leading to faster convergence and more consistent outputs.
- **Preview-Based Analysis**: A 480p preview is uploaded instead of the full-resolution video. This reduces upload time by 60-80% and Gemini processing time significantly, since the AI only needs to understand scene content (not pixel-perfect detail).

### Changes from v1
| Aspect | v1 (Original) | v2 (Optimized) |
|---|---|---|
| Prompt length | ~15 lines | ~5 lines |
| Model | `gemini-2.5-pro` | `gemini-2.5-flash` |
| Temperature | 0.7 | 0.5 |
| API calls | Conceptually 2 (upload, then generate) | 1 upload + 1 generate (unchanged structure, but tighter) |
| Video uploaded | Full resolution | 480p preview |
| Polling strategy | Fixed 5s interval | Exponential backoff 2s → 10s cap |

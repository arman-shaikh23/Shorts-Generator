# Prompts Documentation

> **Note:** If you experience issues with video upload to Gemini due to missing files, check the backend server logs. Deep debugging has been added to verify Dropbox video downloads (e.g. tracking URL redirects, HTTP status codes, and `Content-Type`).
> **Note:** If you experience issues with video upload to Gemini due to missing files, check the backend server logs. Deep debugging has been added to verify Dropbox video downloads (e.g. tracking URL redirects, HTTP status codes, and `Content-Type`).
> **Compatibility:** FFmpeg is executed synchronously via `asyncio.to_thread` instead of `asyncio.create_subprocess_exec` to avoid `NotImplementedError` on Windows (Python 3.13). High-end Sony XAVC camera footage is explicitly normalized to `yuv420p` and stripped of proprietary metadata streams (`rtmd`) so that Gemini can process the resulting preview flawlessly.
> **Routing Precedence:** Ensure `StaticFiles` is never mounted directly at the root `app.mount("/", ...)` before API routes, as this causes wildcard shadowing (yielding 404s for the API). Mount static assets cleanly under a subpath or define specific wildcard handlers.

## Prompt 1: Multi-Video Analysis & Content Generation

### The Prompt (Phase 1: Analysis)
```text
Property: '{property_name}'
Goal: Analyze these {N} video clips to propose a logical Property Story Timeline.

TASKS:
1. Detect Property Type (apartment, house, villa, penthouse).
2. Classify every clip (e.g. exterior, entrance, living_room, kitchen, bedroom, pool, drone_view, etc) and score its quality (0-100). Reject blurry, bad lighting, or duplicate footage.
3. Select ONLY the strongest 8-12 clips.
4. Smart Reel Ordering (Default Proposal):
   - If House/Villa: Exterior -> Entrance -> Living Room -> Dining -> Kitchen -> Bedroom -> Bathroom -> Balcony -> Backyard -> Pool -> Closing.
   - If Apartment/Penthouse: Building Exterior -> Entrance -> Living Room -> Dining -> Kitchen -> Bedroom -> Bathroom -> Balcony -> Amenities -> View -> Closing.
```

### The Prompt (Phase 2: Generation / Variations / Re-sequencing)
```text
Goal: Generate 3 distinct Reel Variations (Luxury, Instagram Viral, Realtor Style) using the provided Pool of Scenes.
For each variation:
1. Write a hook, description, and hashtags that match the style.
2. Create a custom sequence of video clips by selecting and ordering from the pool of scenes. You can reuse clips, drop clips, or completely change the order to fit the vibe!
   - Luxury: Slower paced, focus on beautiful wide shots, pools, and main rooms.
   - Instagram Viral: Fast-paced, start with the most dramatic/unique shot as the hook, quick cuts.
   - Realtor Style: Traditional logical walkthrough (Exterior -> Entrance -> Living -> Kitchen).
```

### Context & Reasoning
- **Phase Split**: The AI pipeline is now split. Phase 1 merely analyzes the clips and returns a proposed array of Room Blocks. This allows the user to drag-and-drop the timeline in the UI. Phase 2 takes the *confirmed* timeline and generates the 3 script/hook variations before triggering FFmpeg.
- **Multi-Video Context**: The prompt receives a list of videos as Parts array before the prompt string. `video_index` maps decisions back to the original source videos.
- **Hook Strategy**: Generating a hook explicitly increases viral retention rates.
- **Flash Model**: Switched from `gemini-2.5-pro` to `gemini-2.5-flash` for 3-5x faster inference. Quality is comparable for structured extraction tasks.
- **Lower Temperature (0.5)**: Reduces generation randomness, leading to faster convergence and more consistent outputs.
- **Preview-Based Analysis**: A 480p preview is uploaded instead of the full-resolution video. This reduces upload time by 60-80% and Gemini processing time significantly, since the AI only needs to understand scene content (not pixel-perfect detail).
- **Multi-Format Architecture**: Instead of hardcoding 9:16 vertical outputs, the pipeline now supports dynamic Aspect Ratios (16:9, 1:1, 9:16) passed from the frontend to the FFmpeg rendering layer, ensuring clips fit specific platforms (YouTube, Reels, Instagram Square).

### Future Roadmap: AI Director Chat (V9.0)
Currently, the V9.0 frontend features a sliding **AI Director Chat Panel** where users can type natural language instructions (e.g. "Focus more on the luxury amenities" or "Make the pacing faster"). In future iterations, this chat history should be passed dynamically into the Phase 2 Generation Prompt array to adjust the final script and pacing overrides on the fly.

### V9.1 Updates: Semantic Selection Engine
- **Full Video Analysis**: Gemini is strictly instructed to analyze entire video durations to pull out multiple distinct clips from long footage, rather than just taking a random 5-second chunk.
- **Semantic Deduplication**: Instead of a separate Python vector-embedding pipeline, we leverage Gemini-2.5-Pro's 2M token context window to actively find and eliminate visually similar clips within the prompt itself, returning only the version with the highest `visual_quality_score`.
- **Advanced Grading Schema**: Every selected clip now receives AI-graded scores for `confidence` (>85% enforced), `lighting`, `stability`, `luxury_appeal`, and `engagement`.

### Changes from v1
| Aspect | v1 (Original) | v2 (Optimized) |
|---|---|---|
| Prompt length | ~15 lines | ~5 lines |
| Model | `gemini-2.5-pro` | `gemini-2.5-flash` |
| Temperature | 0.7 | 0.5 |
| API calls | Conceptually 2 (upload, then generate) | 1 upload + 1 generate (unchanged structure, but tighter) |
| Video uploaded | Full resolution | 480p preview |
| Polling strategy | Fixed 5s interval | Exponential backoff 2s → 10s cap |

# Prompts Documentation

## Prompt 0: ReelForge Quality V2 (Stability + Story Fallback)

### The Prompt
```text
Property: '{property_name}'
Total Uploaded Clips: {clip_count}
Target Style: {style}

You are ReelForge V2 quality assistant. Follow these strict rules:

1) DO NOT remove clips unless they are true duplicates or unusable.
2) Preserve existing production behavior when confidence is low.
3) Return only JSON.

For each selected clip, provide:
- scene_type
- confidence_score (0-100)
- camera_motion
- camera_direction
- shot_size
- start
- end

Narrative order preference:
Exterior/Drone -> Entrance -> Living Room -> Dining -> Kitchen -> Bedroom -> Bathroom -> Balcony -> Amenities -> Exit

Transition quality rules:
- Avoid abrupt jumps (Bathroom -> Drone -> Kitchen).
- Prefer smooth spatial progression.
- Do not repeat identical room/camera perspective when a better alternative exists.

If scene confidence is low (<55), keep conservative ordering and do not force aggressive reordering.
```

### Why This Prompt Exists
- Improves sequence quality while preserving fallback safety.
- Produces confidence data required by feature-flagged V2 ordering logic.
- Keeps compatibility with existing timeline optimizer and rendering pipeline.

## Prompt 0.1: Connection Pooling and Throughput Guardrails

### The Prompt
```text
You are a backend performance engineer for ReelForge.
Optimize throughput with connection pooling and without changing API contracts.

Rules:
1) Reuse one MongoDB client for app lifecycle.
2) Reuse one outbound HTTP client for app lifecycle.
3) Do not create per-request network clients unless isolation is required.
4) Configure bounded pool limits to prevent resource exhaustion.
5) Add startup/shutdown hooks for clean init and cleanup.
6) Keep fallback-safe defaults in env template.
7) Add logs for pool configuration at startup.
8) Verify no regressions via full test suite.

Deliver:
- pool settings added to config
- lifecycle wiring
- migration/rollback notes
- validation results
```

### Why This Prompt Exists
- Prevents repeated TCP/TLS setup overhead.
- Improves request latency and upload stability under concurrency.
- Reduces file download bottlenecks during parallel processing.
- Keeps production behavior stable while scaling traffic safely.

## Prompt 0.2: Pool Observability and Diagnostics Endpoint

### The Prompt
```text
You are operating ReelForge in production with pooled MongoDB and pooled outbound HTTP.
Add observability without changing API contracts or removing existing features.

Rules:
1) Collect pool telemetry as additive metadata only.
2) Track HTTP request latency, timeout classes, and error counters.
3) Track Mongo connect/ping latency plus checkout wait/timeout indicators.
4) Add a read-only diagnostics endpoint at /api/v1/health/pools.
5) Do not expose secrets, credentials, or raw connection strings in diagnostics.
6) Keep endpoint backward compatible and non-breaking.
7) Add tests for diagnostics payload shape and metrics behavior.
8) Keep rollback simple: disabling new usage should not affect legacy flow.
```

### Why This Prompt Exists
- Makes pool saturation visible before it becomes a user-facing outage.
- Gives fast feedback during load testing and production tuning.
- Improves incident response with concrete latency and timeout counters.
- Preserves existing functionality because diagnostics are additive and read-only.

## Prompt 0.3: Pagination Standardization and Backward-Compatible Rollout

### The Prompt
```text
You are a backend/frontend scalability engineer for ReelForge.
Implement pagination for list endpoints without breaking existing workflows.

Rules:
1) Keep existing response keys and behavior valid for legacy clients.
2) Add pagination metadata fields additively: total, page, limit, skip, pages, has_next, has_prev.
3) Support both page-based and skip-based access where practical.
4) Clamp limits to safe bounds to prevent oversized queries.
5) Keep uploads endpoint backward compatible: full-list mode remains available by default.
6) Update frontend list screens to actively use paginated requests and navigation controls.
7) Add tests for pagination helpers and metadata behavior.
8) Update docs and changelog with migration and rollback guidance.
```

### Why This Prompt Exists
- Prevents large payload bottlenecks as project and history data grows.
- Improves perceived speed through smaller responses and explicit navigation.
- Reduces backend/database load while preserving legacy compatibility.
- Creates a safe path to future cursor-based pagination if scale increases.

## Prompt 0.4: Redis Cache-Aside with TTL and Versioned Invalidation

### The Prompt
```text
You are a production backend engineer for ReelForge.
Implement Redis caching with cache-aside pattern, TTL, and safe invalidation.

Rules:
1) Keep API contracts unchanged and preserve fallback behavior.
2) Feature-flag Redis (`ENABLE_REDIS_CACHE`) with default OFF.
3) Apply cache-aside on read-heavy endpoints only.
4) Use endpoint-specific TTL values, configurable by env.
5) Use versioned namespace invalidation (INCR keys), not wildcard scans.
6) On Redis failure, fall back to MongoDB without breaking requests.
7) Invalidate relevant namespaces on project/upload/generation mutations.
8) Add tests for cache set/get, TTL behavior, and version bump invalidation.
9) Update README and CHANGELOG with rollout and rollback instructions.
```

### Why This Prompt Exists
- Reduces repeated MongoDB reads for high-traffic list/detail endpoints.
- Improves response latency while keeping source-of-truth in MongoDB.
- Provides deterministic invalidation at O(1) cost.
- Maintains production safety by default-disabled rollout and graceful fallback.

## Prompt 0.5: Streaming Large Uploads at API Boundaries

### The Prompt
```text
You are a production backend engineer for ReelForge.
Refactor upload endpoints so large files are streamed to disk and never read fully into memory.

Rules:
1) Replace full-file reads (`await file.read()`) with chunked streaming loops.
2) Write chunks incrementally to disk with async file I/O.
3) Enforce max upload sizes for video and music endpoints.
4) Keep single-video upload cap at 10GB (`MAX_VIDEO_UPLOAD_BYTES=10737418240`) unless explicitly changed.
5) Reject non-video uploads on `/uploads/file` (including `.jpg/.jpeg/.png`) with `415`.
6) Validate uploaded media is an actual video stream (not just file extension).
7) Return `413` when size limits are exceeded.
8) Clean up partial files on any error path.
9) Keep API contracts backward compatible where possible.
10) Make chunk size and limits configurable in environment settings.
11) Update README and CHANGELOG with operational guidance.
```

### Why This Prompt Exists
- Prevents memory pressure and process instability during large uploads.
- Improves throughput under concurrent uploads.
- Makes upload failure behavior deterministic and safe (no partial file leftovers).
- Prevents incorrect media types (like images) from entering the video pipeline.
- Supports production tuning via environment-based chunk and size controls.

## Prompt 0.6: MongoDB Indexing for Hot Query Paths

### The Prompt
```text
You are a production backend engineer for ReelForge.
Add database indexing for real query patterns without changing API contracts.

Rules:
1) Identify high-frequency query filters and sort fields from API and worker code.
2) Create indexes during startup in the Mongo connection bootstrap path.
3) Cover auth lookups, project/history pagination sorts, upload ordering/status flows, and token lifecycle operations.
4) Add TTL index for refresh token expiration cleanup.
5) Keep index creation idempotent and safe across restarts.
6) Log index creation outcomes for observability.
7) Keep startup resilient: index failures should be visible in logs.
8) Update README and CHANGELOG with index strategy and operational notes.
```

### Why This Prompt Exists
- Reduces query latency by avoiding collection scans on list and worker paths.
- Improves scalability for user/project growth without API contract changes.
- Keeps auth/session operations predictable under load.
- Adds automatic cleanup for expired refresh tokens through TTL indexing.

## Prompt 0.7: Index Diagnostics Endpoint (Read-Only Health Visibility)

### The Prompt
```text
You are a production backend engineer for ReelForge.
Add a read-only health endpoint that reports Mongo index readiness.

Rules:
1) Add endpoint at `/api/v1/health/indexes`.
2) Return expected indexes, actual indexes, and missing indexes per critical collection.
3) Report aggregate status (`ok` or `degraded`) and total missing count.
4) Do not expose secrets, credentials, or connection URIs.
5) Keep endpoint additive and backward compatible.
6) Add API test coverage for payload shape and core collection presence.
7) Update README and CHANGELOG with usage notes.
```

### Why This Prompt Exists
- Makes index drift visible in environments after migrations or manual DB changes.
- Speeds up production validation by avoiding manual shell checks.
- Helps verify startup index bootstrap behavior without direct database access.

## Prompt 0.8: Idempotency for Write Operations

### The Prompt
```text
You are a production backend engineer for ReelForge.
Implement idempotency for write operations to make client retries safe.

Rules:
1) Support `Idempotency-Key` header (and optional alias `X-Idempotency-Key`).
2) Scope idempotency by authenticated user + endpoint + key.
3) Hash request payload and reject same key used with different payload (`409`).
4) Persist idempotency state in Mongo with statuses (`IN_PROGRESS`, `COMPLETED`, `FAILED`).
5) Replay stored response when same key + same payload is retried.
6) Add TTL cleanup for stale idempotency records.
7) Keep behavior backward compatible when no idempotency key is provided.
8) Apply first to high-impact project/uploads mutations; include multipart upload endpoints using safe metadata-based hashing when full body hashing is impractical.
9) Update docs and changelog with client usage guidance.
```

### Why This Prompt Exists
- Prevents duplicate writes caused by retries/timeouts.
- Makes API behavior deterministic under unstable network conditions.
- Protects data consistency for create/update/delete flows.
- Preserves existing clients by making idempotency opt-in.

## Prompt 0.9: YouTube URL Ingestion for Home-Tour Sources

### The Prompt
```text
You are a production backend engineer for ReelForge.
Add safe support for YouTube URL uploads in the existing `/uploads` flow.

Rules:
1) Keep `POST /api/v1/projects/{project_id}/uploads` backward compatible for existing direct media URLs.
2) Detect YouTube hosts (`youtube.com`, `youtu.be`) and download media using `yt-dlp`.
3) Enforce single-video behavior (`noplaylist=true`) for YouTube URLs.
4) Keep worker pipeline unchanged after download (dedup -> preview -> analyze).
5) Add clear errors for invalid URL schemes, unsupported playlist links, or downloader failures.
6) Add optional env controls:
   - `YTDLP_COOKIES_FILE` for restricted-content sessions.
   - `YOUTUBE_MAX_DURATION_SEC` for server-side duration caps.
7) Update frontend upload-copy text to explicitly mention YouTube URL support.
8) Update README and CHANGELOG with operational notes and constraints.
```

### Why This Prompt Exists
- Users often have one complete home-tour video on YouTube instead of local raw clips.
- Native YouTube ingestion removes manual download/upload friction.
- Keeping the downstream pipeline unchanged preserves quality and stability guarantees.

## Prompt 1: ReelForge Duration-First Story Engine (v5)

### The Prompt
```text
Property: '{property_name}'
Total Uploaded Clips: {clip_count} (indices 0 to {clip_count - 1})

═══ 1. DURATION-FIRST GENERATION & BUDGET ALGORITHM ═══
DO NOT select clips first.
Instead, use: {dynamic_duration}
Add unique clips until the duration budget is reached.
Extract 3-5 seconds from the high-quality portions of each clip.
Example: Clip A (4 sec) + Clip B (3 sec) + Clip C (5 sec). Continue until target duration is achieved.

[Platform Rules injected here (Shorts Hook/Main/Closing OR YouTube Hook/Main/Closing)]

═══ 2. PROPERTY STORY ENGINE ═══
Create a logical property walkthrough.
Priority order: Drone -> Exterior -> Entrance -> Lobby -> Living Room -> Dining -> Kitchen -> Bedroom -> Bathroom -> Balcony -> Pool -> Gym -> Garden -> Parking -> Closing Drone.
THIS ORDER SHOULD OVERRIDE CLIP SCORE.
Bathroom, Parking, or Utility areas should NEVER be the opening shot.

═══ 3. OPENING SHOT ENGINE ═══
Opening shot candidates: Drone, Exterior, Pool, Luxury Living Room.
Select the strongest visual. Opening duration: 5–7 sec. Goal: Immediately impress the viewer.

═══ 4. COVERAGE-FIRST SELECTION ═══
Use maximum unique footage. Goal: 80–95% coverage.
Only remove: Exact duplicates, Near duplicates >95%

═══ 5. CATEGORY COVERAGE RULE ═══
Ensure representation of all major categories. Never allow one category to dominate.

═══ 6. STORYBOARD VALIDATOR ═══
Before outputting, verify:
✓ Strong opening shot (Not a bathroom/parking)
✓ Correct chronological property order
✓ No repeated footage / No duplicate clips
✓ Duration within target budget
✓ Coverage requirements met
If validation fails, silently rebuild the storyboard before responding.
```

### Key Changes from v4 → v5

| Aspect | v4 | v5 (Duration-First Engine) |
|---|---|---|
| Sequence Logic | Strict 5-Stage | **Strict 15-Stage Chronological Priority (Overrides visual score)** |
| Selection Method | Pick 80% clips, then calculate time | **Set Target Budget (e.g. 60s), then add clips until filled** |
| Platform Pacing | None | **Strict Timeline Structures (e.g. Shorts: 0-5s Hook, 5-20s Main, etc)** |
| Shorts Cap | 12 clips maximum | **Absolute 60s hard limit via Budget summation** |
| YouTube Floor | N/A | **Minimum 60s, scales intelligently up to 240s based on raw footage** |

### Reasoning Behind Each Decision

- **Duration-First Focus**: Users complained Shorts were sometimes running over 60s or YouTube videos were rendering at just 30s. Instructing the AI to view selection as a "Duration Budget" perfectly aligns its output with the target platform's required pacing.
- **Score Override**: The AI used to favor 98-score Bathroom clips over 80-score Drone clips for the opening shot. The prompt explicitly forces Sequence logic to override raw Quality Score logic.
- **Dynamic Duration**: Instead of forcing all reels into 30 seconds, we scale: 5 clips → 20-40s, 30 clips → 90-180s. This respects the user's footage volume.
- **clip_duration_sec**: Each clip gets 3-6 seconds of screen time based on quality, replacing the old 1-second-per-clip approach.
- **Property Tour Sequencing**: 18-category ordering ensures logical flow: Drone → Exterior → Entrance → rooms → amenities → closing.
- **Coverage Protection**: The AI is instructed to never remove the only clip representing a category (e.g., the only Gym shot).
- **Post-Processing Validation**: After Gemini returns, the backend recalculates coverage percentage and logs a warning if it drops below 70%.

## Prompt 2: ReelForge Story Engine (v6) - Diversity & Roles

### The Prompt
```text
Property: '{property_name}'
Total Uploaded Clips: {clip_count} (indices 0 to {clip_count - 1})

═══ 1. DURATION-FIRST GENERATION & BUDGET ALGORITHM ═══
DO NOT select clips first. Instead, use: {dynamic_duration}
Add unique clips until the duration budget is reached.
Extract 3-5 seconds from the high-quality portions of each clip.

[Platform Rules injected here]

═══ 2. SCENE ROLE CLASSIFICATION & STORY BUILDER ═══
Assign every selected clip a structural ROLE:
OPENING, PROPERTY_SIGN, EXTERIOR, LOBBY, LIVING_ROOM, DINING, KITCHEN, BEDROOM, BATHROOM, AMENITY, POOL, GYM, PARKING, CLOSING.

Build the reel strictly using this Role order:
OPENING -> PROPERTY_SIGN -> LOBBY -> LIVING_ROOM -> DINING -> KITCHEN -> BEDROOM -> BATHROOM -> AMENITIES -> POOL -> GYM -> CLOSING
THIS ORDER MUST OVERRIDE CLIP SCORE.

═══ 3. OPENING SCENE RULES ═══
Opening candidates: Drone, Exterior, Luxury Living Area.
NEVER use: Bathroom, Parking, Utility Room.
Opening duration: 5–7 seconds.

═══ 4. CLOSING SCENE & DIVERSITY RULES ═══
Closing candidates: Exterior, Pool, Night View, Drone Exit.
NEVER reuse the opening scene.
RULE: opening_scene_id != closing_scene_id (The opening video_index MUST NOT match the closing video_index).
If opening uses Video A, you MUST use Video B for the closing. Avoid using the same source clip twice.

═══ 5. REUSE PROTECTION ═══
Track scene_id and video_id internally.
PREVENT the same temporal segment of a video from appearing twice. Use maximum unique footage.
Only remove: Exact duplicates, Near duplicates >95%.

═══ 6. CATEGORY COVERAGE RULE ═══
Never allow one category to dominate the reel.

═══ 7. STORYBOARD VALIDATOR ═══
Before outputting, verify:
✓ Strong opening (Not bathroom/parking)
✓ Logical walkthrough order based on Roles
✓ No repeated opening shot
✓ No repeated closing shot (Opening video_index != Closing video_index)
✓ Amenities appear near the end
✓ Smooth category transitions
If validation fails, silently rebuild the storyboard before responding.
```

### Key Changes from v5 → v6

| Aspect | v5 | v6 (Diversity & Roles) |
|---|---|---|
| Classification | General scene types | **Strict Structural Roles (OPENING, CLOSING, LOBBY)** |
| Sequence Logic | Loose 15-stage | **Strict Role-based 12-stage builder** |
| Closing Shot | Static | **opening_scene_id != closing_scene_id (Forced diversity)** |
| Reuse Protection | Implicit | **Explicit Tracking of scene_id and video_id** |

### Reasoning Behind Each Decision

- **opening_scene_id != closing_scene_id**: Users noticed reels occasionally started and ended with the exact same clip, which ruined the pacing. This explicit constraint forces Gemini to pick different video sources for the start and end.
- **Scene Role Classification**: Instead of just tagging a clip as "Pool", tagging it as "CLOSING" explicitly commands the LLM to place it at the end of the timeline sequence, solving the random ordering issue.

## Prompt 3: Variation Generation (Updated)

### The Prompt
```text
Property: '{property_name}'
Goal: Generate 3 distinct Reel Variations using the Pool of Scenes.
- Luxury: Use as many clips as possible, slower paced
- Instagram Viral: Fast-paced, aggressive quick-cuts allowed
- Realtor Style: Traditional walkthrough, use nearly all clips
```

### Reasoning
- The Luxury and Realtor variations now explicitly keep most clips, maintaining high coverage. Only the Viral style allows dropping clips for fast pacing.

## Prompt 4: ReelForge Story Engine (v7) - Unlimited Duration & Loop Closure

### The Prompt
```text
Property: '{property_name}'
Total Uploaded Clips: {clip_count} (indices 0 to {clip_count - 1})

═══ 1. MAXIMUM COVERAGE (CRITICAL) ═══
DO NOT stop selecting clips to fit a time budget. Use: TARGET DURATION: UNLIMITED. Use ALL unique, non-duplicate clips. The final video will be exactly as long as necessary to show every important clip.
You MUST select ALL unique, non-duplicate clips provided in the pool.
EACH CLIP must have clip_duration_sec between 8-15 seconds.
Your total_selected_duration_sec MUST equal the sum of all clip_duration_sec for every unique clip in the pool.

[Platform Rules injected here]

═══ 8. STORYBOARD VALIDATOR (RUN BEFORE OUTPUT) ═══
Verify EACH of these or silently rebuild:
✓ Strong opening (scene_type is drone/aerial/exterior/living_room/pool, NOT bathroom/parking)
✓ Logical walkthrough order based on Roles (not visual score)
✓ No repeated footage / No duplicate clips
✓ Uses ALL unique non-duplicate clips available
✓ Opening video_index != Closing video_index
✓ Amenities appear near the end
✓ Smooth category transitions (don't jump from kitchen back to exterior)
If ANY validation fails, silently rebuild the storyboard before responding.
```

### Key Changes from v6 → v7

| Aspect | v6 (Roles) | v7 (Unlimited Duration) |
|---|---|---|
| Target Duration | Strict budget (e.g. 60s hard cap) | **UNLIMITED. Forced to use all unique clips.** |
| Clip Usage | Drop clips to hit target time | **DO NOT drop clips. Output is as long as necessary.** |
| Loop Closure (Backend) | None | **FFmpeg appends 2s snippet of the opening clip to the end of the video.** |

## Prompt 5: Cinematic ReelForge Flow (v8)

### The Prompt
```text
Property: '{property_name}'
Analyze the attached videos. Extract the most stunning, stable cinematic scenes.
Never select the first 2-3 seconds automatically. Instead, analyze the entire video and choose the most stable cinematic portion. 
For example: Bad: 0s-3s = adjustment, 3s-8s = stable. Required: select 3s-8s.
Reject footage with camera shake, autofocus hunting, exposure shifts, drone acceleration, gimbal calibration, or abrupt turns.

Reel Duration Goals:
- Preferred clip duration: 5-7 seconds.
- Minimum clip duration: 4 seconds (use 3 seconds ONLY if the scene quality is very weak).
- Do NOT aggressively compress the reel. Cinematic storytelling is more important than short reels.

Return an array of 'selected_clips'.
For each clip:
- 'video_index': The exact index of the video
- 'scene_type': Strict labels (e.g., 'drone', 'exterior', 'living_room'). NEVER classify drone footage as interior rooms!
- 'start' and 'end': Timestamps in seconds. Avoid timestamps near clip start.
- 'hero_score': 0-100 visual appeal (100-90: Luxury, Stable. 89-70: Good. Below 70: Avoid).
- 'stability_score': 0-100 gimbal stability
- 'hook_score': 0-100 opening hook appeal
- 'luxury_score': 0-100 high-end aesthetics
- 'camera_motion': static, push_in, push_out, pan, orbit, tilt.
- 'camera_direction': left_to_right, right_to_left, forward, backward, neutral.
- 'shot_size': wide, medium, close.

Avoid selecting visually similar clips. Keep only the strongest angles.
```

### Key Changes from v7 → v8

| Aspect | v7 | v8 (Cinematic Flow & Optimizer) |
|---|---|---|
| Camera Continuity | None | **Extracts `camera_motion`, `camera_direction`, and `shot_size` to build smooth contiguous timelines.** |
| Stability & Aesthetics | Single Score | **Splits scoring into `hero_score`, `stability_score`, `hook_score`, and `luxury_score` for precise filtering.** |
| Backend Optimization | Python sorting | **New `TimelineOptimizer` strictly filters low-stability shots, removes duplicates, selects the best hooks, and sequences everything using Luxury Flow.** |
| Clip Trimming | Gemini Start/End | **Backend automatically pads start+2s to avoid gimbal setup jitter.** |

## Prompt 6: Hybrid OpenCV / Gemini Engine (v9)

### The Prompt
```text
Property: '{property_name}'
Analyze the attached videos. Extract the most stunning cinematic scenes.
Focus purely on aesthetics, framing, and content. (Physical camera shake is handled by an external computer vision pipeline, so assume clips can be trimmed for stability later).

Reel Goals:
- Build the longest high-quality cinematic timeline possible. 
- NEVER remove a good clip just to make the reel shorter.
- Select segments between 4 and 12 seconds depending on their aesthetic quality.

Return an array of 'selected_clips'.
For each clip:
- 'video_index': The exact index of the video (0 for the first video in this batch, 1 for the second, etc.)
- 'scene_type': Strict labels (e.g., 'drone', 'aerial', 'exterior', 'lobby', 'living_room', 'kitchen', 'bedroom', 'bathroom', 'pool', 'gym', 'garden', 'parking', 'amenities'). 
  CRITICAL: Drone/DJI footage must NEVER be classified as interior rooms (kitchen/bedroom/etc.). It can ONLY be drone, aerial, exterior, pool, garden, or amenities.
- 'start' and 'end': Timestamps in seconds.
- 'hero_score': 0-100 score based on visual appeal. (100-90: Luxury, Premium. 89-70: Good but not exceptional. Below 70: Avoid).
- 'composition_score': 0-100 score evaluating framing, rule of thirds, and architectural lines.
- 'hook_score': 0-100 score for how well the shot works as an opening hook.
- 'luxury_score': 0-100 score for how luxurious the shot feels (high-end aesthetics).
- 'camera_motion': Choose from: static, push_in, push_out, pan, orbit, tilt.
- 'camera_direction': Choose from: left_to_right, right_to_left, forward, backward, neutral.
- 'shot_size': Choose from: wide, medium, close.

Avoid selecting visually similar clips. Keep only the strongest angles.
```

### Key Changes from v8 → v9

| Aspect | v8 | v9 (Hybrid Engine) |
|---|---|---|
| Stability & Physics | Evaluated by Gemini | **Evaluated mathematically by OpenCV (`cv_analyzer.py`) before timeline optimization.** |
| Aesthetics | General Hero Score | **Adds strict `composition_score` for Gemini to grade architectural framing.** |
| Trimming Rules | Backend hardcode `MIN_SAFE_START = 3.0` | **Dynamic OpenCV Pre-Trim. Only skips 0-3s if math detects shake/exposure pumps.** |
| Drone Classification | Implicit | **Hard constraint added to prevent DJI/Drone footage from being labeled as Kitchens/Bathrooms.** |
| Pacing Limits | 10s ceiling | **Raised ceiling to 12s for exceptional drone footage, removed duration limits, targeting 90-100% preferred coverage.** |

---

## Prompt 7: Critical Reel Quality Upgrade (v10 — Story Zones + Strict Walkthrough)

### Analysis Prompt (Multi-Segment Extraction)
```text
Property: '{property_name}'
Analyze the attached videos. Extract the most stunning cinematic scenes.

MULTI-SEGMENT EXTRACTION:
- A single video may contain MULTIPLE usable scenes at different timestamps.
- Return multiple selected_clips entries with the same video_index but different
  start/end timestamps if the video contains visually distinct segments.
- LIMIT: Maximum 3 segments per video.
- SINGLE-VIDEO SUPPORT: If only one uploaded video exists, still produce a complete
  mini-story by extracting up to 3 distinct, non-overlapping segments from that
  same video_index.

Scene Types: drone, aerial, exterior, lobby, living_room, kitchen, bedroom,
bathroom, pool, gym, garden, parking, amenities, home_office, conference_room,
corridor, staircase, walk_in_closet, terrace, balcony, rooftop

CRITICAL: Drone/DJI footage must NEVER be classified as interior rooms.
```

### Variation Prompt (Reorder Only, Never Remove)
```text
Property: '{property_name}'
Goal: Generate 3 distinct Reel Variations (Luxury, Instagram Viral, Realtor Style).

CRITICAL RULES:
- custom_sequence MUST include ALL clip_id values from the pool.
- You are REORDERING clips for storytelling flow, NOT removing clips.
- Every clip_id must appear EXACTLY ONCE in each variation's custom_sequence.
- Variation generation may NOT remove clips.
- Variation generation may NOT duplicate clips.
- All {N} clips must be present in each variation.

custom_sequence uses clip_id strings (format: "{video_index}_{start}_{end}")
```

### Timeline Optimizer (Story Zones + Strict Walkthrough)
```python
STORY_ZONES = {
    "OPENING":   ["drone", "aerial", "exterior", "entrance"],
    "INTERIOR":  ["lobby", "living_room", "dining", "kitchen", "home_office",
                  "conference_room", "corridor", "staircase", "walk_in_closet",
                  "master_bedroom", "bedroom", "bathroom"],
    "AMENITIES": ["terrace", "balcony", "pool", "gym", "garden", "amenities",
                  "parking", "rooftop"],
    "CLOSING":   ["closing_exterior", "closing_drone", "closing"]
}

# Style-based strictness
Luxury/Realtor:     strict_walkthrough = True
Instagram/Viral:    strict_walkthrough = False (hero-score ordering)

# Hero Protection
if hero_score >= 90: NEVER REMOVE

# Room Continuity Scoring
("living_room", "kitchen"): +10
("kitchen", "pool"):        -15

# Sequence Validation (4 Rules)
1. No backward movement in walkthrough order
2. No more than 3 same scene_type in a row
3. Drone only in Opening/Closing zones
4. Bathroom never before Living Room
```

### Render Audit
```json
{
    "selected_count": 19,
    "rendered_count": 19,
    "selected_duration": 85.0,
    "rendered_duration": 83.2,
    "duration_coverage": 97.9,
    "coverage": 100.0,
    "skipped_clips": []
}
```

### Key Changes from v9 → v10

| Aspect | v9 | v10 (Story Zones + Strict Walkthrough) |
|---|---|---|
| Room Sequence | Soft scoring preference | **Hard walkthrough order (Luxury/Realtor) or hero-score impact (Instagram/Viral)** |
| Clip Identification | `video_index` integer | **Unique `clip_id` string (`{video_index}_{start}_{end}`)** |
| Multi-Segment | 1 segment per video | **Up to 3 segments per video, each with unique clip_id** |
| Minimum Input | Implicit multi-clip assumption | **Supports single-upload projects by extracting multiple segments from one full-tour video** |
| Variation Clips | Cherry-picked subset | **ALL clips included, reorder only, no removal allowed** |
| Render Audit | Count-based | **Full duration coverage audit with skip reasons** |
| Hero Protection | None | **hero_score >= 90 clips are NEVER removed** |
| Continuity | None | **Room-to-room transition bonuses/penalties** |
| Server Stability | No crash guard | **Background tasks auto-restart, FFmpeg 120s timeout** |

---

## Prompt 8: QA & Testing Engineering (v11)

### The Prompt
```text
Project: 'ReelForge Short Generator'
Goal: Generate a comprehensive, 9-layer testing infrastructure and API documentation framework.

Requirements:
1. Implement Unit Testing (Pytest/Vitest) for isolated functions.
2. Implement Integration Testing (Pytest/Vitest) for data flow.
3. Implement System Testing (Playwright) for complete application state.
4. Implement User Acceptance Testing (Playwright) mapping to real-world workflows.
5. Implement Smoke Testing (Playwright) for critical build functionality.
6. Implement Sanity Testing (Playwright) for specific recent bug fixes.
7. Implement Interface/API Testing (Pytest+httpx) for FastAPI routing.
8. Implement Regression Testing (Playwright) to protect baseline functionality.
9. Integrate Swagger UI (`swagger-ui-react`) into the frontend to visualize the OpenAPI schema.

Output:
Provide the implementation plan, test framework scaffolding, and integration code across the frontend, backend, and e2e directories.
```

### Reasoning
- **Quality Assurance**: As the application matured into an enterprise SaaS platform, regressions and UI breaks became more likely. This prompt explicitly instructs the engineering setup to scaffold a complete test suite covering the 9 essential layers of software QA requested by the user.

## Prompt 9: Master Quality Upgrade V4.0

### The Prompt
```text
Property: '{property_name}'
Analyze the attached videos. Extract the most stunning cinematic scenes for a luxury real estate reel.

═══ QUALITY-FIRST OPERATIONAL HIERARCHY ═══
Priority 1 — QUALITY: Visual stability, sharpness, exposure correctness, and frame integrity.
Priority 2 — STORY: Natural spatial walkthrough progression of the home.
Priority 3 — COVERAGE: Maximize asset preservation (target 80-100%) WITHOUT compromising quality or story.
RULE: Low-scoring or structurally redundant clips must NEVER be included solely to satisfy coverage. Narrative cohesion supersedes data volume.

═══ PEAK WINDOW DETECTION ═══
Evaluate continuous video using a 0.5-second rolling window to isolate the mathematically highest-scoring segment (4-7 second default range).
Formula: window_score = (0.30 × luxury) + (0.25 × reveal) + (0.20 × composition) + (0.15 × motion) + (0.10 × lifestyle)

═══ STORY ARC ENGINE ═══
Timeline pacing follows emotionally-paced 4-phase structure:
HOOK (15%) → Hero Exterior, Hero View — instant visual impact
DISCOVERY (35%) → Entrance, Lobby, Living, Dining — guided spatial orientation
SHOWCASE (35%) → Kitchen, Master Bedroom, Pool, Balcony — crown jewels and wow-factor
RESOLUTION (15%) → Best Exterior, Hero View, Drone Pull-Away — emotional close

═══ SCORING FIELDS ═══
- hero_score: 0-100 (90+ = Immutable)
- composition_score: 0-100
- hook_score: 0-100
- luxury_score: 0-100 (90+ = Immutable)
- reveal_score: 0-100 (90+ = Immutable) — NEW V4.0
- lifestyle_score: 0-100 — NEW V4.0
- camera_motion: static, push_in, push_out, pan, orbit, tilt
- camera_direction: left_to_right, right_to_left, forward, backward, neutral
- shot_size: wide, medium, close

═══ DURATION RULES ═══
Standard clips (hallways, bathrooms): 4-7 seconds
Hero clips (kitchens, living rooms, pools): 7-10 seconds
Premium aerial/drone sweeps: 10-12 seconds
```

### Reasoning
- **Retention-First Design**: The Story Arc Engine (HOOK → DISCOVERY → SHOWCASE → RESOLUTION) mirrors how professional luxury real estate editors structure their reels. This pacing keeps viewer attention through emotional peaks rather than flat chronological tours.
- **Property Highlight Memory**: Pre-scanning all assets identifies the "Crown Jewels" before building the timeline, ensuring the most impactful shots are strategically placed at the hook (opening), anchor (mid-reel), and climax (closing).
- **Repetition Memory**: A 5-clip lookback window with -30 penalty eliminates the common `Exterior → Exterior → Exterior` and `Pool → Pool` repetition problem that makes reels feel amateur.
- **Motion Diversity Tracking**: Penalizing 3+ consecutive identical camera movements prevents visual boredom and creates the kinetic variety expected in premium real estate content.
- **Lucas-Kanade Optical Flow**: Automated detection of drone takeoff shake, gimbal initialization, autofocus loops, and exposure hunting ensures only clean footage reaches the final reel.
- **Fault-Tolerant Render Audit Gate**: The 3-tier PASS/WARNING/FAIL gate prevents corrupt or incomplete renders from reaching clients while allowing minor frame drops through.

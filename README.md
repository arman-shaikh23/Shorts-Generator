# Real Estate AI Shorts Generator (Premium SaaS)

An enterprise-grade, Canva-tier AI platform that empowers Real Estate Agents, Builders, and Marketing Agencies to effortlessly transform raw property footage into high-converting, viral social media shorts. The product bridges the gap between raw assets and published marketing material by replacing tedious manual video editing with intelligent, context-aware AI storytelling and an interactive visual timeline.

## Tech Stack
- **Frontend**: React, Vite, Tailwind CSS, Framer Motion, Shadcn UI
- **Backend**: FastAPI (Python), Motor (Async MongoDB)
- **Database**: MongoDB (Atlas)
- **Auth**: RSA-256 JWT with Refresh Token Rotation
- **AI Engine**: Google Gemini Pro (via Files API) + OpenCV Hybrid Scoring
- **Render Engine**: FFmpeg with Dynamic Crossfade Graph

## Production Reliability and Observability (17.16)
- **Structured Logging + Request IDs**
  - Unified root logger with Structlog-first JSON output (`LOG_FORMAT=json`) and request correlation via `X-Request-ID`.
  - File + console logging are both supported; Better Stack shipping is optional via source token.
  - Log events include `trace_id` and `span_id` (when tracing context exists) for Grafana correlation.
- **Rate Limiting**
  - Global middleware protects backend routes with path-aware limits (auth + generation stricter than default).
  - Returns `429` with `Retry-After` and `X-RateLimit-*` headers.
- **OpenTelemetry Tracing**
  - Optional OTEL tracing pipeline for FastAPI + HTTPX + PyMongo.
  - OTLP exporter and console exporter modes are both supported behind feature flags.
- **Alerts**
  - Optional webhook alerts for repeated background-task crashes and startup dependency failures.
  - Built-in cooldown prevents alert storms.
- **Crash-Safe Runtime Guards**
  - Startup dependency initialization now retries with backoff.
  - Background workers auto-restart with escalating retry delay and health state tracking.
- **CI/CD**
  - Added GitHub Actions workflow (`.github/workflows/ci.yml`) for backend tests (with Mongo service) and frontend build.
  - Added local Grafana stack under `observability/` (Grafana + Prometheus + Loki + Tempo + Promtail).

### New Health Endpoints
- `GET /api/v1/health/live`: liveness probe (process is serving requests).
- `GET /api/v1/health/ready`: readiness probe (critical components ready).
- `GET /api/v1/health/runtime`: runtime component + background-task state snapshot.
- Existing diagnostics remain:
  - `GET /api/v1/health/pools`
  - `GET /api/v1/health/indexes`

### Reliability and Observability Env Controls
Add these in `backend/.env` (or use `.env.small` / `.env.large` presets):

```env
ENABLE_STRUCTLOG=true
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_TO_FILE=true
LOG_FILE_PATH=logs/reelforge_debug.log

ENABLE_BETTER_STACK=false
BETTER_STACK_SOURCE_TOKEN=

ENABLE_RATE_LIMITING=true
RATE_LIMIT_REQUESTS_PER_MINUTE=180
RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE=30
RATE_LIMIT_GENERATION_REQUESTS_PER_MINUTE=20
RATE_LIMIT_EXCLUDE_PATHS=/api/v1/health,/favicon.ico,/favicon.svg,/openapi.json,/docs,/redoc,/assets,/outputs,/data
RATE_LIMIT_TRUST_PROXY=false
RATE_LIMIT_MAX_KEYS=10000

STARTUP_RETRY_ATTEMPTS=5
STARTUP_RETRY_BASE_DELAY_SEC=2
STARTUP_RETRY_MAX_DELAY_SEC=15

ENABLE_ALERTS=false
ALERT_WEBHOOK_URL=
ALERT_COOLDOWN_SEC=300
ALERT_HTTP_TIMEOUT_SEC=5.0
ALERT_MIN_CONSECUTIVE_BACKGROUND_FAILURES=2

ENABLE_OTEL=false
OTEL_SERVICE_NAME=reelforge-backend
OTEL_EXPORTER_OTLP_ENDPOINT=
OTEL_EXPORTER_OTLP_HEADERS=
OTEL_EXPORTER_TIMEOUT_SEC=5.0
OTEL_ENABLE_CONSOLE_EXPORTER=false
OTEL_INSTRUMENT_FASTAPI=true
OTEL_INSTRUMENT_HTTPX=true
OTEL_INSTRUMENT_PYMONGO=true
OTEL_INSTRUMENT_LOGGING=true

ENABLE_PROMETHEUS_METRICS=true
PROMETHEUS_METRICS_PATH=/metrics
```

### Grafana Quick Start (Beginner)
1. Run backend with:
   - `ENABLE_OTEL=true`
   - `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces`
   - `ENABLE_PROMETHEUS_METRICS=true`
2. Start monitoring stack:
   - `cd observability`
   - `docker compose up -d`
3. Open Grafana at `http://localhost:3000` with:
   - user: `admin`
   - password: `admin`
4. Open dashboard: `ReelForge Backend Overview`
5. Use **Explore** tab:
   - Prometheus for metrics
   - Loki for logs
   - Tempo for traces

Detailed steps: `observability/README.md`.

## Features
- **7-Step Guided Wizard Workflow**: Completely dismantled the massive single-page dashboard into a focused, modern SaaS wizard (Upload -> Analyze -> Storyboard -> Style -> Music -> Generate -> Export).
- **Interactive Wizard Navigation**: The top progress bar is fully clickable, allowing users to seamlessly navigate backwards to previous steps (e.g., jump back to Upload to add a new clip) and return forward, with strict progression validation that prevents skipping ahead into uncompleted stages.
- **Custom Music Engine & Mixing**: Integrated an advanced FFmpeg `amix` pipeline that dynamically loops and mixes background music with the original video audio. Includes a dedicated UI step with volume sliders (0-100%) and an auto-scanning `data/library/music` folder for users to drop in downloaded MP3/WAV files for playable previewing and generation.
- **Premium Canva-style Upload Workflow**: Focused upload screen with animated drag-and-drop zones, explicit URL integrations (YouTube, Drive, Dropbox, OneDrive), and a dynamic "Upload Complete" success card to keep the workspace clean.
- **Luxury Ocean Aurora Dashboard**: A premium, light-themed workspace inspired by Stripe and Linear. Features an 80px floating top navigation bar and a clean responsive 2-column workspace layout.
- **Authentic Data Visualization**: The UI strictly surfaces real data returned by the backend (e.g. actual extracted clip durations, actual scene types) with zero hardcoded "mock" metrics.
- **Micro-Interactions**: Built heavily with Framer Motion to provide high-end, smooth animations (hover scaling, layout transitions, animated step indicators).
- **Persistent System Status Rail**: Dashboard, Projects, and History now include a shared status rail with `queued`, `processing`, `failed`, and `done` buckets, latest activity timestamps, and quick recovery actions.
- **Status Drill-Down Navigation**: Status cards in the rail are interactive; `done` opens History while `queued`/`processing`/`failed` open Projects with status-aware filtered views.
- **Global Toast Feedback Layer**: Create/download actions now show consistent success/error toast notifications across dashboard workflows.
- **Projects and History Control Panel UX**: Both pages now support URL-synced `search + filter + sort + pagination` so users can share and reopen the exact same view state.
- **Empty-State Onboarding UX**: Empty pages now include practical startup checklists and direct navigation to the next meaningful action.
- **Video Performance Pass**: Video-heavy surfaces now use lighter preload behavior (`preload="none"` where appropriate), poster-first rendering, and viewport-triggered loading on dashboard demo media.

### 1. Premium SaaS Dashboard Experience
The authenticated workspace also exposes a persistent health/status rail so users can monitor generation state at a glance while moving between Dashboard, Projects, and History.
The moment you log into ReelForge, a responsive, 2-column glassmorphism dashboard instantly showcases the platform’s capabilities through a looping demo reel. Users immediately understand the "22 Raw Clips → AI Analysis → Cinematic Reel" workflow without ever needing to read a tutorial.

### 2. Hybrid Cinematic AI Engine V4.0 (OpenCV + Gemini + Story Arc)
- **Story Arc Engine**: Timeline pacing follows an emotionally-paced 4-phase arc: **HOOK** (15% — instant visual impact with hero exteriors/views) → **DISCOVERY** (35% — guided spatial orientation through entrance/lobby/living/dining) → **SHOWCASE** (35% — crown jewels: kitchen/master bedroom/pool/balcony) → **RESOLUTION** (15% — emotional close with drone pull-away). This replaces the flat zone-based walkthrough and significantly improves viewer retention.
- **Property Highlight Memory Module**: Pre-scans all ingested media to identify the "Crown Jewels" (`hero_pool`, `hero_exterior`, `hero_view`, `hero_living_room`) and strategically deploys them: Hook → hero_exterior, Mid-Reel Anchor → hero_living_room, Climax → hero_pool + drone pull-away.
- **Peak Window Detection**: Evaluates video streams using a 0.5-second rolling window to isolate the mathematically highest-scoring segment. Formula: `window_score = (0.30 × luxury) + (0.25 × reveal) + (0.20 × composition) + (0.15 × motion) + (0.10 × lifestyle)`.
- **Repetition Memory**: 5-clip lookback window with -30 point penalty for repeated `scene_type`, eliminating the `Exterior → Exterior → Exterior` repetition pattern even across different source videos.
- **Motion Diversity Tracking**: Deducts 30 points for 3+ consecutive identical `camera_motion`, `camera_direction`, or `shot_size`. Target flow: `Push In → Pan Left → Static Wide → Drone Top-Down → Orbit`.
- **Quality-First Priority Matrix**: Quality → Story → Coverage operational hierarchy. Clips are never included solely to satisfy coverage metrics — narrative cohesion always supersedes data volume.
- **Expanded Hero Protection**: Clips with `hero_score ≥ 90 OR reveal_score ≥ 90 OR luxury_score ≥ 90` are automatically flagged as Immutable. The pacing layer can adjust runtime duration but is strictly prohibited from dropping the asset.
- **Enhanced Adjacency Scoring**: Natural transitions receive +25 bonus (Living Room → Dining). Jarring jumps receive -50 penalty (Bathroom → Kitchen). Missing room types in the progression sequence are gracefully skipped.
- **Contextual Clip Duration**: Standard functional clips (hallways, bathrooms) get 4-7s. Hero asset clips (kitchens, pools, living rooms) get 7-10s. Premium aerial/drone sweeps get 10-12s.
- **Premium Closing Shot Architecture**: Mandatory closing hierarchy: Pool View → Best Exterior → Drone Pull-Away. Never ends on bathroom, closet, secondary bedroom, kitchen island, or unstabilized handheld pan.
- **Multi-Variant Style Profiles**: `luxury_tour` (100% asset preservation, 1.0 pace), `premium_realtor` (90-100%, 0.85 pace), `instagram_viral` (70-80%, 0.60 pace).
- **Lucas-Kanade Optical Flow**: `cv2.calcOpticalFlowPyrLK()` detects and trims drone takeoff shake, gimbal initialization, autofocus loops, and exposure hunting — preserving only the clean footage.
- **Intelligent Media Filtering**: Accepts ≥720p resolution (many premium assets from messaging apps are compressed). Only rejects binary duplicates, corrupted file wrappers, or extreme blur.
- **OpenCV Multi-Threading**: All CPU-intensive CV operations run via `asyncio.to_thread()` behind a `cv_semaphore = asyncio.Semaphore(3)` to prevent CPU saturation and FastAPI event loop blocking.
- **Computer Vision Pre-Processing**: OpenCV physics layer (`cv_analyzer.py`) mathematically analyzes footage for motion blur (Variance of Laplacian), exposure spikes, and severe camera shake (MSE).
- **Multi-Segment Extraction**: A single uploaded video can contribute up to 3 distinct scenes. Each segment gets a unique `clip_id` for accurate tracking.
- **Single-Video Full Tour Support**: Analysis can start with just 1 processed upload. For one long home-tour file, the AI extracts up to 3 strong, non-overlapping segments and builds a reel-ready timeline.
- **Strict Drone Segregation**: DJI/Drone footage is never incorrectly labeled as interior property rooms.
- **Fault-Tolerant Render Audit Gate**: 3-tier status matrix: ≥95% → PASS (deliver), 90-94.9% → WARNING (log, deliver), <90% → FAIL (halt delivery for reprocessing). Tracks `selected_clips`, `rendered_clips`, `missing_clips_indices`, `calculated_target_duration`, `final_compiled_duration`, and `render_success_percentage`.
- **Sequence Validation**: Post-optimization validation enforces 4 hard rules: no backward movement, max 3 same-type consecutive clips, drone only in opening/closing zones, bathroom never before living room.
- **Full Render Audit**: Every render is tracked with `selected_count`, `rendered_count`, `selected_duration`, `rendered_duration`, `duration_coverage_pct`, `audit_status`, and detailed skip reasons.
- **ALL-Clips Variation Rendering**: All 3 style variations MUST include every approved timeline clip. `custom_sequence` controls ordering only, never removal.

### 3. Smart Deduplication & Scene Diversity
- **Production-Grade AI Selection**: Extracts multiple segments from long videos, applies strict >85% confidence thresholding, and uses a native Semantic Deduplication pipeline to guarantee only the highest-quality unique shots are used.
- **ReelForge Storytelling Engine**: Analyzes and builds sequences following a strict real estate logic: Drone/Exterior -> Walkthrough -> Amenities -> Parking. Explicitly prevents using low-tier scenes (e.g., Parking, Bathrooms) as the opening hook.
- **Unlimited Dynamic Reel Durations**: The platform intelligently utilizes all unique non-duplicate footage available, generating Shorts and YouTube videos that are exactly as long as needed rather than being artificially cropped to a 30-60s limit.
- **Seamless Loop Closure**: Automatically appends a 2-second snippet of the first clip to the very end of the final video to create perfect looping content for TikTok, Reels, and Shorts.
- **Coverage Protection System**: Forces maximum clip utilization (100% of unique clips) by ensuring at least 1 segment from every unique uploaded clip is used.
- **Parallel FFmpeg Traffic Control**: Strictly throttles concurrent video encoding operations (Semaphore) to prevent system freezing and memory starvation during heavy loads (30+ clips).
- **Automated Storage Management**: Aggressively cleans up intermediate rendering chunks immediately after compilation. A background daily cron job (`cleanup.py`) continually sweeps for orphaned files. Furthermore, project deletion instantly triggers a deep recursive destruction of all associated `data/` directories to keep the server lightweight.

### ReelForge Story Engine v9
- **Strict Walkthrough Algorithm**: Hard walkthrough order for Luxury/Realtor styles with 4 Story Zones. Instagram/Viral uses hero-score-first ordering for attention optimization.
- **Unlimited Duration Algorithm**: The AI doesn't restrict itself to an arbitrary time budget; it uses ALL unique clips for maximum coverage. 85s of selected footage → 85s final reel.
- **Loop Closure Mechanics**: FFmpeg dynamically appends a 2-second snippet of the opening clip to the very end of the reel, creating an infinite loop effect for social platforms.
- **Scene Role Classification**: Expanded scene types include `home_office`, `conference_room`, `corridor`, `staircase`, `walk_in_closet`, `terrace`, `rooftop` alongside all standard real estate rooms.
- **Strict Deduplication**: 3-stage validation process utilizing SHA-256 (file integrity), 3-frame Perceptual Hashing (visual similarity), and Structural Similarity Index Measure (SSIM).
- **Server Crash Prevention**: Background tasks are wrapped in `safe_background_task()` with auto-restart. FFmpeg subprocesses have 120s timeouts. Ctrl+C immediately kills the server.

- **Enterprise Reliability & Auth**: Secure RSA-256 Google & Email login, backed by intelligent exponential backoff and model failover (`gemini-2.5-pro` -> `flash`) to ensure 99.9% processing uptime.
- Direct downloads of fully prepared 4K/1080p clips from the sticky preview player.

## Reel Quality V2 (Safe Rollout)
ReelForge now includes a **feature-flagged V2 quality layer** that is additive and backward compatible with the current production pipeline.

### What V2 Adds
- Stability metadata per clip (`stability_score_v2`, `motion_variance`, `optical_flow_consistency`, `rotation_stability`, `translation_stability`).
- Trim recommendation metadata (`trim_recommendation_v2`) with confidence and reason codes.
- Optional story ordering layer with confidence-based fallback to existing ordering.
- Optional near-duplicate perspective penalty layer (no hard clip deletions).
- Optional scoring extension (`final_score_v2`) that keeps existing `final_score` intact.

### Feature Flags (`backend/.env`)
- `PIPELINE_SHADOW_MODE=true`: Compute V2 metadata without forcing V2 ordering behavior.
- `ENABLE_STABILITY_V2=false`: Enable stability metadata capture pipeline.
- `ENABLE_TRIM_V2=false`: Apply V2 trim recommendations when confidence is high.
- `ENABLE_STORY_V2=false`: Enable V2 story ordering layer.
- `ENABLE_SCORING_V2=false`: Enable V2 scoring fields (`final_score_v2`, etc.).
- `ENABLE_DEDUP_V2=false`: Enable V2 near-duplicate perspective penalties.
- `ENABLE_TRANSITION_V2=false`: Reserved for stricter transition-policy evolution.
- `V2_MIN_TRIM_CONFIDENCE=0.6`: Minimum confidence required before applying V2 trim.
- `V2_MIN_STORY_CONFIDENCE=0.55`: Minimum confidence required before applying V2 story ordering.

### Rollout Pattern
1. Run with `PIPELINE_SHADOW_MODE=true` and all `ENABLE_*_V2=false` to collect metadata safely.
2. Enable `ENABLE_STORY_V2=true` for sequence improvements once confidence metrics are stable.
3. Enable `ENABLE_TRIM_V2=true` for automatic trim promotion in production.
4. Keep rollback simple by toggling `ENABLE_*_V2=false` (legacy path remains active).

## Connection Pooling (Performance Layer)
ReelForge now uses explicit connection pooling for both MongoDB and outbound HTTP downloads.

### Why Connection Pooling Matters
- Opening a new TCP/TLS connection for every request is expensive.
- Reusing established connections reduces latency and CPU overhead.
- Under parallel uploads/processing, pooling stabilizes throughput and lowers connection churn.
- Pools apply backpressure safely (queueing/waiting) instead of causing burst failures.

### What Is Pooled in ReelForge
- **MongoDB Driver Pool**: Configured in `backend/app/core/database.py` using Motor's built-in pool controls.
- **Shared HTTP Client Pool**: Configured in `backend/app/core/http_client.py` with one `httpx.AsyncClient` for the app lifecycle.
- **FastAPI Lifecycle Wiring**: Pool initialization and cleanup are handled in `backend/main.py` startup/shutdown.

### New Environment Settings
Add or tune these in `backend/.env`:

```env
MONGO_MAX_POOL_SIZE=100
MONGO_MIN_POOL_SIZE=5
MONGO_MAX_IDLE_TIME_MS=45000
MONGO_WAIT_QUEUE_TIMEOUT_MS=10000
MONGO_SERVER_SELECTION_TIMEOUT_MS=5000

HTTP_POOL_MAX_CONNECTIONS=100
HTTP_POOL_MAX_KEEPALIVE_CONNECTIONS=20
HTTP_CONNECT_TIMEOUT_SEC=10.0
HTTP_READ_TIMEOUT_SEC=300.0
HTTP_WRITE_TIMEOUT_SEC=30.0
HTTP_POOL_TIMEOUT_SEC=30.0
```

### Pool Observability & Diagnostics
- **Pool Metrics Collector**: `backend/app/core/pool_observability.py` tracks request latency, timeout classes, Mongo ping/connect metrics, and Mongo checkout wait telemetry.
- **Read-Only Diagnostics Endpoint**: `GET /api/v1/health/pools` returns current pool status (`ok`/`degraded`), issue flags, and detailed snapshots for HTTP + Mongo pools.
- **Timeout Visibility**: Pool timeout events are explicitly logged to make saturation visible before it causes user-facing failures.

### Environment Presets
- `backend/.env.small`: conservative pool sizing for low-concurrency or single-node setups.
- `backend/.env.large`: higher pool sizing for high concurrency or multi-worker deployments.
- Both presets keep all V2 quality flags in backward-compatible safe defaults (`false`).

### Rollout Guidance
1. Start with defaults.
2. Measure p95 API latency and upload success rate.
3. Increase `MONGO_MAX_POOL_SIZE` and `HTTP_POOL_MAX_CONNECTIONS` only if queue waits are visible.
4. Keep `MONGO_MIN_POOL_SIZE` modest to avoid idle resource waste.
5. Use `/api/v1/health/pools` during load testing to validate timeout and wait behavior.
6. Roll back by restoring previous env values; code remains backward compatible.

## Database Indexing (Query Performance Layer)
ReelForge now ensures critical MongoDB indexes at startup to accelerate hot query paths.

### Why Indexing Matters
- Replaces expensive collection scans with index scans on high-traffic endpoints.
- Improves response latency for paginated lists and sorted reads.
- Stabilizes worker throughput for pending-upload polling and status transitions.
- Supports refresh-token lifecycle with TTL-based automatic cleanup.

### Indexes Ensured at Startup
Implemented in `backend/app/core/database.py` during Mongo connection bootstrap.

- `users.email` (unique) for signup/login lookups.
- `refresh_tokens.token` (unique) for refresh token lookup.
- `refresh_tokens.expires_at` (TTL) for automatic expired-token deletion.
- `refresh_tokens.family + is_revoked` for family-wide revocation checks.
- `refresh_tokens.user_id + is_revoked` for logout/session revocation.
- `projects.userId + updatedAt(desc)` for project listing and sort.
- `uploads.projectId + order` for ordered upload listing and tail lookup.
- `uploads.projectId + status + order` for analyzed/duplicate/status-specific project upload reads.
- `uploads.status + uploadedAt` for pending worker polling/query progression.
- `uploads.userId + status` for user-level upload/status counts.
- `generated_shorts.userId + createdAt(desc)` for history listing and sort.
- `generated_shorts.projectId` for project-level generated count and cleanup queries.
- `idempotency_keys.user_id + endpoint + key` (unique) for retry deduplication scope.
- `idempotency_keys.expires_at` (TTL) for automatic key cleanup.
- `idempotency_keys.status + updated_at` for idempotency state diagnostics.

### Operational Notes
- Index creation runs on every startup and is idempotent.
- Startup does not crash if an index creation fails; failures are logged with `[MONGO INDEX]`.
- Read-only diagnostics endpoint: `GET /api/v1/health/indexes` lists expected/actual/missing indexes per critical collection.
- Validate usage with Mongo `explain()` and ensure winning plans use `IXSCAN`.

## Idempotency for Write Operations (Retry Safety Layer)
ReelForge now supports optional idempotency keys for critical JSON write endpoints so network retries do not duplicate writes.

### Header Contract
- Request header: `Idempotency-Key: <client_generated_unique_key>`
- Alias header also accepted: `X-Idempotency-Key`
- No key provided: endpoint behaves normally (backward compatible).

### Write Endpoints Covered
- `POST /api/v1/projects`
- `PATCH /api/v1/projects/{project_id}`
- `DELETE /api/v1/projects/{project_id}`
- `POST /api/v1/projects/{project_id}/uploads`
- `POST /api/v1/projects/{project_id}/uploads/file`
- `POST /api/v1/projects/{project_id}/uploads/music`
- `PATCH /api/v1/projects/{project_id}/uploads/reorder`
- `DELETE /api/v1/projects/{project_id}/uploads/{upload_id}`

### Behavior
- First request with a new key: operation executes normally and response is stored.
- Retry with same key + same payload: stored response is replayed (no duplicate write).
- Same key + different payload: `409` conflict (`Idempotency-Key already used with a different request payload`).
- Same key while first request is still processing: `409` conflict.

### Storage Model
- Collection: `idempotency_keys`
- Unique index: `(user_id, endpoint, key)`
- TTL index on `expires_at` (automatic cleanup)
- Key status lifecycle: `IN_PROGRESS -> COMPLETED` (or `FAILED` on error)

### Operational Notes
- Designed for client retries after timeout/connection drops.
- Use a fresh key for a new business action.
- Reuse the exact same key only when retrying the same action.

## Streaming Uploads (Large Files)
ReelForge now streams incoming file uploads in chunks and never loads the full upload into memory.

### Where Streaming Is Applied
- `POST /api/v1/projects/{project_id}/uploads/file` (video upload)
- `POST /api/v1/projects/{project_id}/uploads/music` (custom music upload)
- Internal write loop: reads chunk -> writes chunk -> repeats until EOF.

### Why This Matters
- Prevents RAM spikes when uploading large videos.
- Improves multi-user upload stability under concurrency.
- Allows deterministic API-level size enforcement with `413 Payload Too Large`.
- Removes partial files automatically when upload fails or exceeds limits.
- Rejects non-video payloads (for example `.jpg`) on the video upload endpoint.

### Streaming Upload Environment Settings
Configure these in `backend/.env` if needed:

```env
UPLOAD_STREAM_CHUNK_SIZE=1048576
MAX_VIDEO_UPLOAD_BYTES=10737418240
MAX_MUSIC_UPLOAD_BYTES=104857600
```

- `UPLOAD_STREAM_CHUNK_SIZE`: bytes per read/write chunk (default 1MB).
- `MAX_VIDEO_UPLOAD_BYTES`: max allowed size for a **single** `/uploads/file` request (10GB default).
- `MAX_MUSIC_UPLOAD_BYTES`: max allowed size for `/uploads/music` requests.

### Video Input Validation Rules (`/uploads/file`)
- File extension must be a supported video type (`.mp4`, `.mov`, `.mkv`, `.avi`, `.webm`, `.m4v`).
- Supported image uploads are accepted (`.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.tif`, `.tiff`, `.gif`) and normalized into motion MP4 clips during worker processing.
- Uploaded file is verified with `ffprobe` to confirm it contains a real video stream.
- If validation fails, the API returns `415 Unsupported Media Type`.

### Remote URL Ingestion (`/uploads`)
- `POST /api/v1/projects/{project_id}/uploads` accepts `http(s)` URLs, including YouTube watch/share links and direct media links.
- YouTube URLs are downloaded with `yt-dlp`, normalized to local media, then processed by the same dedup/preview/analyze pipeline.
- Playlist URLs are not supported; submit a single YouTube video URL per upload item.
- Optional environment settings:
  - `YTDLP_COOKIES_FILE`: path to exported browser cookies for age-restricted/private-access scenarios.
  - `YOUTUBE_MAX_DURATION_SEC`: hard cap for remote YouTube source duration (`0` disables cap).
- Ensure you have the legal right to download and process the source media.

## Pagination (Scalability Layer)
ReelForge now exposes standardized pagination metadata for list-heavy APIs, while preserving legacy response fields.

### Backend Pagination Coverage
- `GET /api/v1/projects`
  - Supports `page`, `skip`, `limit`.
  - Returns additive metadata: `total`, `page`, `limit`, `skip`, `pages`, `has_next`, `has_prev`, `next_page`, `prev_page`, `next_skip`, `prev_skip`.
- `GET /api/v1/history`
  - Supports `page`, `skip`, `limit`.
  - Returns same standardized metadata fields.
- `GET /api/v1/projects/{project_id}/uploads`
  - Backward compatible default: returns full list when no pagination params are sent.
  - Paginated mode is enabled by passing `paginate=true` or any of `page/skip/limit`.

### Frontend Usage
- Projects page uses paginated fetch with page controls.
- History page uses paginated fetch with page controls.
- Existing project detail upload workflow remains unchanged and backward compatible.

### Why This Helps
- Faster page rendering on large datasets.
- Lower memory use and smaller API payloads.
- Better UX through explicit Prev/Next navigation.
- Safe migration path because legacy fields and unpaginated upload behavior are preserved.

## Redis Caching (TTL + Invalidation + Cache-Aside)
ReelForge now includes a feature-flagged Redis caching layer designed for safe rollout and zero contract breakage.

### Cache Pattern Used
- **Cache-aside**:
1. Try Redis (`GET`) using deterministic key.
2. On cache miss, fetch from MongoDB.
3. Return response and populate Redis (`SET EX ttl`).
- MongoDB remains source of truth; Redis is an acceleration layer.

### What Is Cached
- `GET /api/v1/projects` (paginated list)
- `GET /api/v1/projects/{project_id}` (detail)
- `GET /api/v1/projects/dashboard/stats`
- `GET /api/v1/history` (paginated)
- `GET /api/v1/projects/{project_id}/uploads` (full and paginated modes)
- `GET /api/v1/music-library`

### TTL Settings
Configure in `backend/.env`:

```env
ENABLE_REDIS_CACHE=false
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=100
REDIS_CONNECT_TIMEOUT_SEC=2.0
REDIS_READ_TIMEOUT_SEC=2.0

CACHE_DEFAULT_TTL_SEC=60
CACHE_TTL_PROJECTS_SEC=60
CACHE_TTL_PROJECT_DETAIL_SEC=60
CACHE_TTL_HISTORY_SEC=90
CACHE_TTL_UPLOADS_SEC=30
CACHE_TTL_DASHBOARD_STATS_SEC=30
CACHE_TTL_MUSIC_LIBRARY_SEC=300
CACHE_VERSION_TTL_SEC=2592000
```

### Invalidation Strategy
- **Versioned namespace keys** are used for O(1) invalidation.
- Mutation endpoints bump version counters instead of scanning/deleting wildcard keys.
- Main invalidation groups:
  - Project mutations: projects list + project detail + stats
  - Upload mutations: uploads list + project detail + projects list + stats
  - Generation mutations: history + projects list + project detail + stats
  - Project delete: projects + history + stats + project detail + uploads

### Rollout Safety
- Cache is disabled by default (`ENABLE_REDIS_CACHE=false`).
- If Redis is unavailable or errors occur, the API falls back to MongoDB reads without failing requests.
- Existing response contracts and workflow behavior remain unchanged.

## Troubleshooting
- **Professional Camera Footage (Sony XAVC, etc.)**: High-end footage with `rtmd` metadata streams or 10-bit 4:2:2 chroma subsampling might fail standard FFmpeg extraction. The application automatically normalizes this footage, dropping non-video/audio streams and forcing `yuv420p` pixel format to ensure Gemini AI compatibility.
- **API 404 Errors**: If `/api/process` returns a 404 on deployment, verify that the static file mount isn't intercepting the root path. Our production build is configured to serve static assets safely without shadowing `/api/*`.
- **Windows Python 3.13 `NotImplementedError`**: FFmpeg commands are deliberately executed using `subprocess.run` inside `asyncio.to_thread()` instead of `asyncio.create_subprocess_exec`. This is to circumvent a `NotImplementedError` limitation on Windows platforms with the Proactor event loop. 
- **Missing Videos**: If downloading from Dropbox fails or creates empty files, check the server logs. We have added deep debugging around the download stage to trace HTTP responses, content types, and file sizes.

## Quality Assurance & Testing Strategy
ReelForge utilizes a comprehensive, multi-layered testing strategy to guarantee stability across its cinematic AI engine and SaaS platform:

- **Unit Testing**: Tests individual functions, methods, or modules in isolation (e.g., verifying the OpenCV motion blur math). It helps identify defects at the earliest stage of development.
- **Integration Testing**: Verifies that different modules or components work correctly together (e.g., testing the FastAPI integration with MongoDB). It ensures proper data flow and communication between integrated parts.
- **System Testing**: Tests the complete application as a whole against specified requirements. It validates the overall functionality of the system end-to-end.
- **User Acceptance Testing (UAT)**: Conducted by end users or clients to verify that the software meets business requirements. It is the final testing phase before deployment.
- **Smoke Testing**: Checks the basic and critical functionalities of a new build (e.g., does the dashboard load?). It determines whether the build is stable enough for further testing.
- **Sanity Testing**: Performs a quick validation of specific changes or bug fixes. It ensures that recent modifications work as expected.
- **Interface Testing**: Tests the interaction between different systems, applications, or APIs. It ensures that data is exchanged correctly across interfaces.
- **Regression Testing**: Verifies that recent changes or bug fixes have not affected the existing functionality of the application (e.g., ensuring loop closure doesn't break timeline optimization).
- **API Testing**: Verifies that APIs function correctly by validating requests, responses, data exchange, and business logic between applications. We expose an interactive **Swagger UI** on the frontend at `/api-docs` to facilitate this.

## Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- `ffmpeg` installed on your system (`sudo apt install ffmpeg` / `brew install ffmpeg` / download for Windows)
- A Gemini API Key from [Google AI Studio](https://aistudio.google.com/)

### 1. Clone & Setup Backend
```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment
python -m venv venv

# Activate it (Windows)
.\venv\Scripts\activate
# (Mac/Linux: source venv/bin/activate)

# Install requirements
pip install -r requirements.txt

# Environment variables
cp .env.example .env
# Open .env and add your GEMINI_API_KEY
```

### 2. Setup Frontend
```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install
```

### 3. Run Locally (Development)

Start the backend:
```bash
cd backend
uvicorn main:app --reload --port 8000
```

Start the frontend:
```bash
cd frontend
npm run dev
```
Access the app at `http://localhost:5173`.

## Deployment to Railway
1. Push this repository to GitHub.
2. Log into [Railway](https://railway.app/).
3. Create a new project -> Deploy from GitHub repo.
4. Railway will automatically detect the `Dockerfile` and build both the frontend and backend into a single deployable unit.
5. In your Railway project variables, add:
   - `GEMINI_API_KEY`: `<your_api_key>`
6. Deploy and access via the generated public URL!

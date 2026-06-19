# Real Estate AI Shorts Generator (Premium SaaS)

An enterprise-grade, Canva-tier AI platform that empowers Real Estate Agents, Builders, and Marketing Agencies to effortlessly transform raw property footage into high-converting, viral social media shorts. The product bridges the gap between raw assets and published marketing material by replacing tedious manual video editing with intelligent, context-aware AI storytelling and an interactive visual timeline.

## Tech Stack
- **Frontend**: React, Vite, Tailwind CSS, Framer Motion, Shadcn UI
- **Backend**: FastAPI (Python), Motor (Async MongoDB)
- **Database**: MongoDB (Atlas)
- **Auth**: RSA-256 JWT with Refresh Token Rotation
- **AI Engine**: Google Gemini Pro (via Files API) + OpenCV Hybrid Scoring
- **Render Engine**: FFmpeg with Dynamic Crossfade Graph

## Features
- **7-Step Guided Wizard Workflow**: Completely dismantled the massive single-page dashboard into a focused, modern SaaS wizard (Upload -> Analyze -> Storyboard -> Style -> Music -> Generate -> Export).
- **Interactive Wizard Navigation**: The top progress bar is fully clickable, allowing users to seamlessly navigate backwards to previous steps (e.g., jump back to Upload to add a new clip) and return forward, with strict progression validation that prevents skipping ahead into uncompleted stages.
- **Custom Music Engine & Mixing**: Integrated an advanced FFmpeg `amix` pipeline that dynamically loops and mixes background music with the original video audio. Includes a dedicated UI step with volume sliders (0-100%) and an auto-scanning `data/library/music` folder for users to drop in downloaded MP3/WAV files for playable previewing and generation.
- **Premium Canva-style Upload Workflow**: Focused upload screen with animated drag-and-drop zones, explicit URL integrations (Drive, Dropbox, OneDrive), and a dynamic "Upload Complete" success card to keep the workspace clean.
- **Luxury Ocean Aurora Dashboard**: A premium, light-themed workspace inspired by Stripe and Linear. Features an 80px floating top navigation bar and a clean responsive 2-column workspace layout.
- **Authentic Data Visualization**: The UI strictly surfaces real data returned by the backend (e.g. actual extracted clip durations, actual scene types) with zero hardcoded "mock" metrics.
- **Micro-Interactions**: Built heavily with Framer Motion to provide high-end, smooth animations (hover scaling, layout transitions, animated step indicators).

### 1. Premium SaaS Dashboard Experience
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

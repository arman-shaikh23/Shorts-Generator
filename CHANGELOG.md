# Changelog

All notable changes to this project will be documented in this file.

## [17.14.0] - Workflow UX Polish (Toasts + Drill-Down + URL-Synced Views)
### Added
- **Global toast system** (`frontend/src/context/ToastContext.jsx`, `frontend/src/main.jsx`)
  - Added a shared toast provider for success/error/info feedback across authenticated flows.
  - Added toast helpers for standardized messaging and auto-dismiss behavior.
- **Action feedback wiring**
  - `frontend/src/components/layout/TopNav.jsx`: Added create-project success/error toasts.
  - `frontend/src/pages/DashboardPage.jsx`: Added create-project success/error toasts.
  - `frontend/src/pages/HistoryPage.jsx`: Added download success/fallback toasts.
- **Status rail drill-down navigation** (`frontend/src/components/layout/SystemStatusRail.jsx`)
  - Made status buckets clickable for direct operational routing.
  - `done` now routes to `/dashboard/history`.
  - `queued`, `processing`, and `failed` now route to `/dashboard/projects?status=<bucket>&page=1`.

### Changed
- **Projects management UX rewrite** (`frontend/src/pages/ProjectsPage.jsx`)
  - Added URL-synced search/filter/sort/pagination state (`q`, `status`, `sort`, `page`).
  - Added client-safe list filtering/sorting and paged grid navigation.
  - Added filtered metrics strip and improved no-results reset actions.
- **History management UX rewrite** (`frontend/src/pages/HistoryPage.jsx`)
  - Added URL-synced search/filter/sort/pagination state (`q`, `style`, `sort`, `page`).
  - Added client-safe list filtering/sorting and paged reel grid navigation.
  - Kept direct reel video thumbnails (removed custom poster dependency); cards use inline video preview with `preload="metadata"`.

### Documentation
- **README.md**
  - Added feature notes for global toasts, status drill-down navigation, and URL-synced Projects/History controls.
- **PROMPTS.md**
  - Added Prompt 0.11 for frontend workflow polish implementation policy.

### Validation
- Frontend build: passed (`npm run build`).

## [17.13.0] - UX Reliability Pass (Status Rail + Empty-State Guidance + Video Performance)
### Added
- **Persistent system-status rail** (`frontend/src/components/layout/SystemStatusRail.jsx`)
  - Added shared status rail across authenticated pages (`/dashboard`, `/dashboard/projects`, `/dashboard/history`).
  - Added live lifecycle buckets: `queued`, `processing`, `failed`, `done`.
  - Added latest activity timestamps and quick recovery actions (`Retry Failed`, `Resume Processing`, `Continue Setup`, `Open History`).
  - Added auto-refresh polling (30s) and manual refresh control.

### Changed
- **Authenticated layout integration** (`frontend/src/App.jsx`)
  - Mounted status rail in `DashboardLayout` so monitoring remains visible while navigating between pages.
- **Projects empty-state onboarding UX** (`frontend/src/pages/ProjectsPage.jsx`)
  - Added startup checklist and guided next-step links to reduce dead-end behavior.
- **History empty-state onboarding UX** (`frontend/src/pages/HistoryPage.jsx`)
  - Added first-export checklist and guided CTAs back to the production flow.
- **Video performance pass**
  - `frontend/src/components/dashboard/DemoVideoCard.jsx`: Added viewport-triggered lazy loading via `IntersectionObserver`, poster-first behavior, and reduced-motion-aware autoplay gating.
  - `frontend/src/pages/HistoryPage.jsx`: Reel cards switched to `preload="none"` with poster fallback.
  - `frontend/src/pages/LandingPage.jsx`: Tutorial video switched to `preload="none"`.
  - `frontend/src/pages/ProjectDetailPage.jsx`: Preview/storyboard videos switched to `preload="none"` and final result player to `preload="metadata"`.
  - `frontend/src/components/HowItWorksModal.jsx`: Modal player explicitly set to `preload="metadata"`.
- **Dashboard quick actions cleanup** (`frontend/src/pages/DashboardPage.jsx`)
  - Removed `API Docs` quick action as requested.

### Documentation
- **README.md**
  - Added UX reliability features: persistent status rail, empty-state onboarding, and video performance pass.
- **PROMPTS.md**
  - Added Prompt 0.10 for frontend UX reliability implementation policy.

### Validation
- Frontend build: passed (`npm run build`).

## [17.12.0] - YouTube URL Upload Support (`/uploads`)
### Added
- **YouTube ingestion path in downloader** (`backend/services/video.py`)
  - Added YouTube URL detection for `youtube.com` / `youtu.be` hosts.
  - Added `yt-dlp` based media download path for YouTube sources.
  - Enforced single-video behavior for YouTube URLs (`noplaylist`).
  - Added clearer runtime errors for downloader failures and missing output files.
- **Configuration controls** (`backend/app/core/config.py`)
  - Added `YTDLP_COOKIES_FILE` for optional cookie-authenticated downloads.
  - Added `YOUTUBE_MAX_DURATION_SEC` for optional max source duration caps.
- **Environment templates**
  - Added YouTube downloader env settings to:
    - `backend/.env.example`
    - `backend/.env.small`
    - `backend/.env.large`
- **Dependency**
  - Added `yt-dlp` to `backend/requirements.txt`.

### Changed
- **Uploads URL intake hardening** (`backend/app/api/uploads.py`)
  - Added `http(s)` URL validation for URL-based uploads.
  - Added filename inference for remote URLs.
  - Added YouTube-specific filename normalization (`youtube_<video_id>.mp4`).
- **Frontend URL upload UX** (`frontend/src/pages/ProjectDetailPage.jsx`)
  - URL import messaging now explicitly includes YouTube support.
  - URL add flow now surfaces backend validation/downloader errors to the user instead of a generic message.

### Documentation
- **README.md**
  - Added Remote URL Ingestion section for YouTube and direct-link uploads.
  - Added env variable documentation for `YTDLP_COOKIES_FILE` and `YOUTUBE_MAX_DURATION_SEC`.
- **PROMPTS.md**
  - Added Prompt 0.9 for production-safe YouTube ingestion design.

## [17.11.0] - Single Full-Tour Video Support (1 Processed Upload)
### Changed
- **Backend analysis minimum-input gate** (`backend/app/api/generation.py`)
  - Updated analysis precheck from `>= 3 processed clips` to `>= 1 processed clip`.
  - Single full home-tour upload can now enter AI analysis without additional filler uploads.
- **Frontend wizard validation alignment** (`frontend/src/pages/ProjectDetailPage.jsx`)
  - Updated Analyze-step guard from 3 processed clips to 1 processed clip.
  - Prevents UI/backend mismatch for single-upload projects.
- **Gemini analysis instruction update** (`backend/services/gemini.py`)
  - Added explicit single-video guidance to extract up to 3 distinct, non-overlapping peak segments from one `video_index`.

### Documentation
- **README.md**
  - Added "Single-Video Full Tour Support" capability note under AI engine features.
- **PROMPTS.md**
  - Added "SINGLE-VIDEO SUPPORT" rule to the multi-segment analysis prompt example.
  - Added a key-changes row documenting single-upload project support.

## [17.10.0] - Idempotency for JSON Write Operations
### Added
- **Idempotency core module**: `backend/app/core/idempotency.py`
  - Supports `Idempotency-Key` and `X-Idempotency-Key` headers.
  - Canonical request hashing to bind a key to one payload.
  - Mongo-backed idempotency lifecycle: `IN_PROGRESS`, `COMPLETED`, `FAILED`.
  - Replay support for completed requests using stored response payload.
- **Idempotency storage indexes** in `backend/app/core/database.py`:
  - `idemp_user_endpoint_key_uq` (unique): `(user_id, endpoint, key)`
  - `idemp_expires_ttl` (TTL): `expires_at`
  - `idemp_status_updated_idx`: `(status, updated_at)`

### Changed
- **Projects API idempotency coverage** (`backend/app/api/projects.py`)
  - `POST /api/v1/projects`
  - `PATCH /api/v1/projects/{project_id}`
  - `DELETE /api/v1/projects/{project_id}`
- **Uploads API idempotency coverage** (`backend/app/api/uploads.py`)
  - `POST /api/v1/projects/{project_id}/uploads`
  - `POST /api/v1/projects/{project_id}/uploads/file`
  - `POST /api/v1/projects/{project_id}/uploads/music`
  - `PATCH /api/v1/projects/{project_id}/uploads/reorder`
  - `DELETE /api/v1/projects/{project_id}/uploads/{upload_id}`
- **Health index diagnostics** (`backend/app/api/health.py`)
  - Added `idempotency_keys` expected index set to `/api/v1/health/indexes` report.
- **API tests**
  - Updated `backend/tests/api/test_endpoints.py` to assert `idempotency_keys` in index diagnostics collections.
- **Documentation updates**
  - `README.md`: added full idempotency usage guide for write retries.
  - `PROMPTS.md`: added Prompt 0.8 for idempotency implementation policy.

### Validation
- Backend tests: `53 passed` after idempotency integration.

## [17.9.0] - Index Diagnostics Endpoint (`/api/v1/health/indexes`)
### Added
- **Read-only index diagnostics endpoint** in `backend/app/api/health.py`:
  - `GET /api/v1/health/indexes`
  - Returns per-collection `expected_indexes`, `actual_indexes`, and `missing_indexes`.
  - Returns aggregate status (`ok` / `degraded`) and `missing_total`.
  - Covers critical collections: `users`, `refresh_tokens`, `projects`, `uploads`, `generated_shorts`.
- **API test coverage**
  - Added `test_index_health_endpoint` in `backend/tests/api/test_endpoints.py`.
  - Verifies response payload shape and critical collection presence.

### Changed
- **Documentation updates**
  - `README.md`: Database Indexing section now includes diagnostics endpoint usage.
  - `PROMPTS.md`: added Prompt 0.7 for index health visibility and verification workflow.

### Validation
- Backend tests: `53 passed` after index diagnostics endpoint integration.

## [17.8.0] - MongoDB Indexing for Hot Query Paths
### Added
- **Startup index bootstrap** in `backend/app/core/database.py`
  - Added `ensure_database_indexes(...)` to create indexes during Mongo connection startup.
  - Added safe index creation helper with structured warning logs (`[MONGO INDEX]`) on failures.
- **Indexes for core query patterns**
  - `users.email` unique index for auth lookup.
  - `refresh_tokens.token` unique index for token lookup.
  - `refresh_tokens.expires_at` TTL index for automatic expired-token cleanup.
  - `refresh_tokens.family + is_revoked` and `refresh_tokens.user_id + is_revoked` for revocation flows.
  - `projects.userId + updatedAt(desc)` for projects listing.
  - `uploads.projectId + order` for ordered upload list/tail queries.
  - `uploads.projectId + status + order`, `uploads.status + uploadedAt`, `uploads.userId + status` for worker and status/count paths.
  - `generated_shorts.userId + createdAt(desc)` and `generated_shorts.projectId` for history and project-level generated queries.

### Changed
- **Mongo connection startup flow**
  - `connect_to_mongo()` now ensures indexes immediately after successful DB initialization.
- **Documentation updates**
  - `README.md`: added "Database Indexing (Query Performance Layer)" with strategy and operational notes.
  - `PROMPTS.md`: added Prompt 0.6 for index-driven performance hardening.

### Validation
- Backend tests: `52 passed` after index bootstrap integration.

## [17.7.0] - Strict Video Upload Validation (10GB Single File + Non-Video Rejection)
### Added
- **Video input validation layer** in `backend/app/api/uploads.py` for `POST /api/v1/projects/{project_id}/uploads/file`:
  - Extension allowlist (`.mp4`, `.mov`, `.mkv`, `.avi`, `.webm`, `.m4v`).
  - Content-Type guard rejecting image payloads (`image/*`) so `.jpg/.jpeg/.png` cannot be uploaded as videos.
  - Post-save media verification via `ffprobe` to ensure uploaded payload contains a real video stream.
  - Explicit `415 Unsupported Media Type` errors for invalid media types.

### Changed
- **Single video size cap default**:
  - `MAX_VIDEO_UPLOAD_BYTES` changed to `10737418240` (10GB) in:
    - `backend/app/core/config.py`
    - `backend/.env.example`
    - `backend/.env.small`
    - `backend/.env.large`
- **Documentation updates**:
  - `README.md`: clarified single-file 10GB cap and video validation/rejection behavior.
  - `PROMPTS.md`: strengthened Prompt 0.5 with 10GB single-file and non-video rejection requirements.

## [17.6.0] - Streaming Large Uploads (Chunked, Memory-Safe API Boundaries)
### Added
- **Streaming upload controls in config** (`backend/app/core/config.py`)
  - `UPLOAD_STREAM_CHUNK_SIZE`
  - `MAX_VIDEO_UPLOAD_BYTES`
  - `MAX_MUSIC_UPLOAD_BYTES`
- **Reusable streaming helper** in `backend/app/api/uploads.py`
  - `stream_upload_to_disk(...)` writes uploads chunk-by-chunk using async file I/O.
  - Enforces endpoint-level max size limits with explicit `413` responses.
  - Cleans up partial files on error and rejects empty uploads.
- **Environment template updates**
  - Added streaming upload settings to:
    - `backend/.env.example`
    - `backend/.env.small`
    - `backend/.env.large`

### Changed
- **Uploads API** (`backend/app/api/uploads.py`)
  - `POST /api/v1/projects/{project_id}/uploads/file` no longer uses full in-memory reads.
  - `POST /api/v1/projects/{project_id}/uploads/music` no longer uses full in-memory reads.
  - Both endpoints now stream chunks directly to disk and rely on configurable limits.
- **Documentation**
  - `README.md`: Added a dedicated "Streaming Uploads (Large Files)" section with behavior and env settings.
  - `PROMPTS.md`: Added Prompt 0.5 for memory-safe, chunked upload boundary design.

### Validation
- Backend tests: `52 passed` after streaming-upload refactor.
  
## [17.5.0] - Redis Cache-Aside Layer with TTL and Versioned Invalidation
### Added
- **Redis cache core module**: `backend/app/core/cache.py`
  - Feature-flagged cache enablement (`ENABLE_REDIS_CACHE`).
  - Cache-aside helpers (`cache_get`, `cache_set`) with JSON serialization and TTL.
  - Versioned namespace key strategy for invalidation (`INCR`) across:
    - user projects list
    - user history list
    - user dashboard stats
    - project detail
    - project uploads list
  - Read-key builders for projects, history, uploads, stats, and music library cache.
  - Mutation invalidation helpers for project/upload/generation/delete flows.
- **Redis dependency** in `backend/requirements.txt` (`redis`).
- **Cache configuration settings** in `backend/app/core/config.py` and env templates:
  - `ENABLE_REDIS_CACHE`, `REDIS_URL`, `REDIS_MAX_CONNECTIONS`
  - `REDIS_CONNECT_TIMEOUT_SEC`, `REDIS_READ_TIMEOUT_SEC`
  - `CACHE_DEFAULT_TTL_SEC`
  - `CACHE_TTL_PROJECTS_SEC`, `CACHE_TTL_PROJECT_DETAIL_SEC`
  - `CACHE_TTL_HISTORY_SEC`, `CACHE_TTL_UPLOADS_SEC`
  - `CACHE_TTL_DASHBOARD_STATS_SEC`, `CACHE_TTL_MUSIC_LIBRARY_SEC`
  - `CACHE_VERSION_TTL_SEC`
- **New unit tests**: `backend/tests/unit/test_cache.py`
  - validates cache set/get behavior
  - validates TTL propagation
  - validates version bump invalidation behavior

### Changed
- **App lifecycle** (`backend/main.py`)
  - Added Redis cache connect/close in startup/shutdown.
  - Added cache-aside for `/api/v1/music-library`.
- **Projects API** (`backend/app/api/projects.py`)
  - Added cache-aside for list/detail/dashboard stats endpoints.
  - Added invalidation on create/update/delete mutations.
- **History API** (`backend/app/api/history.py`)
  - Added cache-aside for paginated history endpoint.
- **Uploads API** (`backend/app/api/uploads.py`)
  - Added cache-aside for full and paginated list modes.
  - Added invalidation on add/file/delete/reorder mutations.
- **Generation API** (`backend/app/api/generation.py`)
  - Added invalidation after analysis timeline update.
  - Added invalidation after successful reel generation writes.

### Validation
- Backend tests: `52 passed` after Redis cache integration.
- Frontend build: passed (`npm run build`).

## [17.4.0] - Pagination Standardization for Projects, History, and Uploads
### Added
- **Shared pagination utility**: `backend/app/core/pagination.py`
  - `normalize_limit(...)` for safe bounded limits.
  - `resolve_page_skip(...)` for page/skip interoperability.
  - `build_pagination_meta(...)` for consistent metadata (`total`, `page`, `limit`, `skip`, `pages`, `has_next`, `has_prev`, `next_page`, `prev_page`, `next_skip`, `prev_skip`).
- **New unit tests**: `backend/tests/unit/test_pagination.py` for pagination helper behavior.
- **Frontend pagination controls**
  - Projects page now fetches paginated data and renders Prev/Next controls.
  - History page now fetches paginated data and renders Prev/Next controls.

### Changed
- **Projects API** (`backend/app/api/projects.py`)
  - Added `page` query support while preserving existing `skip` and `limit`.
  - Response now includes standardized pagination metadata (additive, non-breaking).
- **History API** (`backend/app/api/history.py`)
  - Added `skip` query support in addition to `page` and `limit`.
  - Response now uses shared standardized pagination metadata.
- **Uploads API** (`backend/app/api/uploads.py`)
  - Added optional paginated mode (`paginate=true` or `page/skip/limit` supplied).
  - Preserved backward-compatible full-list behavior when no pagination params are passed.
  - Added standardized pagination metadata fields in both modes.

### Validation
- Backend tests: `49 passed` after pagination integration.
- Frontend build: passed (`npm run build`).

## [17.3.0] - Pool Observability, Diagnostics Endpoint, and Env Presets
### Added
- **Pool Observability Module**: `backend/app/core/pool_observability.py`
  - Tracks pooled HTTP request telemetry (`requests_total`, latency stats, timeout class counters, error counters).
  - Tracks Mongo telemetry (connect/ping latency, checkout wait metrics, checkout timeout counters, pool lifecycle event counters).
  - Exposes a combined diagnostics snapshot API for operational health reporting.
- **Read-only diagnostics endpoint**: `GET /api/v1/health/pools`
  - Implemented via `backend/app/api/health.py` and router registration in `backend/main.py`.
  - Returns `status`, `issues`, and detailed `http_pool` / `mongo_pool` snapshots.
- **Environment sizing presets**
  - `backend/.env.small` for low-concurrency deployments.
  - `backend/.env.large` for high-concurrency deployments.
  - Presets retain safe V2 defaults to preserve current production behavior.
- **Tests**
  - Added `backend/tests/unit/test_pool_observability.py`.
  - Extended `backend/tests/api/test_endpoints.py` with pool diagnostics endpoint coverage.

### Changed
- **Mongo connection setup** (`backend/app/core/database.py`)
  - Wired in observability configuration and event listeners when available.
  - Added startup connect/ping latency capture and failure metrics.
  - Added explicit pool close state tracking.
- **HTTP client module** (`backend/app/core/http_client.py`)
  - Added pooled stream helper with automatic metrics capture (`stream_with_pool_metrics`).
  - Added lifecycle metrics updates during startup/shutdown.
- **Download pipeline** (`backend/services/video.py`)
  - Switched to observability-enabled pooled HTTP streaming helper.
  - Added explicit timeout logging and failure mapping for pooled/network timeout conditions.
- **Env template note** (`backend/.env.example`)
  - Added pointer to `.env.small` and `.env.large` presets.

### Validation
- Backend tests: `44 passed` after observability + diagnostics integration.

## [17.2.0] - Connection Pooling for DB and Outbound HTTP
### Added
- **MongoDB Pool Controls** in `backend/app/core/config.py`:
  - `MONGO_MAX_POOL_SIZE`
  - `MONGO_MIN_POOL_SIZE`
  - `MONGO_MAX_IDLE_TIME_MS`
  - `MONGO_WAIT_QUEUE_TIMEOUT_MS`
  - `MONGO_SERVER_SELECTION_TIMEOUT_MS`
- **Shared HTTP Client Pool Controls** in `backend/app/core/config.py`:
  - `HTTP_POOL_MAX_CONNECTIONS`
  - `HTTP_POOL_MAX_KEEPALIVE_CONNECTIONS`
  - `HTTP_CONNECT_TIMEOUT_SEC`
  - `HTTP_READ_TIMEOUT_SEC`
  - `HTTP_WRITE_TIMEOUT_SEC`
  - `HTTP_POOL_TIMEOUT_SEC`
- **App-level pooled HTTP client module**: `backend/app/core/http_client.py`
  - Single reusable `httpx.AsyncClient` with configured limits and timeout budget.

### Changed
- **Mongo initialization** (`backend/app/core/database.py`):
  - `AsyncIOMotorClient` now uses explicit pool settings and logs active pool config at startup.
- **FastAPI lifespan** (`backend/main.py`):
  - Added startup initialization and shutdown cleanup for shared HTTP client pool.
- **Video download path** (`backend/services/video.py`):
  - Replaced per-call `httpx.AsyncClient(...)` creation with shared pooled client usage.
- **Environment template** (`backend/.env.example`):
  - Added Mongo and HTTP pooling tunables with safe defaults.

### Validation
- Backend tests: `40 passed` after pooling integration.

## [17.1.0] - Safe Quality V2 Foundation (Feature-Flagged)
### Added
- **Quality V2 Feature Flags** in backend config and `.env.example`:
  - `PIPELINE_SHADOW_MODE`
  - `ENABLE_STABILITY_V2`, `ENABLE_TRIM_V2`, `ENABLE_STORY_V2`, `ENABLE_SCORING_V2`, `ENABLE_DEDUP_V2`, `ENABLE_TRANSITION_V2`
  - `V2_MIN_TRIM_CONFIDENCE`, `V2_MIN_STORY_CONFIDENCE`
  - V2 score weight controls (`V2_STABILITY_WEIGHT`, `V2_CINEMATIC_WEIGHT`, `V2_STORY_WEIGHT`, `V2_ROOM_UNIQUENESS_WEIGHT`, `V2_TRANSITION_WEIGHT`)
- **New service module**: `backend/services/quality_v2.py`
  - Stability analysis metadata: `stability_score_v2`, `motion_variance`, `camera_shake_score`, `optical_flow_consistency`, `rotation_stability`, `translation_stability`
  - Trim recommendation engine: `recommended_trim_start/end`, `trim_confidence`, `trim_reason_codes`, fallback handling
  - Story classification and ordering helpers with confidence-gated fallback
  - Near-duplicate perspective penalty layer (non-destructive)
  - Extended scoring metadata (`final_score_v2`, `room_uniqueness_score`, `transition_quality_score`, `cinematic_score`)

### Changed
- **Generation pipeline** (`backend/app/api/generation.py`):
  - Added V2 metadata capture path (safe additive behavior).
  - Added optional V2 trim promotion controlled by confidence + feature flag.
  - Added quality options wiring into `TimelineOptimizer.optimize(...)`.
  - Added `aiMetadata.quality_v2` summary for observability.
- **Timeline optimizer** (`backend/services/timeline_optimizer.py`):
  - Added optional V2 dedup penalty pass.
  - Added optional V2 story ordering pass with confidence fallback.
  - Added optional V2 scoring metadata pass.
  - Preserved existing V4 flow and legacy behavior by default.

### Tests
- Added `backend/tests/unit/test_quality_v2.py` covering:
  - story classification
  - transition quality logic
  - story ordering fallback behavior
  - near-duplicate penalties
  - scoring v2 fields
  - trim recommendation behavior
- Extended `backend/tests/unit/test_video_services.py` with optimizer V2 integration assertions.
- Validation results:
  - Backend: `40 passed`
  - Frontend lint: passed
  - Frontend unit tests: passed
  - Playwright E2E: passed

## [17.0.0] - ReelForge Master Quality Upgrade V4.0
### Added
- **Story Arc Engine**: Replaced flat zone-based walkthrough with emotionally-paced 4-phase arc: HOOK (15%) → DISCOVERY (35%) → SHOWCASE (35%) → RESOLUTION (15%). Clips are now mapped to emotional phases for maximum viewer retention.
- **Property Highlight Memory Module**: Pre-scans all ingested media to cache `hero_pool`, `hero_exterior`, `hero_view`, `hero_living_room` for strategic placement. Hook deploys hero_exterior, mid-reel anchors hero_living_room, climax deploys hero_pool + drone pull-away.
- **Peak Window Detection**: V4.0 scoring formula: `window_score = (0.30 × luxury) + (0.25 × reveal) + (0.20 × composition) + (0.15 × motion) + (0.10 × lifestyle)`. Replaces flat hybrid scoring.
- **Repetition Memory Engine**: 5-clip lookback window with -30 point penalty for repeated `scene_type`. Eliminates `Exterior → Exterior → Exterior` and `Pool → Pool` repetition patterns.
- **Motion Diversity Tracking**: Deducts 30 points for 3+ consecutive identical `camera_motion`, `camera_direction`, or `shot_size`. Enforces kinetic variety.
- **Quality-First Priority Matrix**: Quality → Story → Coverage operational hierarchy. Clips are never included solely to satisfy an arbitrary coverage metric.
- **Expanded Hero Protection**: Immutability flag for clips with `hero_score ≥ 90 OR reveal_score ≥ 90 OR luxury_score ≥ 90`. Pacing can adjust duration but cannot drop.
- **Enhanced Adjacency Scoring**: Bumped natural transition bonuses to +25 (Living Room → Dining) and jarring jump penalties to -50 (Bathroom → Kitchen). Soft Recovery skips missing room types gracefully.
- **Contextual Clip Duration Rules**: Standard clips: 4-7s, Hero clips: 7-10s, Premium Aerial/Drone: 10-12s.
- **Premium Closing Shot Architecture**: Mandatory hierarchy: Pool View → Best Exterior → Drone Pull-Away. Strict prohibition on bathroom/closet/kitchen endings.
- **Multi-Variant Style Profiles**: `luxury_tour` (100% preservation, 1.0 pace), `premium_realtor` (90-100%, 0.85 pace), `instagram_viral` (70-80%, 0.60 pace).
- **Lucas-Kanade Optical Flow**: `cv2.calcOpticalFlowPyrLK()` detection and trimming of drone takeoff shake, gimbal initialization anomalies, autofocus loops, and exposure hunting.
- **Intelligent Media Filtering**: Lowered acceptance floor to ≥720p (many premium assets from messaging apps are compressed). Only rejects corrupted files or extreme blur (Laplacian < 20).
- **OpenCV Multi-Threading**: All CPU-intensive CV operations wrapped in `asyncio.to_thread()` behind `cv_semaphore = asyncio.Semaphore(3)` for non-blocking FastAPI execution.
- **Fault-Tolerant Render Audit Gate**: 3-tier status matrix: ≥95% → PASS (deliver), 90-94.9% → WARNING (log + deliver), <90% → FAIL (halt delivery for reprocessing).
- **Gemini V4.0 Prompt**: Added `reveal_score` (0-100) and `lifestyle_score` (0-100) to the Gemini response schema. Rewritten prompt with quality-first hierarchy, peak window detection, and duration rules.

### Changed
- **Timeline Optimizer**: Complete V4.0 rewrite with Story Arc builder, Repetition Memory, Motion Diversity, and resort-after-penalties pipeline.
- **CV Analyzer**: Added `detect_camera_adjustments()` and `check_media_quality()` functions alongside existing `analyze_video_segment()`.
- **Generation API**: Integrated Lucas-Kanade detection, Property Highlight Memory, and CV semaphore throttling into the analysis pipeline.
- **Render Audit**: Upgraded from simple percentage check to 3-tier PASS/WARNING/FAIL gate with `audit_status` field persisted to MongoDB.

## [16.0.0] - Comprehensive Testing Framework & API Documentation
### Added
- **Swagger UI Integration**: Added frontend integration for Swagger UI at `/api-docs` using `swagger-ui-react`, allowing users to explore and test the FastAPI backend directly from the React web app.
- **Unit Testing**: Isolated testing for individual functions and UI components using Pytest (Backend) and Vitest (Frontend).
- **Integration Testing**: Verification of data flow between modules, API routes, and React components.
- **System Testing**: Playwright-based testing covering the complete application as a whole against specified requirements.
- **User Acceptance Testing (UAT)**: Scenario-based tests mapped to business requirements and real-world Realtor workflows.
- **Smoke & Sanity Testing**: Fast Playwright verification suites to ensure the core build is stable and recent changes are valid.
- **Interface & API Testing**: Automated verification of FastAPI interactions, requests, and responses using `httpx`.
- **Regression Testing**: Protected functionality baselines to ensure future updates don't break the existing timeline optimization engine.

## [15.0.0] - ReelForge Cinematic Engine v9 (Critical Reel Quality Upgrade)
### Added
- **Strict Walkthrough Mode**: Enforced a hard real-estate walkthrough sequence for Luxury/Realtor styles: Drone → Exterior → Entrance → Lobby → Living Room → Dining → Kitchen → Master Bedroom → Bedroom → Bathroom → Balcony → Pool → Gym → Garden → Amenities → Parking → Closing. Missing scenes are skipped, never reordered backwards.
- **Story Zones**: Clips are now grouped into 4 cinematic zones: `OPENING` (drone/aerial/exterior/entrance), `INTERIOR` (lobby through bathroom), `AMENITIES` (pool/gym/garden/parking), `CLOSING` (closing exterior/drone). Each zone is assembled in order for natural storytelling.
- **Flexible Mode for Instagram/Viral**: Instagram and Viral styles use hero-score ordering with scene diversity instead of strict walkthrough, prioritizing attention over tour order.
- **Room Continuity Scoring**: Natural room-to-room transitions receive bonuses (e.g., Living Room → Kitchen: +10), while unnatural jumps receive penalties (e.g., Kitchen → Pool: -15).
- **Hero Clip Protection**: Clips with `hero_score >= 90` are now NEVER removed from the timeline, regardless of other quality scores, unless the file is physically missing or corrupted.
- **Unique `clip_id` System**: Every clip now gets a unique identifier (`{video_index}_{start}_{end}`) enabling multi-segment extraction where a single uploaded video can contribute up to 3 distinct scenes.
- **Multi-Segment Extraction**: Gemini can now extract multiple usable segments from a single video (e.g., lobby at 3-7s, entrance at 10-15s). Capped at `MAX_SEGMENTS_PER_VIDEO = 3`.
- **Sequence Validation**: Post-optimization `validate_storyline()` enforces 4 rules: no backward movement, max 3 same-type consecutive clips, drone only in opening/closing, bathroom never before living room.
- **Full Render Audit with Duration Coverage**: `build_reel()` now returns a comprehensive audit dict tracking `selected_count`, `rendered_count`, `selected_duration`, `rendered_duration`, `duration_coverage_pct`, and `skipped_clips` with reasons.
- **Render Fail Threshold**: Generation automatically alerts if `rendered_count < selected_count * 0.9` (less than 90% of clips rendered).
- **Detailed Skip Reasons**: Every skipped clip is logged with a specific reason: `missing_file`, `ffmpeg_timeout`, `decode_error`, `ffmpeg_error`.
- **Expanded Scene Types**: Added `home_office`, `conference_room`, `corridor`, `staircase`, `walk_in_closet`, `terrace`, `rooftop` to the walkthrough order and Gemini prompt.

### Changed
- **ALL-Clips Variation Rendering**: Variations now MUST include every approved timeline clip. `custom_sequence` only controls ordering, never removal. Missing clips are appended in original timeline order.
- **Variations use `clip_id` strings** instead of `video_index` integers, preventing multi-segment clips from overwriting each other.
- **Removed `MAX_CLIP_DURATION = 10.0` double-cap** from `build_reel()` — the timeline optimizer already enforces smart duration bounds (4-12s based on score and scene type).

### Fixed
- **85s → 25s Duration Bug**: Root cause was `generate_variations()` cherry-picking only 6 of 19 clips. Now all clips are always included.
- **Server Crash Prevention**: Background tasks (`upload_worker`, `daily_cleanup`) are now wrapped in `safe_background_task()` that auto-restarts on crash instead of killing the event loop.
- **FFmpeg Deadlock Prevention**: Added 120-second timeout to all FFmpeg subprocess calls. Hung processes are killed and the clip is skipped instead of blocking all renders.
- **Ctrl+C Immediate Kill**: `SIGINT` handler calls `os._exit(0)` to bypass hanging Gemini threads.

## [14.0.0] - ReelForge Cinematic Engine v8
### Added
- **Cinematic Timeline Optimizer**: Added a new Python backend module (`timeline_optimizer.py`) to programmatically polish the final video reel timeline, fixing camera stability and visual flow.
- **Advanced Metadata Extraction**: Gemini now extracts `camera_motion`, `camera_direction`, `shot_size`, `stability_score`, `hook_score`, and `luxury_score` for every clip.
- **Strict Pre-Trim Rules**: The backend automatically enforces a 3.0s minimum safe start to the start of every selected clip to absolutely eliminate camera shake, autofocus hunting, and gimbal calibration movements.
- **Maximized Property Coverage**: Eliminated subjective visual deduplication (pHash). The pipeline now preserves unique camera angles and room perspectives, guaranteeing maximum property coverage (e.g. 18-21 unique videos used if uploaded).
- **Target Selection Range**: Gemini now instructed to search the `3s-8s` safe zone of videos instead of automatically capturing from 0.0s.
- **Premium Dashboard Hero Redesign**: The dashboard has been upgraded to a 2-column SaaS layout. It now features an animated, glassmorphism Demo Video Card on the right side, showing a looping showcase of ReelForge in action (raw clips to cinematic reel), highlighting core AI features automatically.
- **Single Active Video Playback**: Enhanced the user experience across the Dashboard and History pages. Starting a new reel now automatically pauses all other videos on the page and resets their playback position to prevent overlapping audio.
- **Hybrid OpenCV/Gemini Scoring**: Offloaded mathematical physics tasks (motion blur, heavy shake, gimbal stability, exposure) to OpenCV (`cv_analyzer.py`), leaving Gemini strictly to handle aesthetic metadata (`composition`, `luxury_score`). Both engines merge scores to compute a master `final_score` for the timeline builder.
- **Phase 5 Render Coverage Audit**: Introduced a new backend verification stage that dynamically compares `selected_clips` vs `rendered_clips` after FFmpeg concatenation. Automatically logs missing clips, enabling fast debugging of missing renders or timeline overlaps.
- **Dynamic Pre-Trim Skipping**: Ripped out the hardcoded 3-second start buffer. The system now uses OpenCV to mathematically analyze the first `0-3` seconds of a clip. It only trims the start if it detects physical instability (acceleration, calibration, exposure pumps). Otherwise, 0.0s is preserved.
- **Dynamic Cinematic Pacing**: Completely removed fixed target reel durations. Final pacing now uses intelligent boundaries: 4-7s (Default), 7-10s (Hero clips), and up to 12s (Exceptional Drones) to maintain momentum without forcing length.
- **Maximum Coverage Strategy**: The system now preserves unique videos aggressively, aiming for a 90-100% preferred coverage target. It will only drop videos if their `final_score` mathematically fails, ensuring high quality footage is never discarded randomly.
- **Extended Clip Limits**: Clip constraints have been widened. Preferred clip length is now 5-8s, with Hero scenes extending up to 6-10s. The absolute ceiling for a single clip is now 10s. Weak clips are softly trimmed to 4-5s.
- **Scene Diversity Constraints**: Added hard caps and scoring penalties to strictly prevent repetitive shots: max 2 contiguous exterior shots, max 2 drone shots, and max 2 shots from the exact same room category in a row.
- **Camera Continuity logic**: Sequences clips based on camera direction (e.g., `left_to_right`) to prevent jarring visual jumps, penalizing abrupt reverses in motion.
- **Verbose Debugging**: Explicit reasoning is now logged for every single clip removed from the pipeline.

## [13.0.0] - ReelForge Story Engine v7 (Unlimited Duration & Loop Closure)
### Changed
- **Unlimited Duration Algorithm**: Removed the 30-60 second artificial constraint for short videos. The AI is now instructed to utilize all non-duplicate uploaded clips, rendering a video that is exactly as long as necessary to showcase every important room.
- **Strict Semantic Ordering**: Refined the API and Render pipeline to strictly ignore raw AI confidence sorting and force a chronological property tour: Drone -> Aerial -> Exterior -> Entrance -> Lobby -> Living Room -> Kitchen -> Bedroom -> Bathroom -> Amenities -> Closing.
- **Loop Closure System**: Added a programmatic loop generator in the FFmpeg render pipeline. The system now takes the very first opening clip, cuts a 2.0-second snippet, and appends it to the very end of the reel. This creates a perfect loop effect when uploaded to Shorts/Reels/TikTok.

## [12.0.0] - ReelForge Story Engine v6 (Diversity & Roles Refactor)
### Changed
- **Scene Role Classification**: The AI now tags every clip with a structural structural role (e.g. `OPENING`, `LOBBY`, `CLOSING`) ensuring chronological property tours that don't feel like random clip collections.
- **Strict Opening/Closing Diversity**: Enforced the rule `opening_scene_id != closing_scene_id`. The engine is now hard-coded to never reuse the opening clip as the closing shot, forcing it to fetch a new clip (e.g. from Video B if Video A was used for the hook).
- **Explicit Reuse Protection**: Added direct commands to the AI internally tracking `scene_id` and `video_id` to prevent the same temporal segment from appearing twice unless specifically requested.

## [11.0.0] - ReelForge Story Engine v5 (Duration-First Refactor)
### Changed
- **Duration-First Algorithm**: The Gemini AI Engine no longer arbitrarily selects clips. It now calculates a strict "Duration Budget" (Shorts: max 60s, YouTube: scales up to 240s based on footage) and intelligently sums clip extractions (e.g., 4s + 3s + 5s) until the precise duration budget is hit.
- **Chronological Property Sequencing**: Rewrote the core logic to strictly override visual quality scores with logical property tour storytelling. It forces the sequence: Drone -> Exterior -> Entrance -> Lobby -> Living Room -> Dining -> Kitchen -> Bedroom -> Bathroom -> Balcony -> Pool -> Gym -> Garden -> Parking -> Closing Drone.
- **Platform Specific Pacing**: The AI now understands explicit timeline pacing. For example, Shorts videos enforce a 5-second "Hook" phase, 15-second "Main Property" phase, and 20-second "Best Rooms" phase.
- **Opening Shot Enforcement**: Hardcoded restrictions to prevent Bathrooms or Parking areas from ever being the opening shot. The opening shot is now locked to Drone, Exterior, or Luxury shots with a fixed 5-7 second duration.

## [10.1.0] - Automated Storage Cleanup & 3-Stage Deduplication
### Added
- **Aggressive Storage Cleanup Pipeline**: Added `app/core/cleanup.py` daily background worker that purges orphaned temporary files older than 24 hours. Additionally, `video.py` now destroys intermediate FFmpeg clips (`clip_X.mp4`) instantly after a reel compiles. Finally, deleting a project now securely wipes its entire filesystem `data/` directory.
- **3-Stage Pre-Processor Deduplication Engine**: Videos are now filtered *before* AI analysis to save tokens and guarantee duplicate removal.
  1. **Stage 1 (SHA256 Hash)**: Instantly catches exact identical files.
  2. **Stage 2 (3-Frame pHash)**: Extracts Beginning, Middle, and End frames, computing the Hamming distance to catch >95% perceptual matches.
  3. **Stage 3 (Local SSIM)**: Uses OpenCV & skimage Structural Similarity to structurally compare the raw pixel layouts.
- **Duplicate Audit Panel**: The Analysis transparency UI now breaks down exact duplicates caught by the Local Engine versus semantic duplicates removed by the AI.

## [10.0.0] - Custom Music Engine & Strict Shorts Duration Fix
### Added
- **Dynamic Custom Music Library**: Added a new "Music Selection" Step (Step 5) in the workflow. Users can now drop downloaded MP3/WAV files directly into `backend/data/library/music`, and the frontend will automatically scan and display them in a playable library.
- **Interactive Wizard Navigation**: The top progress bar is now fully clickable. Users can instantly navigate backwards to previous steps (e.g., jumping from Style back to Upload to add a new clip) and seamlessly return forward, with strict "highest step reached" validation preventing them from skipping ahead into uncompleted stages.
- **Advanced FFmpeg Audio Mixing**: Fully integrated background music rendering. Users can now independently control the `Background Music Volume` and the `Original Voiceover Volume`. FFmpeg uses the `amix` filter to dynamically loop and merge the audio perfectly into the final exported MP4.
- **Custom Audio Uploads**: Added a drag-and-drop zone with a dedicated API endpoint (`POST /projects/{id}/music`) allowing users to upload specific `.mp3` or `.wav` files directly from their computer into the project without needing to touch the backend folder.
- **Strict Shorts Duration Cap**: The AI Story Engine now has a mathematical hard-cap implemented in the Gemini prompt. When generating a "Shorts" format reel (max 60s), the AI is strictly forced to select a maximum of 15 clips—actively overriding the "use 80% coverage" rule to ensure the resulting video absolutely stays under 60 seconds.

## [9.1.0] - ReelForge Story Engine & Stability Patches
### Added
- **ReelForge Story Sequencing**: AI now maps out a logical real estate property tour (Drone -> Exterior -> Entrance -> Living -> Kitchen -> Bedroom -> Bathroom -> Amenities -> Parking -> Closing) rather than sorting clips strictly by visual score.
- **Dynamic Reel Duration**: Duration algorithm intelligently scales total output time based on the volume of unique footage (e.g., Short Mode: 30-45s for 10 clips, up to 60s max. YouTube Mode: 60-90s for 10 clips, up to 120s max).
- **Opening Shot Enforcement**: AI is explicitly instructed to open with premium shots (Drone, Exterior, Luxury Scene) and explicitly banned from opening with low-tier scenes (Parking, Storage).
- **Minimum Clip Usage & 3-5s Segment Extraction**: Guaranteed that 1 segment from every unique uploaded clip is used. Clips are perfectly trimmed to 3-5 seconds depending on visual quality score.
- **Storage Auto-Cleanup**: The backend now strictly sleeps to release Windows file locks and aggressively purges `clip_x.mp4` intermediate segments after a reel is compiled, saving gigabytes of storage.
- **Parallel FFmpeg Traffic Control**: Fixed a massive system-crashing bug (`WinError 10055`) by implementing a strict `asyncio.Semaphore(4)` that throttles FFmpeg encodings to 4 maximum concurrent operations, preventing laptop freezes under heavy loads.

### Changed
- **UI Button Integrity**: The "Start AI Analysis" button is strictly disabled until *all* clips are fully processed.
- **Aspect Ratio Toggles**: Refined "Final Polish" options to highlight duration lengths for Reels (45 to 60s) and YouTube (1-2 min+), completely removing the legacy 'Square' 1:1 option to streamline the creative flow.

## [9.0.0] - Guided AI SaaS Workflow (Wizard)
- **Horizontal Progress Navigation**: Added a top bar showing current step progress and property name.
- **Upload Success Summary Card**: Replaced the sprawling horizontal gallery in Step 1 with a premium Canva/Descript style success card that dynamically appears once clips are uploaded.
- **Drag-and-Drop Enhancements**: Added Framer Motion hover states, glowing borders, and scaling upload icons to the drag-and-drop zone.
- **Smart Crossfade Engine**: Replaced basic FFmpeg concatenation with a massive `-filter_complex` pipeline utilizing `xfade` and `acrossfade` for smooth, professional transitions.
- **Production-Grade AI Selection Engine**: Overhauled the Gemini prompt to perform "Full Video Analysis" (extracting multiple chunks per video), apply strict >85% confidence thresholds, and leverage Gemini's context window for active semantic deduplication.
- **Coverage Protection & Adjustable Sensitivity**: Implemented a 3-Level duplicate detection engine. Added a "Duplicate Sensitivity" dropdown to the UI. The AI is now strictly instructed to maximize footage coverage and never drop a clip if it's the only one of its category.
- **Real Estate Storytelling Structure**: Forced the AI output to structure reels identically to professional editors (Impressive Hook -> Walkthrough -> Amenities -> CTA).
- **Enhanced Transparency Panel UI**: Added a list view tracking exactly which clips were removed and the specific AI reasoning behind the drop (e.g., "Similarity > 95%"). Also displays total seconds analyzed and detailed AI ranking scores (`visual_quality_score`, `luxury_appeal`) for every chosen clip.
- **Dynamic Style-Based Transitions**: Auto-assigns transition types based on style (Luxury = 0.5s fade, Viral = fast wipeleft, Realtor = slideleft).
- **Scene Grouping Engine**: A pre-render sorting algorithm groups identical room types together to prevent jarring random jumps.
- **Step Isolation**: Isolated the `/analyze` and `/generate` SSE endpoints into distinct views to reduce cognitive load during processing.

### Changed
- **High-Quality Render Pipeline**: Massively upgraded FFmpeg render presets from `fast crf 23` to `slow crf 18`, utilizing auto color-normalization (`eq` filter) and forced 30fps matching to guarantee crisp, professional video exports without frame drops.
- **Removed Hardcoded Mock Data**: Purged all fake metrics from the UI (e.g., random AI Confidence percentages, fake rejected clip reasons, and placeholder Viral/Retention scores) so the dashboard strictly reflects genuine backend API data.
- **Global Responsive Layout**: Fixed deeply nested `flex-1 min-h-0` constraints, allowing the application to scroll naturally (`overflow-y-auto`) and stack appropriately on mobile/tablet devices.
- **URL Import Panel**: Updated text to explicitly list supported external sources (Google Drive, Dropbox, OneDrive, Direct MP4 URLs).

## [8.0.0] - AI Creative Studio Redesign
### Added
- **Completely Redesigned Studio Interface**: Transformed the dashboard into a 3-section AI workspace (Uploaded Footage, AI Director, AI Storyboard).
- **Multi-Format Generation**: Added support for 9:16 (Reels/Shorts), 16:9 (YouTube), and 1:1 (Square) aspect ratios with dynamic FFmpeg cropping and scaling.
- **AI Scene Detection & Insights**: Visualized AI analysis showing detected rooms, property type, and confidence scores.
- **Two-Row Story View**: Visually compare raw uploaded clips against the AI-selected final sequence.
- **AI Rejection Panel**: Displays clips rejected by the AI with mock reasoning (e.g. Blurry, Shaky).
- **Dynamic Sticky Preview Panel**: Auto-adjusts preview player aspect ratio and provides easy access to style presets and generated hooks.

## [7.0.0] - 2026-06-13
### Changed
- **Luxury Ocean Aurora Redesign**: Radically transformed the ReelForge UI from a dark admin dashboard into a premium, Stripe-inspired light-themed SaaS product.
- **Top Navigation Architecture**: Completely removed the legacy left sidebar. Replaced it with a modern, floating 80px high glassmorphism Top Navigation Bar.
- **Micro-Interactions**: Heavily integrated `framer-motion` to provide smooth, premium animations (hover scaling, layout transitions, animated stat counters) across the dashboard and storyboard.
- **Intelligent Story Builder**: Rebuilt the drag-and-drop horizontal storyboard using light mode aesthetics, soft shadows, and real-time AI confidence metrics.

## [6.0.0] - 2026-06-13
- **Premium Studio Redesign**: Completely transformed the ReelForge dashboard from an admin panel into a high-end AI creative studio. Implemented a 3-pane layout featuring a fixed sidebar, central main workspace, and sticky right-side preview panel.
- **Cinematic Theme**: Upgraded global styling to use a deep gradient `#0A0A0B` background, `#111827` glassmorphism cards, and `#8B5CF6` purple accents.
- **Horizontal Story Builder**: Replaced the infinitely scrolling vertical list with a compact, snap-scrolling horizontal storyboard showcasing video thumbnails and AI detection metrics.
- **Dynamic Timelines**: The AI generation prompt now forces Gemini to return a `custom_sequence` array, physically reordering clips uniquely for each of the 3 output variations (Luxury, Viral, Realtor).
- **Sticky AI Preview**: The right side of the dashboard is now a dedicated persistent preview engine featuring a 16:9 video player, AI script previews, and alternative variation access.

## [5.0.0] - 2026-06-12
- **Premium SaaS Re-architecture**: Upgraded the prototype into a fully-featured, Canva-tier Real Estate Shorts Generator.
- **MongoDB Integration**: Replaced stateless architecture with persistent MongoDB collections for Users, Projects, Uploads, Generated Shorts, and History tracking.
- **JWT RSA-256 Authentication**: Added enterprise-grade secure login, refresh token rotation, and explicit revocation.
- **Interactive Visual Timeline**: Separated the AI Analysis phase from the FFmpeg Render phase. Users can now visually drag-and-drop the "Property Story Builder" blocks (e.g., Exterior -> Living Room -> Kitchen) to perfect the sequence before generating.
- **3 Reel Variations**: The rendering engine now outputs 3 distinct stylistic variations (Luxury, Instagram Viral, Realtor Style) per generation.
- **Premium Upload Hub**: Replaced the basic textarea with a dynamic upload interface supporting Dropbox Folder parsing, URL Cards, and local multi-file drag-and-drop.
- **SaaS Dashboard Workspace**: Rebuilt the frontend with React Router, Tailwind CSS, and Framer Motion, introducing a professional dashboard with analytics, recent projects, and cinematic video previews.

## [4.0.0] - 2026-06-12
### Added
- **Production Reliability Layer**: Implemented robust failure handling for the Gemini API. The system now features exponential backoff (5s to 60s) with random jitter to gracefully handle HTTP 503, 429, and Model Overloaded errors.
- **Model Fallback**: The primary reasoning engine is now `gemini-2.5-pro`. If it fails 3 times consecutively due to server load, the system dynamically fails over to `gemini-2.5-flash` for remaining attempts, ensuring maximum uptime.
- **Concurrency Management**: Added strict `asyncio.Semaphore(2)` locking to prevent overwhelming the AI servers during parallel clip processing.
- **Real-Time Retry UI**: The frontend SSE stream now actively notifies users during AI congestion (e.g., "AI servers busy, retrying... (Retry 1 of 5)").

## [3.0.0] - 2026-06-12
### Added
- **AI Real Estate Reel Generator**: Upgraded the pipeline to accept 10-30 Dropbox clips. FFMPEG and Gemini now detect property types (Apartment vs House) and enforce smart storytelling sequences. Quality-based filtering automatically rejects blurry/shaky footage and selects the top 8-12 clips.
- **Premium Dashboard**: The UI now supports Reel Duration & Style selection, and renders a fully detailed preview dashboard mapping out the property description, property type, processing metrics, and the final hook.

## [2.0.0] - 2026-06-12
### Added
- **Multi-Video Property Reels**: Completely overhauled the architecture to accept between 5 and 10 separate property videos (e.g., exterior, drone, living room). The application processes them in parallel, uploads previews for all assets, and runs a unified Gemini analysis to stitch together a single optimal 20-30 second viral reel.
- **Frontend Upgrades**: Added multi-URL textarea input with strict 5-10 URL validation. Rebuilt the results dashboard to showcase the final unified video with integrated hook and analytics.

## [1.0.4] - 2026-06-12
### Added
- **Sony XAVC & High-End Camera Support**: Implemented rigorous FFmpeg stream mapping (`-map 0:v:0`, `-map 0:a:0?`), disabled data streams (`-dn`), and enforced standard pixel formats (`-pix_fmt yuv420p`) to ensure Sony XAVC files with `rtmd` metadata streams process cleanly. Added an automatic normalization fallback if the initial preview generation fails.

## [1.0.3] - 2026-06-12
### Fixed
- **FastAPI Routing Bug**: Fixed a route precedence issue where `app.mount("/", StaticFiles(...))` would shadow all subsequent routes, including the core `/api/process` SSE endpoint, causing an immediate 404 response. The static files are now correctly mounted under `/static`, and a dedicated `@app.get("/")` handler gracefully serves the `index.html` file, ensuring API routes are reachable.

## [1.0.2] - 2026-06-12
### Fixed
- **Windows Compatibility**: Replaced all uses of `asyncio.create_subprocess_exec` with `subprocess.run` running in a separate thread via `asyncio.to_thread`. This resolves a critical `NotImplementedError` when executing FFmpeg on Windows using Python 3.13.

## [1.0.1] - 2026-06-12
### Fixed
- **Debugging**: Added deep debugging around Dropbox video downloading logic, including traceback, content length/type verification, and error handling for empty files or non-existent files.

## [1.0.0] - 2026-06-11
### Added
- **Backend Setup**: FastAPI server initialization with Server-Sent Events (SSE) support for streaming live progress to the frontend.
- **Gemini Integration**: Built a robust service utilizing the Gemini Files API for large video uploads and `gemini-2.5-pro` for structured content generation (script, title, hashtags).
- **FFMPEG Processing**: Automated downloading from Dropbox and video cropping to 9:16 aspect ratio using `asyncio.subprocess`.
- **Frontend Setup**: Bootstrapped Vite + React application.
- **Premium UI/UX**: Designed a high-quality glassmorphism dark mode UI using Vanilla CSS, complete with custom keyframe animations and a dynamic progress tracking layout.
- **Deployment Ready**: Implemented a unified Dockerfile supporting both frontend building and backend serving, ready for one-click deployment on Railway.
- **Documentation**: Created `README.md` and `PROMPTS.md`.

# Changelog

All notable changes to this project will be documented in this file.

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

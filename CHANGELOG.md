# Changelog

All notable changes to this project will be documented in this file.

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

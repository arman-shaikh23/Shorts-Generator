# Changelog

All notable changes to this project will be documented in this file.

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

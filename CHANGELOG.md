# Changelog

All notable changes to this project will be documented in this file.

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

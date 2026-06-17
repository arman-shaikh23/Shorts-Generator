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

### 2. Hybrid Cinematic AI Engine v9 (OpenCV + Gemini)
- **Computer Vision Pre-Processing**: Before hitting the AI, an OpenCV physics layer (`cv_analyzer.py`) mathematically analyzes the footage for motion blur (Variance of Laplacian), exposure spikes, and severe camera shake (MSE). It dynamically scrubs out the first 0-3 seconds *only* if the operator was calibrating the gimbal.
- **Advanced Contextual Understanding**: The AI views every frame of your raw footage. It categorizes rooms (e.g., distinguishing a kitchen from a living room) and determines the exact camera movement (pan, tilt, drone approach).
- **Multi-Segment Extraction**: A single uploaded video can contribute up to 3 distinct scenes if it contains multiple rooms (e.g., lobby at 3-7s, entrance at 10-15s). Each segment gets a unique `clip_id` for accurate tracking.
- **Strict Drone Segregation**: Explicit classification constraints guarantee DJI/Drone footage will never be incorrectly labeled as interior property rooms.
- **Story Zones Architecture**: Clips are grouped into 4 cinematic zones — OPENING (drone/aerial/exterior), INTERIOR (lobby through bathroom), AMENITIES (pool/gym/garden), CLOSING — ensuring natural real-estate storytelling.
- **Strict Walkthrough Mode**: For Luxury and Realtor styles, clips follow a hard walkthrough order (Drone → Exterior → Entrance → Lobby → Living Room → Kitchen → Bedroom → Bathroom → Amenities → Closing). For Instagram/Viral, clips are ordered by hero-score impact.
- **Room Continuity Scoring**: Natural room transitions (e.g., Living Room → Kitchen) receive bonuses, while unnatural jumps (e.g., Kitchen → Pool) are penalized, creating smooth virtual tours.
- **Hero Clip Protection**: Clips with `hero_score >= 90` are NEVER removed from the timeline regardless of other quality metrics.
- **Sequence Validation**: Post-optimization validation enforces 4 hard rules: no backward movement, max 3 same-type consecutive clips, drone only in opening/closing zones, bathroom never before living room.
- **Smart Pacing Bounds**: Clips are intelligently trimmed based on their calculated `final_score`. Weak clips bounded to 4-7s, Hero clips to 7-10s, exceptional Drone shots up to 12s.
- **Full Render Audit**: Every render is tracked with `selected_count`, `rendered_count`, `selected_duration`, `rendered_duration`, `duration_coverage_pct`, and detailed skip reasons (`missing_file`, `ffmpeg_timeout`, `decode_error`).
- **ALL-Clips Variation Rendering**: All 3 style variations (Luxury, Instagram, Realtor) MUST include every approved timeline clip. `custom_sequence` controls ordering only, never removal.

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

## Troubleshooting
- **Professional Camera Footage (Sony XAVC, etc.)**: High-end footage with `rtmd` metadata streams or 10-bit 4:2:2 chroma subsampling might fail standard FFmpeg extraction. The application automatically normalizes this footage, dropping non-video/audio streams and forcing `yuv420p` pixel format to ensure Gemini AI compatibility.
- **API 404 Errors**: If `/api/process` returns a 404 on deployment, verify that the static file mount isn't intercepting the root path. Our production build is configured to serve static assets safely without shadowing `/api/*`.
- **Windows Python 3.13 `NotImplementedError`**: FFmpeg commands are deliberately executed using `subprocess.run` inside `asyncio.to_thread()` instead of `asyncio.create_subprocess_exec`. This is to circumvent a `NotImplementedError` limitation on Windows platforms with the Proactor event loop. 
- **Missing Videos**: If downloading from Dropbox fails or creates empty files, check the server logs. We have added deep debugging around the download stage to trace HTTP responses, content types, and file sizes.

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

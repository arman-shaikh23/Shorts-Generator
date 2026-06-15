# Real Estate AI Shorts Generator (Premium SaaS)

An enterprise-grade, Canva-tier AI platform that empowers Real Estate Agents, Builders, and Marketing Agencies to effortlessly transform raw property footage into high-converting, viral social media shorts. The product bridges the gap between raw assets and published marketing material by replacing tedious manual video editing with intelligent, context-aware AI storytelling and an interactive visual timeline.

## Tech Stack
- **Frontend**: React, Vite, Tailwind CSS, Framer Motion, Shadcn UI
- **Backend**: FastAPI (Python), Motor (Async MongoDB)
- **Database**: MongoDB (Atlas)
- **Auth**: RSA-256 JWT with Refresh Token Rotation
- **AI Engine**: Google Gemini Pro (via Files API)
- **Render Engine**: FFmpeg

## Features
- **6-Step Guided Wizard Workflow**: Completely dismantled the massive single-page dashboard into a focused, modern SaaS wizard (Upload -> Analyze -> Storyboard -> Style -> Generate -> Export).
- **Premium Canva-style Upload Workflow**: Focused upload screen with animated drag-and-drop zones, explicit URL integrations (Drive, Dropbox, OneDrive), and a dynamic "Upload Complete" success card to keep the workspace clean.
- **Luxury Ocean Aurora Dashboard**: A premium, light-themed workspace inspired by Stripe and Linear. Features an 80px floating top navigation bar and a clean responsive 2-column workspace layout.
- **Authentic Data Visualization**: The UI strictly surfaces real data returned by the backend (e.g. actual extracted clip durations, actual scene types) with zero hardcoded "mock" metrics.
- **Micro-Interactions**: Built heavily with Framer Motion to provide high-end, smooth animations (hover scaling, layout transitions, animated step indicators).
- **Smart Crossfade Engine**: Generated videos use a massive `-filter_complex` FFmpeg pipeline with `xfade` and `acrossfade` for buttery-smooth transitions (Fades, Wipes, Slides) tailored automatically to the selected reel style.
- **Production-Grade AI Selection**: Extracts multiple segments from long videos, applies strict >85% confidence thresholding, and uses a native Semantic Deduplication pipeline to guarantee only the highest-quality unique shots are used.
- **ReelForge Storytelling Engine**: Analyzes and builds sequences following a strict real estate logic: Drone/Exterior -> Walkthrough -> Amenities -> Parking. Explicitly prevents using low-tier scenes (e.g., Parking, Bathrooms) as the opening hook.
- **Dynamic Reel Durations**: The platform intelligently scales output duration based on the volume of unique footage available, generating 30-60s Shorts or 60-120s YouTube videos.
- **Coverage Protection System**: Forces maximum clip utilization (80-95%) by ensuring at least 1 segment from every unique uploaded clip is used. Trims clips dynamically (3-5s) based on visual quality score.
- **Parallel FFmpeg Traffic Control**: Strictly throttles concurrent video encoding operations (Semaphore) to prevent system freezing and memory starvation during heavy loads (30+ clips).
- **Automated Storage Management**: Aggressively cleans up intermediate rendering chunks after compilation, ensuring long-term server storage remains free of bloat.
- **Adjustable Duplicate Sensitivity**: Users can define how aggressively the AI filters clips via a dropdown (Low, Medium, High).
- **Scene Grouping Algorithm**: Prevents jarring visual jumping by intelligently sorting and grouping similar scenes (e.g. all exterior shots play sequentially).
- **Studio Grade Quality**: Enforces strict `fps=30`, color-normalization passes (`eq=contrast=1.05`), and high-end `-preset slow -crf 18` encoding for crisp, artifact-free exports.
- **AI Creative Studio**: Replaces the generic file manager with a 3-stage AI pipeline (Uploaded Footage, AI Director Analysis, and AI Storyboard). Shows detected rooms, confidence scores, and AI rejection reasons.
- **Multi-Format Generation**: Instantly re-crop and scale videos into 9:16 (Instagram Reels/TikTok) or 16:9 (YouTube Long Form) aspect ratios based on user selection.
- **Two-Row Story View**: Visually compare your raw uploaded clips against the final, logically sequenced storyboard selected by the AI Director.
- **3 Reel Variations**: Instead of a single output, the AI automatically generates 3 unique stylistic variations (Luxury, Viral, Realtor) allowing the user to select the perfect vibe.
- **Advanced Upload Hub**: Seamlessly import 10-40 videos via dynamic URL cards, Dropbox Folder links, or a massive drag-and-drop local file zone.
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

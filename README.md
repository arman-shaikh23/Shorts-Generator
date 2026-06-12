# Property Video to Shorts Generator

An AI-powered full-stack web application that transforms horizontal real estate videos into vertical (9:16) short clips optimized for social media (Instagram Reels, YouTube Shorts, TikTok). It automatically identifies the best moments, crops the video, and generates a script, title, and hashtags.

## Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: React (Vite) + Vanilla CSS
- **AI Processing**: Google Gemini Pro (via Files API)
- **Video Processing**: FFMPEG

## Features
- **Smart Reel Sequencer**: Upload 10-30 separate raw clips. The AI will detect if the property is a House or Apartment and dynamically sequence the footage (e.g., Exterior -> Living Room -> Kitchen -> Pool) according to real estate storytelling best practices.
- **AI Clip Filtering**: Automatically scores clips from 0-100, rejecting blurry, shaky, or poor-lighting footage to build the perfect 20, 30, or 45-second reel.
- **Production Reliability Layer**: Intelligent exponential backoff with jitter and automatic model failover (`gemini-2.5-pro` -> `gemini-2.5-flash`) ensures maximum uptime during AI server congestion.
- **Premium Dashboard**: Customize reel duration and style, and view detailed metrics including total raw clip duration processed and property descriptions.
- Server-Sent Events (SSE) for granular progress tracking across 8 AI milestones and real-time retry alerts.
- Direct downloads of fully prepared `.mp4` clips.

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

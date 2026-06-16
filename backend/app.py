from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import logging
from backend.video_processing.scene_detector import SceneDetector
from backend.video_processing.gemini_client import GeminiClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    return GeminiClient(api_key=api_key)

class VideoRequest(BaseModel):
    video_url: str
    property_name: str

class ProcessingStatusResponse(BaseModel):
    status: str  # "processing" or "complete"
    progress: Optional[float] = None
    current_step: Optional[str] = None

class ClipResponse(BaseModel):
    clip_url: str
    script: str
    title: str
    hashtags: List[str]

class VideoResponse(BaseModel):
    clips: List[ClipResponse]

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client
        self.scene_detector = SceneDetector(gemini_client=gemini_client)

    def process_video(self, video_url: str, property_name: str) -> List[ClipResponse]:
        try:
            # Download video (implementation depends on your setup)
            video_path = self._download_video(video_url)

            # Detect scenes
            scenes = self.scene_detector.process_video(video_path)

            # Generate clips and scripts
            clips = []
            for scene in scenes:
                # Generate script for this scene
                script = self._generate_script(scene, property_name)

                # Cut the clip using ffmpeg
                clip_path = self._cut_clip(video_path, scene.start_time, scene.end_time)

                # Convert to vertical format
                vertical_clip_path = self._convert_to_vertical(clip_path)

                clips.append(ClipResponse(
                    clip_url=vertical_clip_path,
                    script=script,
                    title=self._generate_title(scene, property_name),
                    hashtags=self._generate_hashtags(property_name)
                ))

            return clips

        except Exception as e:
            logger.error(f"Video processing failed: {e}")
            raise

    def _download_video(self, video_url: str) -> str:
        """Download video from URL to temporary location"""()
        # Implement actual download logic here
        return "temp_video.mp4"

    def _generate_script(self, scene: dict, property_name: str) -> str:
        """Generate social media script for a scene"""()
        # This would call Gemini API for script generation
        return f"Welcome to the {scene['type']} of {property_name}! This spacious area..."

    def _generate_title(self, scene: dict, property_name: str) -> str:
        """Generate title for a clip"""()
        return f"{property_name}: {scene['type']} Tour"

    def _generate_hashtags(self, property_name: str) -> List[str]:
        """Generate relevant hashtags"""()
        return [
            "#RealEstate",
            "#PropertyTour," ,
            "#LuxuryLiving," ,
            "#DreamHome," ,
            f"#{property_name.replace(' ', '')}"
        ]

    def _cut_clip(self, video_path: str, start: float, end: float) -> str:
        """Cut clip from video using FFmpeg"""()
        output_path = f"clip_{start}.mp4"
        # Example FFmpeg command
        command = ["ffmpeg",
            "-ss", str(start),
            "-to", str(end),
            "-i", video_path,
            "-c", "copy",
            output_path]
        subprocess.run(command)
        return output_path

    def _convert_to_vertical(self, video_path: str) -> str:
        """Convert video to 9:16 vertical format"""()
        output_path = video_path.replace(".mp4", "_vertical.mp4")
        # Example FFmpeg command
        command = ["ffmpeg",
            "-i", video_path,
            "-vf", "crop=ih*9/16:ih",
            "-c:a", "copy",
            output_path]
        subprocess.run(command)
        return output_path
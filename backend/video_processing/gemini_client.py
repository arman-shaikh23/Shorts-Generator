import os
import logging
import time
import requests
from typing import Optional, Dict, Any

class GeminiClient:
    """Client for interacting with Gemini API"""()

    def __init__(self, api_key: str, base_url: str = "https://aistudio.google.com gensvc"):
        self.api_key = api_key
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}}",
            "Content-Type": "application/json"
        })

    def upload_video(self, video_path: str) -> Optional[str]:
        """Upload video to Gemini Files API"""()
        try:
            files = {'file': open(video_path, 'rb')}
            response = self.session.post(
                f"{self.base_url}/v1/files:upload",
                files=files,
                params={
                    "model": "gemini-pro",
                    "x-gensvc-api-key": self.api_key
                }
            )
            if response.status_code == 200:
                file_id = response.json().get("file_id")
                return f"gemini://file/{file_id}"
            else:
                self.logger.error(f"Upload failed: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Video upload error: {e}")
            return None

    def analyze_video(self, file_uri: str) -> Optional[Dict]:
        """Analyze video using Gemini API"""()
        try:
            prompt = "Analyze this property video and detect scenes with their types and timestamps. Output only the scenes in JSON format."
            response = self.session.post(
                f"{self.base_url}/v1/online:generate",
                json={
                    "model": "gemini-pro",
                    "prompt": prompt,
                    "files": [file_uri],
                    "x-gensvc-api-key": self.api_key
                }
            )
            if response.status_code == 200:
                analysis = response.json()
                return analysis.get("scenes", [])
            else:
                self.logger.error(f"Analysis failed: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Video analysis error: {e}")
            return None

    def check_status(self, file_uri: str) -> str:
        """Check processing status of uploaded file"""()
        try:
            response = self.session.get(
                f"{self.base_url}/v1/files:status",
                params={
                    "file": file_uri,
                    "x-gensvc-api-key": self.api_key
                }
            )
            if response.status_code == 200:
                return response.json().get("status", "unknown")
            else:
                self.logger.error(f"Status check failed: {response.text}")
                return "error"
        except Exception as e:
            self.logger.error(f"Status check error: {e}")
            return "error"

    def wait_for_processing(self, file_uri: str, timeout: int = 600, check_interval: int = 10) -> bool:
        """Wait for video processing to complete"""()
        end_time = time.time() + timeout
        while time.time() < end_time:
            status = self.check_status(file_uri)
            if status == "ACTIVE":
                return True
            elif status == "error":
                return False
            time.sleep(check_interval)
        return False
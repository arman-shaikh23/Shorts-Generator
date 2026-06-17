import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

def analyze_video_segment(filepath: str, start_sec: float, end_sec: float = None) -> dict:
    """
    Analyzes a video segment for mathematical scores.
    Returns:
        {
            "stability_score": 0-100,
            "motion_quality_score": 0-100,
            "blur_score": 0-100,
            "lighting_score": 0-100,
            "is_unstable": bool
        }
    """
    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        return {"stability_score": 50, "motion_quality_score": 50, "blur_score": 50, "lighting_score": 50, "is_unstable": True}

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0: fps = 30
    
    start_frame = int(start_sec * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    end_frame = int(end_sec * fps) if end_sec else start_frame + int(fps * 3) # default analyze 3 secs
    
    laplacian_vars = []
    brightness_vals = []
    mse_vals = []
    
    prev_gray = None
    
    frameCount = 0
    while cap.isOpened() and frameCount < (end_frame - start_frame):
        success, frame = cap.read()
        if not success:
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Blur detection
        laplacian_vars.append(cv2.Laplacian(gray, cv2.CV_64F).var())
        
        # Lighting/Brightness
        brightness_vals.append(np.mean(gray))
        
        # Motion Quality / Shake (MSE between consecutive frames)
        if prev_gray is not None:
            err = np.sum((gray.astype("float") - prev_gray.astype("float")) ** 2)
            err /= float(gray.shape[0] * gray.shape[1])
            mse_vals.append(err)
            
        prev_gray = gray
        frameCount += 1

    cap.release()
    
    if not laplacian_vars:
        return {"stability_score": 50, "motion_quality_score": 50, "blur_score": 50, "lighting_score": 50, "is_unstable": True}

    # Calculate metrics
    avg_laplacian = np.mean(laplacian_vars)
    avg_brightness = np.mean(brightness_vals)
    max_mse = np.max(mse_vals) if mse_vals else 0
    avg_mse = np.mean(mse_vals) if mse_vals else 0
    
    # Map to 0-100 scores
    # Blur: higher laplacian = less blur. Usually > 100 is sharp.
    blur_score = min(100, int(avg_laplacian / 5))
    
    # Lighting: ideal brightness around 120-180
    if 100 <= avg_brightness <= 200:
        lighting_score = 90
    elif avg_brightness < 50 or avg_brightness > 230:
        lighting_score = 40
    else:
        lighting_score = 70
        
    # Motion/Stability: High MSE means severe shake or sudden cut.
    # Typical smooth pan MSE is < 1500. Drops/shakes are > 3000.
    if max_mse > 4000:
        stability_score = 30
        motion_quality_score = 30
        is_unstable = True
    elif max_mse > 2000:
        stability_score = 60
        motion_quality_score = 60
        is_unstable = False
    else:
        stability_score = 90
        motion_quality_score = max(50, 100 - int(avg_mse / 20))
        is_unstable = False

    return {
        "stability_score": stability_score,
        "motion_quality_score": motion_quality_score,
        "blur_score": blur_score,
        "lighting_score": lighting_score,
        "is_unstable": is_unstable
    }

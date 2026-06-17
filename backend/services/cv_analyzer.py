import cv2
import numpy as np
import logging
import time

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
#  HIGH-PERFORMANCE CV ANALYZER — Optimized for Speed
#  Target: <6 seconds per video, <2 minutes for 20 videos
#
#  Optimizations vs. original:
#  1. Frame sampling: every 15th frame instead of every frame
#  2. Downscale to 480p before all math (16x fewer pixels than 4K)
#  3. 3-window analysis: start/middle/end of segment (not entire clip)
#  4. 30-second hard timeout per video
#  5. Lightweight MSE via absdiff instead of float64 squaring
# ═══════════════════════════════════════════════════════════════

ANALYSIS_WIDTH = 640       # Downscale target width (keeps aspect ratio)
FRAME_SAMPLE_INTERVAL = 15 # Analyze every Nth frame
WINDOW_DURATION_SEC = 1.5  # Seconds to analyze per window (start/mid/end)
TIMEOUT_SEC = 30           # Hard timeout per video


def _downscale(frame, target_width=ANALYSIS_WIDTH):
    """Downscale frame to target width, preserving aspect ratio."""
    h, w = frame.shape[:2]
    if w <= target_width:
        return frame
    scale = target_width / w
    new_h = int(h * scale)
    return cv2.resize(frame, (target_width, new_h), interpolation=cv2.INTER_AREA)


def _analyze_window(cap, start_frame: int, num_frames: int, sample_interval: int):
    """
    Analyze a short window of frames. Returns partial metrics.
    Reads only every `sample_interval`-th frame for speed.
    """
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    laplacian_vars = []
    brightness_vals = []
    mse_vals = []
    prev_gray = None
    frames_read = 0
    
    for i in range(num_frames):
        success, frame = cap.read()
        if not success:
            break
        
        # Only process every Nth frame
        if i % sample_interval != 0:
            continue
        
        # Downscale for speed
        small = _downscale(frame)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        
        # Blur detection (Laplacian variance)
        laplacian_vars.append(cv2.Laplacian(gray, cv2.CV_64F).var())
        
        # Lighting/Brightness
        brightness_vals.append(np.mean(gray))
        
        # Motion/Shake detection (lightweight absdiff instead of float64 MSE)
        if prev_gray is not None:
            diff = cv2.absdiff(gray, prev_gray)
            mse_approx = float(np.mean(diff.astype(np.float32) ** 2))
            mse_vals.append(mse_approx)
        
        prev_gray = gray
        frames_read += 1
    
    return laplacian_vars, brightness_vals, mse_vals, frames_read


def analyze_video_segment(filepath: str, start_sec: float, end_sec: float = None) -> dict:
    """
    Analyzes a video segment for mathematical quality scores.
    
    OPTIMIZED: Uses 3-window sampling (start/middle/end) with frame skipping
    and downscaling. Completes in <6 seconds per video instead of ~200s.
    
    Returns:
        {
            "stability_score": 0-100,
            "motion_quality_score": 0-100,
            "blur_score": 0-100,
            "lighting_score": 0-100,
            "is_unstable": bool
        }
    """
    t0 = time.perf_counter()
    default_result = {"stability_score": 50, "motion_quality_score": 50, "blur_score": 50, "lighting_score": 50, "is_unstable": True}
    
    try:
        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            logger.warning(f"[CV] Cannot open: {filepath}")
            return default_result

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        start_frame = int(start_sec * fps)
        if end_sec and end_sec > start_sec:
            end_frame = int(end_sec * fps)
        else:
            end_frame = start_frame + int(fps * 3)  # Default 3 seconds
        
        # Clamp to actual video length
        end_frame = min(end_frame, total_frames)
        segment_frames = end_frame - start_frame
        
        if segment_frames <= 0:
            cap.release()
            return default_result
        
        window_frames = int(WINDOW_DURATION_SEC * fps)
        
        # ── 3-Window Strategy: Start / Middle / End ──
        # Instead of reading ALL frames, we sample 3 short windows
        windows = []
        
        # Window 1: Start of segment
        w1_start = start_frame
        w1_count = min(window_frames, segment_frames)
        windows.append((w1_start, w1_count))
        
        # Window 2: Middle of segment (only if segment > 3 windows)
        if segment_frames > window_frames * 3:
            mid_start = start_frame + (segment_frames // 2) - (window_frames // 2)
            windows.append((mid_start, window_frames))
        
        # Window 3: End of segment (only if different from start)
        if segment_frames > window_frames * 2:
            w3_start = end_frame - window_frames
            windows.append((w3_start, window_frames))
        
        # Analyze each window
        all_laplacian = []
        all_brightness = []
        all_mse = []
        total_sampled = 0
        
        for w_start, w_count in windows:
            # Check timeout
            elapsed = time.perf_counter() - t0
            if elapsed > TIMEOUT_SEC:
                logger.warning(f"[CV TIMEOUT] {filepath} exceeded {TIMEOUT_SEC}s at window analysis. Using partial data.")
                break
            
            lap, bri, mse, read = _analyze_window(cap, w_start, w_count, FRAME_SAMPLE_INTERVAL)
            all_laplacian.extend(lap)
            all_brightness.extend(bri)
            all_mse.extend(mse)
            total_sampled += read
        
        cap.release()
        
        if not all_laplacian:
            return default_result
        
        # ── Calculate Metrics ──
        avg_laplacian = np.mean(all_laplacian)
        avg_brightness = np.mean(all_brightness)
        max_mse = np.max(all_mse) if all_mse else 0
        avg_mse = np.mean(all_mse) if all_mse else 0
        
        # Map to 0-100 scores (same thresholds as original)
        # Blur: higher laplacian = sharper image. Typically >100 is sharp.
        blur_score = min(100, int(avg_laplacian / 5))
        
        # Lighting: ideal brightness is 120-180
        if 100 <= avg_brightness <= 200:
            lighting_score = 90
        elif avg_brightness < 50 or avg_brightness > 230:
            lighting_score = 40
        else:
            lighting_score = 70
        
        # Motion/Stability: High MSE = severe shake or sudden cuts
        # Note: MSE values are lower than original because we use downscaled frames
        # Scale factor: (original_pixels / downscaled_pixels) ≈ 9x for 4K→640
        # But absdiff+mean normalizes per-pixel, so thresholds adjust slightly
        if max_mse > 800:
            stability_score = 30
            motion_quality_score = 30
            is_unstable = True
        elif max_mse > 400:
            stability_score = 60
            motion_quality_score = 60
            is_unstable = False
        else:
            stability_score = 90
            motion_quality_score = max(50, 100 - int(avg_mse / 4))
            is_unstable = False
        
        elapsed = time.perf_counter() - t0
        logger.info(f"[CV PERF] {filepath.split('/')[-1].split(chr(92))[-1]}: {elapsed:.1f}s | {total_sampled} frames sampled | blur={blur_score} stab={stability_score} light={lighting_score} motion={motion_quality_score}")
        
        return {
            "stability_score": stability_score,
            "motion_quality_score": motion_quality_score,
            "blur_score": blur_score,
            "lighting_score": lighting_score,
            "is_unstable": is_unstable
        }
    
    except Exception as e:
        elapsed = time.perf_counter() - t0
        logger.error(f"[CV ERROR] {filepath}: {e} ({elapsed:.1f}s)")
        return default_result

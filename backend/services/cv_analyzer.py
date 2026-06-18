import cv2
import numpy as np
import logging
import time
import asyncio

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
#  REELFORGE V4.0 — HIGH-PERFORMANCE CV ANALYZER
#  
#  Features:
#  1. 3-window sampling (start/middle/end) with frame skipping
#  2. Downscale to 480p before all math
#  3. Lucas-Kanade Optical Flow for camera adjustment detection
#  4. Intelligent Media Filtering (720p floor, no auto-block)
#  5. asyncio.to_thread() compatible — never blocks event loop
#  6. cv_semaphore throttling for CPU-intensive operations
# ═══════════════════════════════════════════════════════════════

ANALYSIS_WIDTH = 640       # Downscale target width (keeps aspect ratio)
FRAME_SAMPLE_INTERVAL = 15 # Analyze every Nth frame
WINDOW_DURATION_SEC = 1.5  # Seconds to analyze per window (start/mid/end)
TIMEOUT_SEC = 30           # Hard timeout per video

# V4.0: Concurrency throttle for CPU-intensive operations
cv_semaphore = asyncio.Semaphore(3)

# V4.0: Lucas-Kanade Optical Flow parameters
LK_PARAMS = dict(
    winSize=(15, 15),
    maxLevel=2,
    criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
)

# V4.0: Feature detection parameters for Shi-Tomasi corners
FEATURE_PARAMS = dict(
    maxCorners=100,
    qualityLevel=0.3,
    minDistance=7,
    blockSize=7
)

# V4.0: Camera adjustment detection thresholds
ADJUSTMENT_FLOW_THRESHOLD = 15.0   # Average optical flow magnitude indicating adjustment
ADJUSTMENT_VARIANCE_THRESHOLD = 50.0  # High variance = erratic movement (gimbal init, shake)
MIN_STABLE_FRAMES = 5  # Minimum consecutive stable frames to be considered "clean"


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


def detect_camera_adjustments(filepath: str, start_sec: float, end_sec: float) -> dict:
    """
    V4.0: Lucas-Kanade Optical Flow analysis to detect and isolate:
    - Drone takeoff shake
    - Gimbal initialization anomalies
    - Autofocus loops
    - Exposure hunting adjustments
    
    Returns:
        {
            "trim_start_sec": float,  # Recommended start after trimming bad frames
            "trim_end_sec": float,    # Recommended end (usually unchanged)
            "has_adjustment": bool,   # Whether camera adjustments were detected
            "adjustment_type": str,   # Type of adjustment found
            "stable_window_start": float,  # Where clean footage begins
            "stable_window_end": float     # Where clean footage ends
        }
    
    IMPORTANT: This function is CPU-intensive. Always call via:
        async with cv_semaphore:
            result = await asyncio.to_thread(detect_camera_adjustments, ...)
    """
    t0 = time.perf_counter()
    default_result = {
        "trim_start_sec": start_sec,
        "trim_end_sec": end_sec,
        "has_adjustment": False,
        "adjustment_type": "none",
        "stable_window_start": start_sec,
        "stable_window_end": end_sec
    }
    
    try:
        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            logger.warning(f"[CV LK] Cannot open: {filepath}")
            return default_result
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        start_frame = int(start_sec * fps)
        end_frame = min(int(end_sec * fps), total_frames)
        
        if end_frame - start_frame < MIN_STABLE_FRAMES * 2:
            cap.release()
            return default_result
        
        # Only analyze the first 3 seconds for adjustments
        # (gimbal/drone issues are almost always at the start)
        analysis_end_frame = min(start_frame + int(3.0 * fps), end_frame)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        success, first_frame = cap.read()
        if not success:
            cap.release()
            return default_result
        
        first_small = _downscale(first_frame)
        prev_gray = cv2.cvtColor(first_small, cv2.COLOR_BGR2GRAY)
        
        # Detect features to track
        prev_pts = cv2.goodFeaturesToTrack(prev_gray, mask=None, **FEATURE_PARAMS)
        
        if prev_pts is None:
            cap.release()
            return default_result
        
        flow_magnitudes = []
        frame_idx = start_frame + 1
        sample_step = max(1, int(fps / 10))  # ~10 samples per second
        
        while frame_idx < analysis_end_frame:
            # Check timeout
            if time.perf_counter() - t0 > TIMEOUT_SEC / 2:
                logger.warning(f"[CV LK TIMEOUT] {filepath}")
                break
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            success, frame = cap.read()
            if not success:
                break
            
            small = _downscale(frame)
            curr_gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            
            # Lucas-Kanade Optical Flow
            if prev_pts is not None and len(prev_pts) > 0:
                next_pts, status, err = cv2.calcOpticalFlowPyrLK(
                    prev_gray, curr_gray, prev_pts, None, **LK_PARAMS
                )
                
                if next_pts is not None and status is not None:
                    good_new = next_pts[status.ravel() == 1]
                    good_old = prev_pts[status.ravel() == 1]
                    
                    if len(good_new) > 0 and len(good_old) > 0:
                        # Calculate flow magnitudes
                        flow = good_new - good_old
                        magnitudes = np.sqrt(flow[:, 0]**2 + flow[:, 1]**2)
                        avg_magnitude = float(np.mean(magnitudes))
                        flow_magnitudes.append({
                            "frame": frame_idx,
                            "sec": frame_idx / fps,
                            "avg_flow": avg_magnitude,
                            "max_flow": float(np.max(magnitudes)),
                            "flow_variance": float(np.var(magnitudes))
                        })
                    
                    # Re-detect features periodically to avoid drift
                    if len(good_new) < 20:
                        prev_pts = cv2.goodFeaturesToTrack(curr_gray, mask=None, **FEATURE_PARAMS)
                    else:
                        prev_pts = good_new.reshape(-1, 1, 2)
                else:
                    prev_pts = cv2.goodFeaturesToTrack(curr_gray, mask=None, **FEATURE_PARAMS)
            
            prev_gray = curr_gray
            frame_idx += sample_step
        
        cap.release()
        
        if not flow_magnitudes:
            return default_result
        
        # Analyze flow pattern to detect adjustments
        has_adjustment = False
        adjustment_type = "none"
        stable_start_sec = start_sec
        
        # Check for erratic early movement (gimbal init, takeoff shake)
        early_flows = [f for f in flow_magnitudes if f["sec"] < start_sec + 2.0]
        late_flows = [f for f in flow_magnitudes if f["sec"] >= start_sec + 2.0]
        
        if early_flows:
            early_avg_flow = np.mean([f["avg_flow"] for f in early_flows])
            early_max_variance = max(f["flow_variance"] for f in early_flows)
            
            late_avg_flow = np.mean([f["avg_flow"] for f in late_flows]) if late_flows else 0
            
            # Detect gimbal initialization (high variance, then stabilizes)
            if early_max_variance > ADJUSTMENT_VARIANCE_THRESHOLD and early_avg_flow > ADJUSTMENT_FLOW_THRESHOLD:
                has_adjustment = True
                
                if early_max_variance > 100:
                    adjustment_type = "gimbal_init"
                elif early_avg_flow > 25:
                    adjustment_type = "drone_takeoff_shake"
                else:
                    adjustment_type = "camera_adjustment"
                
                # Find where the footage stabilizes
                for f in flow_magnitudes:
                    if f["sec"] > start_sec + 0.5 and f["avg_flow"] < ADJUSTMENT_FLOW_THRESHOLD * 0.5:
                        stable_start_sec = f["sec"]
                        break
                else:
                    # If no stable point found in first 3s, skip the first 2s
                    stable_start_sec = start_sec + 2.0
            
            # Detect exposure hunting (oscillating brightness changes = high flow variance)
            elif early_max_variance > ADJUSTMENT_VARIANCE_THRESHOLD * 0.7 and early_avg_flow < 5:
                has_adjustment = True
                adjustment_type = "exposure_hunting"
                stable_start_sec = start_sec + 1.5
            
            # Detect autofocus loop (moderate flow with periodic spikes)
            elif len(early_flows) >= 3:
                flow_vals = [f["avg_flow"] for f in early_flows]
                if max(flow_vals) > ADJUSTMENT_FLOW_THRESHOLD and min(flow_vals) < 3:
                    has_adjustment = True
                    adjustment_type = "autofocus_loop"
                    stable_start_sec = start_sec + 1.0
        
        elapsed = time.perf_counter() - t0
        
        if has_adjustment:
            logger.info(f"[CV LK] {filepath.split('/')[-1].split(chr(92))[-1]}: "
                        f"Detected {adjustment_type}. Trimming {start_sec:.1f}s → {stable_start_sec:.1f}s. "
                        f"({elapsed:.1f}s)")
        
        return {
            "trim_start_sec": stable_start_sec,
            "trim_end_sec": end_sec,
            "has_adjustment": has_adjustment,
            "adjustment_type": adjustment_type,
            "stable_window_start": stable_start_sec,
            "stable_window_end": end_sec
        }
    
    except Exception as e:
        elapsed = time.perf_counter() - t0
        logger.error(f"[CV LK ERROR] {filepath}: {e} ({elapsed:.1f}s)")
        return default_result


def check_media_quality(filepath: str) -> dict:
    """
    V4.0: Intelligent Media Filtering.
    Accept >= 720p. Only reject corrupted files or extreme blur.
    
    Returns:
        {
            "is_acceptable": bool,
            "resolution": (width, height),
            "blur_score": float,
            "rejection_reason": str or None
        }
    """
    try:
        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            return {"is_acceptable": False, "resolution": (0, 0),
                    "blur_score": 0, "rejection_reason": "corrupted_file"}
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # V4.0: Accept >= 720p (many premium assets from messaging apps are 720p)
        min_dimension = min(width, height)
        if min_dimension < 720:
            cap.release()
            return {"is_acceptable": False, "resolution": (width, height),
                    "blur_score": 0, "rejection_reason": f"below_720p ({width}x{height})"}
        
        # Quick blur check on a single frame
        success, frame = cap.read()
        cap.release()
        
        if not success:
            return {"is_acceptable": False, "resolution": (width, height),
                    "blur_score": 0, "rejection_reason": "cannot_read_frames"}
        
        gray = cv2.cvtColor(_downscale(frame), cv2.COLOR_BGR2GRAY)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Only reject extremely blurry content (Laplacian variance < 20)
        if blur_score < 20:
            return {"is_acceptable": False, "resolution": (width, height),
                    "blur_score": blur_score, "rejection_reason": f"extreme_blur (score={blur_score:.1f})"}
        
        return {"is_acceptable": True, "resolution": (width, height),
                "blur_score": blur_score, "rejection_reason": None}
    
    except Exception as e:
        logger.error(f"[CV QUALITY] Error checking {filepath}: {e}")
        return {"is_acceptable": False, "resolution": (0, 0),
                "blur_score": 0, "rejection_reason": f"error: {str(e)}"}


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

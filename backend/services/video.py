import httpx
import os
import asyncio
import time
import subprocess
import logging
import math
from typing import Optional, Callable

logger = logging.getLogger(__name__)

# Check ffmpeg installation
subprocess.run(["ffmpeg", "-version"], check=True)

def run_ffmpeg(cmd):
    logger.info(f"Running FFmpeg: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"FFmpeg failed:\n{result.stderr}")
        raise RuntimeError(f"FFmpeg failed:\n{result.stderr}")
    return result

def get_exact_duration(path: str) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(res.stdout.strip())
    except ValueError:
        return 5.0

def parse_time_to_seconds(time_str: str) -> float:
    try:
        return float(time_str)
    except ValueError:
        pass
    parts = str(time_str).split(':')
    total = 0.0
    for part in parts:
        total = total * 60 + float(part)
    return total

def has_audio(path: str) -> bool:
    cmd = ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return bool(res.stdout.strip())

def get_direct_url(url: str) -> str:
    if "dropbox.com" in url:
        return url.replace("?dl=0", "").replace("&dl=0", "") + ("&dl=1" if "?" in url else "?dl=1")
    return url

async def download_video(url: str, filename: str, project_id: str, on_progress: Optional[Callable] = None) -> str:
    os.makedirs(f"data/{project_id}/downloads", exist_ok=True)
    filepath = os.path.join(f"data/{project_id}/downloads", filename)
    
    if not url.startswith("http"):
        if os.path.exists(url):
            if on_progress: await on_progress(100)
            return url
        raise FileNotFoundError(f"Local file not found: {url}")

    direct_url = get_direct_url(url)
    start = time.perf_counter()

    async with httpx.AsyncClient(follow_redirects=True, timeout=300.0) as client:
        async with client.stream("GET", direct_url) as response:
            if response.status_code != 200: raise RuntimeError(f"Download failed: {response.status_code}")
            with open(filepath, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=262144):
                    f.write(chunk)

    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        raise RuntimeError("Downloaded file is empty or missing")

    logger.info(f"Downloaded {filename} in {time.perf_counter() - start:.1f}s")
    return filepath

async def create_preview(video_path: str, project_id: str) -> str:
    preview_filename = f"preview_{os.path.basename(video_path)}"
    os.makedirs(f"data/{project_id}/previews", exist_ok=True)
    preview_path = os.path.join(f"data/{project_id}/previews", preview_filename)
    
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-map", "0:v:0", "-map", "0:a:0?", "-dn",
        "-vf", "scale=-2:480", "-pix_fmt", "yuv420p",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        "-c:a", "aac", "-b:a", "64k", "-ac", "1", preview_path
    ]
    try:
        await asyncio.to_thread(run_ffmpeg, cmd)
    except RuntimeError:
        logger.warning("Preview generation failed, skipping.")
        return video_path
        
    return preview_path

async def process_segment(input_path: str, output_path: str, start_time: str, end_time: str, aspect_ratio: str = "9:16"):
    """
    Pass 1: High-Quality Trim, Crop, and Auto Color Normalization.
    This prepares clips with EXACT framerates and resolutions so `xfade` works perfectly.
    """
    start = time.perf_counter()
    
    # Calculate crop & scale for aspect ratio, plus auto-color matching and subtle Ken Burns simulated scale
    vf_filter = "crop=ih*9/16:ih,scale=720:1280"
    if aspect_ratio == "16:9": vf_filter = "crop=iw:iw*9/16,scale=1280:720"
    elif aspect_ratio == "1:1": vf_filter = "crop=ih:ih,scale=1080:1080"
    
    # Inject color normalization (Brighten slightly, boost contrast/saturation to look premium)
    # Inject standard fps to prevent xfade desyncs
    vf_chain = f"fps=30,{vf_filter},eq=contrast=1.05:brightness=0.01:saturation=1.1,format=yuv420p"

    cmd = [
        "ffmpeg", "-y",
        "-ss", start_time, "-to", end_time,
        "-i", input_path
    ]
    
    if not has_audio(input_path):
        cmd.extend(["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"])
        cmd.extend(["-map", "0:v:0", "-map", "1:a:0", "-shortest"])
        
    cmd.extend([
        "-vf", vf_chain,
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        output_path
    ])

    await asyncio.to_thread(run_ffmpeg, cmd)
    logger.info(f"[HQ PREP] Prepared clip in {time.perf_counter() - start:.1f}s")
    return output_path

async def build_reel(
    timeline_blocks: list[dict],
    input_paths: list[str],
    property_name: str,
    target_duration_sec: int,
    style: str,
    project_id: str,
    aspect_ratio: str = "9:16",
    music_path: Optional[str] = None,
    music_volume: float = 0.2,
    vo_volume: float = 1.0,
    on_progress: Optional[Callable] = None
) -> str:
    if not timeline_blocks: raise ValueError("Timeline is empty")

    output_dir = f"data/{project_id}/outputs"
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"{property_name.replace(' ', '_')}_{style}_{int(time.time())}.mp4"
    output_path = os.path.join(output_dir, output_filename)
    start = time.perf_counter()

    # --- SCENE GROUPING ENGINE (Full Property Tour Order) ---
    scene_order = {
        "drone": 1, "aerial": 2, "exterior": 3, "entrance": 4, "lobby": 5,
        "living room": 6, "kitchen": 7, "dining": 8, "bedroom": 9, "bathroom": 10,
        "balcony": 11, "pool": 12, "gym": 13, "parking": 14, "garden": 15,
        "amenities": 16, "closing drone": 17, "closing": 18, "other": 19
    }
    sorted_blocks = sorted(timeline_blocks, key=lambda x: scene_order.get(x.get("scene_type", "").lower(), 99))

    # --- STYLE-BASED TRANSITION RULES ---
    s = style.lower()
    transition_type = 'fade'
    transition_duration = 0.5
    if 'viral' in s:
        transition_type = 'wipeleft'
        transition_duration = 0.25
    elif 'cinematic' in s:
        transition_type = 'fade'
        transition_duration = 0.7
    elif 'realtor' in s:
        transition_type = 'slideleft'
        transition_duration = 0.4

    # 1. Process and normalize each scene into a temporary HQ clip
    ffmpeg_sem = asyncio.Semaphore(4)  # Limit concurrent FFmpeg jobs to prevent laptop freezing
    
    async def process_one(i, scene):
        v_idx = scene.get("video_index", 0)
        if v_idx >= len(input_paths): return None
        clip_path = os.path.join(output_dir, f"clip_{i}_{int(time.time())}.mp4")
        
        start_t = str(scene.get("start", "0"))
        
        # Use clip_duration_sec from Gemini if available (3-6 seconds per clip)
        clip_dur = scene.get("clip_duration_sec")
        if clip_dur and float(clip_dur) > 0:
            start_seconds = parse_time_to_seconds(start_t)
            end_t_val = start_seconds + float(clip_dur)
        else:
            end_t_val = parse_time_to_seconds(scene.get("end", "5"))
        
        # Add transition duration buffer so crossfade has visual material
        end_t = str(end_t_val + transition_duration)
        
        async with ffmpeg_sem:
            await process_segment(input_paths[v_idx], clip_path, start_t, end_t, aspect_ratio)
        return clip_path

    tasks = [process_one(i, scene) for i, scene in enumerate(sorted_blocks)]
    results = await asyncio.gather(*tasks)
    clip_paths = [r for r in results if r]

    if not clip_paths: raise ValueError("No valid clips generated")

    # If only 1 clip, just rename and return
    if len(clip_paths) == 1:
        os.rename(clip_paths[0], output_path)
        return output_path

    # --- DYNAMIC SMART CROSSFADE ENGINE ---
    durations = [get_exact_duration(p) for p in clip_paths]
    
    # Build filter_complex string
    filter_chains = []
    current_time = 0.0
    
    v_labels = [f"[{i}:v]" for i in range(len(clip_paths))]
    a_labels = [f"[{i}:a]" for i in range(len(clip_paths))]

    for i in range(len(clip_paths) - 1):
        current_time += durations[i]
        offset = current_time - (transition_duration * (i + 1))
        
        in1_v = v_labels[i] if i == 0 else f"[v{i}]"
        in2_v = v_labels[i+1]
        out_v = f"[v{i+1}]"
        
        xfade_cmd = f"{in1_v}{in2_v}xfade=transition={transition_type}:duration={transition_duration}:offset={offset:.3f}{out_v}"
        filter_chains.append(xfade_cmd)
        
        in1_a = a_labels[i] if i == 0 else f"[a{i}]"
        in2_a = a_labels[i+1]
        out_a = f"[a{i+1}]"
        acrossfade_cmd = f"{in1_a}{in2_a}acrossfade=d={transition_duration}{out_a}"
        filter_chains.append(acrossfade_cmd)

    filter_complex = ";".join(filter_chains)
    final_v = f"[v{len(clip_paths)-1}]"
    final_a = f"[a{len(clip_paths)-1}]"

    concat_cmd = ["ffmpeg", "-y"]
    
    if music_path and os.path.exists(music_path):
        music_idx = len(clip_paths)
        for cp in clip_paths:
            concat_cmd.extend(["-i", cp])
        # Add background music with infinite loop
        concat_cmd.extend(["-stream_loop", "-1", "-i", music_path])
        
        # Apply volumes and mix
        mixing_filter = f"{final_a}volume={vo_volume}[vo];[{music_idx}:a]volume={music_volume}[music_vol];[vo][music_vol]amix=inputs=2:duration=first:dropout_transition=2[mixed_a]"
        filter_complex = f"{filter_complex};{mixing_filter}"
        final_a = "[mixed_a]"
    else:
        for cp in clip_paths:
            concat_cmd.extend(["-i", cp])
        
        # Apply vo_volume even if no music
        if vo_volume != 1.0:
            mixing_filter = f"{final_a}volume={vo_volume}[mixed_a]"
            filter_complex = f"{filter_complex};{mixing_filter}"
            final_a = "[mixed_a]"

    # Assemble the massive FFmpeg command
    concat_cmd.extend([
        "-filter_complex", filter_complex,
        "-map", final_v,
        "-map", final_a,
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        output_path
    ])

    logger.info(f"Executing XFADE Graph with {len(clip_paths)} clips...")
    await asyncio.to_thread(run_ffmpeg, concat_cmd)

    # Cleanup temp clips
    # Add a short delay to ensure Windows releases the file handles from FFmpeg
    await asyncio.sleep(1.5)
    for cp in clip_paths:
        try: 
            os.remove(cp)
            logger.info(f"Deleted temp clip: {cp}")
        except OSError as e:
            logger.warning(f"Could not delete temp clip {cp}: {e}")

    elapsed = time.perf_counter() - start
    logger.info(f"[PERF] Final Dynamic Reel built with xfade in {elapsed:.1f}s")
    
    return output_path

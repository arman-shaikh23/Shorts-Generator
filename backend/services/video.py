import httpx
import os
import asyncio
import time
import subprocess
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)

# Check ffmpeg installation before anything else
subprocess.run(["ffmpeg", "-version"], check=True)

def run_ffmpeg(cmd):
    logger.info(f"Running FFmpeg: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    logger.info(result.stdout)
    if result.stderr:
        logger.error(result.stderr)

    logger.info(f"FFmpeg return code: {result.returncode}")

    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed:\n{result.stderr}"
        )

    return result

def get_total_duration(paths: list[str]) -> float:
    """Calculate the total raw duration (in seconds) of multiple video files."""
    total = 0.0
    for path in paths:
        try:
            cmd = [
                "ffprobe", "-v", "error", 
                "-show_entries", "format=duration", 
                "-of", "default=noprint_wrappers=1:nokey=1", 
                path
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                total += float(res.stdout.strip())
        except Exception as e:
            logger.error(f"Failed to get duration for {path}: {e}")
    return total

def get_direct_url(url: str) -> str:
    """Ensure the dropbox url is a direct download link."""
    if "dropbox.com" in url:
        return url.replace("?dl=0", "").replace("&dl=0", "") + ("&dl=1" if "?" in url else "?dl=1")
    return url

async def download_video(url: str, output_path: str) -> str:
    """Stream-download video directly to disk with large chunks. Avoids loading entire file into memory."""
    direct_url = get_direct_url(url)
    start = time.perf_counter()
    
    print(f"[DEBUG] Original URL: {url}")
    print(f"[DEBUG] Direct URL: {direct_url}")

    async with httpx.AsyncClient(follow_redirects=True, timeout=300.0) as client:
        async with client.stream("GET", direct_url) as response:
            print(f"[DEBUG] Final URL: {response.url}")
            print(f"[DEBUG] HTTP Status: {response.status_code}")
            
            content_type = response.headers.get("Content-Type", "")
            content_length = response.headers.get("Content-Length", "unknown")
            print(f"[DEBUG] Content-Type: {content_type}")
            print(f"[DEBUG] Content-Length: {content_length}")

            if response.status_code != 200:
                raise RuntimeError(f"Download failed: {response.status_code}")

            if "text/html" in content_type.lower():
                raise RuntimeError(f"Dropbox returned HTML instead of video. Content-Type={content_type}")

            with open(output_path, "wb") as f:
                # 256KB chunks for faster throughput vs the old 8KB
                async for chunk in response.aiter_bytes(chunk_size=262144):
                    f.write(chunk)

    if not os.path.exists(output_path):
        raise RuntimeError(f"File not created: {output_path}")

    size = os.path.getsize(output_path)

    if size == 0:
        raise RuntimeError("Downloaded file is empty")

    print(f"[DEBUG] Exact file path: {os.path.abspath(output_path)}")
    print(f"[DEBUG] Final file size: {size} bytes")

    elapsed = time.perf_counter() - start
    size_mb = size / (1024 * 1024)
    print(f"[PERF] Download: {elapsed:.1f}s  |  {size_mb:.1f} MB  |  {size_mb/elapsed:.1f} MB/s")
    return output_path

async def create_preview(input_path: str, preview_path: str) -> str:
    """Create a 480p low-res preview for Gemini analysis. Much faster upload & processing."""
    start = time.perf_counter()

    def get_preview_cmd(inp: str, out: str) -> list:
        return [
            "ffmpeg", "-y",
            "-fflags", "+genpts",
            "-i", inp,
            "-map", "0:v:0",
            "-map", "0:a:0?",
            "-dn",
            "-vf", "scale=-2:480",
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "28",
            "-c:a", "aac",
            "-b:a", "64k",
            "-ac", "1",
            out
        ]

    cmd = get_preview_cmd(input_path, preview_path)

    try:
        await asyncio.to_thread(run_ffmpeg, cmd)
    except RuntimeError as e:
        logger.warning(f"Preview generation failed, attempting normalization: {e}")
        normalized_path = input_path.replace(".mp4", "_normalized.mp4")
        if normalized_path == input_path:
            normalized_path += "_normalized.mp4"
            
        norm_cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-map", "0:v:0",
            "-map", "0:a:0?",
            "-dn",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            normalized_path
        ]
        await asyncio.to_thread(run_ffmpeg, norm_cmd)
        
        # Retry preview on normalized footage
        retry_cmd = get_preview_cmd(normalized_path, preview_path)
        await asyncio.to_thread(run_ffmpeg, retry_cmd)
        
        # Cleanup normalized intermediate file
        try:
            os.remove(normalized_path)
        except OSError:
            pass

    elapsed = time.perf_counter() - start
    orig_mb = os.path.getsize(input_path) / (1024 * 1024)
    prev_mb = os.path.getsize(preview_path) / (1024 * 1024)
    print(f"[PERF] Preview: {elapsed:.1f}s  |  {orig_mb:.1f} MB -> {prev_mb:.1f} MB  ({(1 - prev_mb/orig_mb)*100:.0f}% smaller)")
    return preview_path

async def process_segment(input_path: str, output_path: str, start_time: str, end_time: str):
    """
    Two-pass optimized pipeline:
      Pass 1: Stream-copy trim (near-instant, no re-encode)
      Pass 2: Crop to 9:16 vertical at 720x1280, fast preset, CRF 23
    """
    start = time.perf_counter()
    trimmed_path = output_path.replace(".mp4", "_trim.mp4")

    # --- Pass 1: Fast trim with stream copy (no re-encoding) ---
    trim_cmd = [
        "ffmpeg", "-y",
        "-ss", start_time,
        "-to", end_time,
        "-i", input_path,
        "-c", "copy",          # stream copy = instant
        "-avoid_negative_ts", "make_zero",
        trimmed_path
    ]

    await asyncio.to_thread(run_ffmpeg, trim_cmd)

    trim_elapsed = time.perf_counter() - start

    # --- Pass 2: Crop to vertical 9:16 at 720x1280 ---
    crop_start = time.perf_counter()
    crop_cmd = [
        "ffmpeg", "-y",
        "-i", trimmed_path,
        "-vf", "crop=ih*9/16:ih,scale=720:1280",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        output_path
    ]

    await asyncio.to_thread(run_ffmpeg, crop_cmd)

    # Cleanup temp trimmed file
    try:
        os.remove(trimmed_path)
    except OSError:
        pass

    total_elapsed = time.perf_counter() - start
    crop_elapsed = time.perf_counter() - crop_start
    print(f"[PERF] Segment export: trim={trim_elapsed:.1f}s  crop={crop_elapsed:.1f}s  total={total_elapsed:.1f}s")
    return output_path

async def build_reel(input_paths: list[str], timeline: list[dict], output_dir: str) -> str:
    """Extract individual scenes from their respective videos and concat them into a single reel."""
    start = time.perf_counter()
    clip_paths = []
    
    # 1. Extract and crop each scene sequentially (or we could use asyncio.gather)
    async def process_one(i, scene):
        v_idx = scene["video_index"]
        if v_idx >= len(input_paths):
            logger.warning(f"Scene {i} references invalid video_index {v_idx}. Skipping.")
            return None
            
        inp = input_paths[v_idx]
        clip_path = os.path.join(output_dir, f"clip_{i}.mp4")
        await process_segment(inp, clip_path, scene["start"], scene["end"])
        return clip_path

    # Parallelize extraction
    tasks = [process_one(i, scene) for i, scene in enumerate(timeline)]
    results = await asyncio.gather(*tasks)
    clip_paths = [r for r in results if r]

    # 2. Concat all extracted clips
    concat_txt = os.path.join(output_dir, "concat.txt")
    with open(concat_txt, "w") as f:
        for cp in clip_paths:
            f.write(f"file '{os.path.basename(cp)}'\n")
            
    final_output = os.path.join(output_dir, "final_reel.mp4")
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_txt,
        "-c", "copy",
        final_output
    ]
    
    await asyncio.to_thread(run_ffmpeg, concat_cmd)
    
    # Cleanup intermediate clips and concat.txt
    try:
        os.remove(concat_txt)
        for cp in clip_paths:
            os.remove(cp)
    except OSError:
        pass
        
    elapsed = time.perf_counter() - start
    logger.info(f"[PERF] Final Reel built from {len(clip_paths)} clips in {elapsed:.1f}s")
    
    return "/outputs/final_reel.mp4"

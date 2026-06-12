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

    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed:\n{result.stderr}"
        )

    return result

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
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", "scale=-2:480",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "28",
        "-c:a", "aac",
        "-b:a", "64k",
        "-ac", "1",           # mono audio is enough for analysis
        preview_path
    ]

    await asyncio.to_thread(run_ffmpeg, cmd)

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

async def process_segments_parallel(input_path: str, segments: list, output_dir: str) -> list:
    """Process ALL segments concurrently using asyncio.gather. Never sequential."""
    start = time.perf_counter()

    async def _process_one(i: int, segment: dict):
        output_filename = f"output_{i}.mp4"
        output_path = os.path.join(output_dir, output_filename)
        await process_segment(input_path, output_path, segment["start_time"], segment["end_time"])
        segment["video_url"] = f"/outputs/{output_filename}"
        return segment

    tasks = [_process_one(i, seg) for i, seg in enumerate(segments)]
    results = await asyncio.gather(*tasks)

    elapsed = time.perf_counter() - start
    print(f"[PERF] All {len(segments)} segments parallel: {elapsed:.1f}s total")
    return list(results)

import os
import asyncio
import time
import subprocess
import logging
import math
import glob
import urllib.parse
import shutil
from functools import lru_cache
from typing import Optional, Callable
from pathlib import Path

import httpx

from app.core.http_client import stream_with_pool_metrics

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif"}
IMAGE_CODECS = {"mjpeg", "jpeg", "png", "webp", "bmp", "gif", "tiff"}

@lru_cache(maxsize=1)
def _ensure_media_binaries() -> None:
    missing = [binary for binary in ("ffmpeg", "ffprobe") if shutil.which(binary) is None]
    if missing:
        missing_binaries = ", ".join(missing)
        raise RuntimeError(
            f"Missing required media binaries: {missing_binaries}. "
            "Install ffmpeg and ensure it is available on PATH."
        )

def run_ffmpeg(cmd):
    _ensure_media_binaries()
    logger.info(f"Running FFmpeg: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        logger.error(f"[FFMPEG TIMEOUT] Command hung for >120s. Killed.")
        raise RuntimeError("FFmpeg process timed out after 120 seconds")
    if result.returncode != 0:
        logger.error(f"FFmpeg failed:\n{result.stderr}")
        raise RuntimeError(f"FFmpeg failed:\n{result.stderr}")
    return result


def _probe_media(path: str) -> dict:
    _ensure_media_binaries()
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        path,
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except Exception:
        return {}
    if res.returncode != 0:
        return {}
    try:
        import json

        return json.loads(res.stdout or "{}")
    except Exception:
        return {}


def _has_video_stream_probe(probe_data: dict) -> bool:
    streams = probe_data.get("streams") or []
    return any(s.get("codec_type") == "video" for s in streams)


def _safe_float(val) -> Optional[float]:
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _is_still_image_probe(path: str, probe_data: dict) -> bool:
    streams = probe_data.get("streams") or []
    if len(streams) != 1:
        return False

    stream = streams[0]
    if stream.get("codec_type") != "video":
        return False

    format_name = ((probe_data.get("format") or {}).get("format_name") or "").lower()
    codec_name = (stream.get("codec_name") or "").lower()
    suffix = Path(path).suffix.lower()

    duration = _safe_float(stream.get("duration"))
    if duration is None:
        duration = _safe_float((probe_data.get("format") or {}).get("duration"))

    nb_frames = str(stream.get("nb_frames") or "").strip().lower()
    frame_unknown = nb_frames in {"", "n/a"}
    frame_single = nb_frames == "1"
    short_or_unknown_duration = duration is None or duration <= 0.25

    format_looks_image = any(
        token in format_name for token in ("image2", "jpeg_pipe", "png_pipe", "webp_pipe", "bmp_pipe", "tiff_pipe")
    )
    codec_looks_image = codec_name in IMAGE_CODECS
    suffix_looks_image = suffix in IMAGE_EXTENSIONS

    if format_looks_image:
        return True
    if codec_looks_image and short_or_unknown_duration and (frame_unknown or frame_single):
        return True
    if suffix_looks_image and codec_looks_image and short_or_unknown_duration:
        return True
    return False


def _build_photo_motion_path(image_path: str, project_id: str, upload_id: Optional[str]) -> str:
    safe_stem = Path(image_path).stem
    slug = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in safe_stem).strip("._") or "image"
    stamp = int(time.time() * 1000)
    suffix = upload_id or "asset"
    os.makedirs(f"data/{project_id}/processed", exist_ok=True)
    return os.path.join(f"data/{project_id}/processed", f"photo_motion_{slug}_{suffix}_{stamp}.mp4")


def _render_photo_motion_clip(image_path: str, output_path: str, duration_sec: float = 6.0, fps: int = 30) -> None:
    frame_count = max(1, int(duration_sec * fps))
    vf = (
        f"scale=1920:1080:force_original_aspect_ratio=increase,"
        f"crop=1920:1080,"
        f"zoompan=z='min(zoom+0.0008,1.12)':d={frame_count}:s=1920x1080:fps={fps},"
        "format=yuv420p"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        image_path,
        "-vf",
        vf,
        "-t",
        str(duration_sec),
        "-r",
        str(fps),
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        output_path,
    ]
    run_ffmpeg(cmd)


async def normalize_upload_media(media_path: str, project_id: str, upload_id: Optional[str] = None) -> tuple[str, str]:
    """
    Normalize uploaded media to a video path consumable by the downstream pipeline.
    Returns: (normalized_path, media_type) where media_type is "video" or "image".
    """
    probe_data = await asyncio.to_thread(_probe_media, media_path)
    if _is_still_image_probe(media_path, probe_data):
        motion_path = _build_photo_motion_path(media_path, project_id, upload_id)
        await asyncio.to_thread(_render_photo_motion_clip, media_path, motion_path)
        logger.info("Converted still image to motion clip: %s -> %s", media_path, motion_path)
        return motion_path, "image"

    if _has_video_stream_probe(probe_data):
        return media_path, "video"

    # Fallback path when ffprobe misses type but extension clearly indicates an image.
    if Path(media_path).suffix.lower() in IMAGE_EXTENSIONS:
        motion_path = _build_photo_motion_path(media_path, project_id, upload_id)
        await asyncio.to_thread(_render_photo_motion_clip, media_path, motion_path)
        logger.info("Converted image (extension fallback) to motion clip: %s -> %s", media_path, motion_path)
        return motion_path, "image"

    raise RuntimeError("Unsupported upload: could not detect a video stream or supported image format.")

def get_exact_duration(path: str) -> float:
    _ensure_media_binaries()
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
    _ensure_media_binaries()
    cmd = ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return bool(res.stdout.strip())

def get_direct_url(url: str) -> str:
    if "dropbox.com" in url:
        if "dl=0" in url:
            return url.replace("dl=0", "dl=1")
        elif "?" in url:
            return url + "&dl=1"
        else:
            return url + "?dl=1"
    return url


def is_youtube_url(url: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return False
    host = (parsed.netloc or "").lower().split(":")[0]
    if host in {"youtu.be", "youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}:
        return True
    return host.endswith(".youtube.com")


def _safe_file_stem(name: str, fallback: str = "video") -> str:
    stem = Path(name or "").stem.strip() or fallback
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in stem).strip("._")
    return cleaned or fallback


def _resolve_youtube_download_path(info: dict, output_dir: str, unique_prefix: str) -> str:
    candidates = [
        p for p in glob.glob(os.path.join(output_dir, f"{unique_prefix}.*"))
        if os.path.isfile(p) and not p.endswith(".part")
    ]
    if candidates:
        return max(candidates, key=os.path.getmtime)

    requested = info.get("requested_downloads") or []
    for item in requested:
        path = item.get("filepath")
        if path and os.path.exists(path):
            return path

    filepath = info.get("filepath")
    if filepath and os.path.exists(filepath):
        return filepath

    return ""


def _download_youtube_video_sync(url: str, filename: str, project_id: str) -> str:
    try:
        import yt_dlp
    except Exception as exc:
        raise RuntimeError("yt-dlp is not installed on the server.") from exc

    from app.core.config import get_settings

    settings = get_settings()
    output_dir = f"data/{project_id}/downloads"
    os.makedirs(output_dir, exist_ok=True)

    safe_stem = _safe_file_stem(filename, fallback="youtube_video")
    unique_prefix = f"{safe_stem}_{int(time.time() * 1000)}"
    output_template = os.path.join(output_dir, f"{unique_prefix}.%(ext)s")

    max_duration = max(0, int(getattr(settings, "YOUTUBE_MAX_DURATION_SEC", 0) or 0))

    def _duration_filter(info, *args, **kwargs):
        if max_duration <= 0:
            return None
        duration = info.get("duration")
        if isinstance(duration, (int, float)) and duration > max_duration:
            return (
                f"Video duration {int(duration)}s exceeds allowed limit "
                f"of {max_duration}s."
            )
        return None

    ydl_opts = {
        "outtmpl": output_template,
        "format": "bv*[height<=1080]+ba/b[height<=1080]/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "retries": 3,
        "fragment_retries": 3,
        "socket_timeout": 30,
        "match_filter": _duration_filter,
    }

    cookie_file = (getattr(settings, "YTDLP_COOKIES_FILE", "") or "").strip()
    if cookie_file:
        if os.path.exists(cookie_file):
            ydl_opts["cookiefile"] = cookie_file
        else:
            logger.warning("[YTDLP] Cookie file not found: %s", cookie_file)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    if not info:
        raise RuntimeError("No media metadata returned by yt-dlp.")

    if info.get("_type") == "playlist":
        raise RuntimeError("Playlist URLs are not supported. Please paste a single video URL.")

    downloaded_path = _resolve_youtube_download_path(info, output_dir, unique_prefix)
    if not downloaded_path:
        raise RuntimeError("yt-dlp completed but no downloaded file was found.")
    return downloaded_path

async def download_video(url: str, filename: str, project_id: str, on_progress: Optional[Callable] = None) -> str:
    os.makedirs(f"data/{project_id}/downloads", exist_ok=True)
    filepath = os.path.join(f"data/{project_id}/downloads", filename)
    
    if not url.startswith("http"):
        if os.path.exists(url):
            if on_progress: await on_progress(100)
            return url
        raise FileNotFoundError(f"Local file not found: {url}")

    if is_youtube_url(url):
        start = time.perf_counter()
        try:
            yt_path = await asyncio.to_thread(_download_youtube_video_sync, url, filename, project_id)
        except Exception as exc:
            logger.error("[YTDLP] Failed to download YouTube URL %s: %s", url, exc)
            raise RuntimeError(f"YouTube download failed: {exc}") from exc

        if not os.path.exists(yt_path) or os.path.getsize(yt_path) == 0:
            raise RuntimeError("YouTube download returned an empty or missing file")
        if on_progress:
            await on_progress(100)
        logger.info("Downloaded YouTube source in %.1fs", time.perf_counter() - start)
        return yt_path

    direct_url = get_direct_url(url)
    start = time.perf_counter()

    try:
        async with stream_with_pool_metrics("GET", direct_url) as response:
            if response.status_code != 200:
                raise RuntimeError(f"Download failed: {response.status_code}")
            with open(filepath, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=262144):
                    f.write(chunk)
    except httpx.PoolTimeout as exc:
        logger.error("[HTTP POOL] Timeout while waiting for a pooled download connection: %s (%s)", direct_url, exc)
        raise
    except httpx.TimeoutException as exc:
        logger.error("[HTTP POOL] Network timeout while downloading: %s (%s)", direct_url, exc)
        raise

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
    
    # Smart cropping to prevent out-of-bounds errors on various input aspect ratios
    # Calculates the largest possible crop box that fits within the source while maintaining the target aspect ratio
    if aspect_ratio == "16:9":
        vf_filter = "crop='min(iw,ih*16/9)':'min(ih,iw*9/16)',scale=1280:720"
    elif aspect_ratio == "1:1":
        vf_filter = "crop='min(iw,ih)':'min(ih,iw)',scale=1080:1080"
    else: # Default 9:16
        vf_filter = "crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',scale=720:1280"
    
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
    property_name: str,
    target_duration_sec: int,
    style: str,
    project_id: str,
    aspect_ratio: str = "9:16",
    music_path: Optional[str] = None,
    music_volume: float = 0.2,
    vo_volume: float = 1.0,
    on_progress: Optional[Callable] = None
) -> dict:
    if not timeline_blocks: raise ValueError("Timeline is empty")

    output_dir = f"data/{project_id}/outputs"
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"{property_name.replace(' ', '_')}_{style}_{int(time.time())}.mp4"
    output_path = os.path.join(output_dir, output_filename)
    start = time.perf_counter()

    # Calculate selected_duration from timeline
    selected_duration_sec = 0.0
    for blk in timeline_blocks:
        selected_duration_sec += float(blk.get("clip_duration_sec", 4.0))

    # --- LOOP CLOSURE: Add first clip to end for 2 seconds ---
    sorted_blocks = list(timeline_blocks)
    if sorted_blocks:
        first_clip_copy = dict(sorted_blocks[0])
        first_clip_copy["clip_duration_sec"] = 2.0
        first_clip_copy["_loop_closure"] = True
        sorted_blocks.append(first_clip_copy)

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
    ffmpeg_sem = asyncio.Semaphore(4)
    skipped_clips = []

    async def process_one(i, scene):
        local_path = scene.get("localPath")
        clip_id = scene.get("clip_id", f"{scene.get('video_index', i)}_{scene.get('start', '0')}_{scene.get('end', '5')}")
        is_loop_closure = bool(scene.get("_loop_closure"))
        
        if not local_path or not os.path.exists(local_path):
            logger.error(f"[SKIP] Missing local file for clip: {clip_id}")
            if not is_loop_closure:
                skipped_clips.append({"clip_id": clip_id, "reason": "missing_file"})
            return None
        
        clip_path = os.path.join(output_dir, f"clip_{i}_{int(time.time())}.mp4")

        start_seconds = parse_time_to_seconds(scene.get("start", "0"))
        start_t = str(start_seconds)

        # Use clip_duration_sec from optimizer (already bounded by trim logic)
        clip_dur = scene.get("clip_duration_sec")
        if clip_dur and float(clip_dur) > 0:
            end_t_val = start_seconds + float(clip_dur)
        else:
            end_t_val = parse_time_to_seconds(scene.get("end", "5"))

        # Add transition duration buffer so crossfade has visual material
        end_t = str(end_t_val + transition_duration)

        try:
            async with ffmpeg_sem:
                await process_segment(local_path, clip_path, start_t, end_t, aspect_ratio)
            return {"path": clip_path, "is_loop_closure": is_loop_closure}
        except RuntimeError as e:
            err_str = str(e)
            if "timed out" in err_str.lower():
                reason = "ffmpeg_timeout"
            elif "decode" in err_str.lower() or "codec" in err_str.lower():
                reason = "decode_error"
            else:
                reason = "ffmpeg_error"
            logger.error(f"[SKIP] FFmpeg failed for clip {clip_id}: {err_str[:100]}")
            if not is_loop_closure:
                skipped_clips.append({"clip_id": clip_id, "reason": reason})
            return None

    tasks = [process_one(i, scene) for i, scene in enumerate(sorted_blocks)]
    results = await asyncio.gather(*tasks)
    clip_entries = [r for r in results if r]
    clip_paths = [entry["path"] for entry in clip_entries]

    selected_count = len(timeline_blocks)
    rendered_count = sum(1 for entry in clip_entries if not entry["is_loop_closure"])

    if not clip_paths: raise ValueError("No valid clips generated")

    # If only 1 clip, just rename and return
    if len(clip_paths) == 1:
        os.rename(clip_paths[0], output_path)
        rendered_duration = get_exact_duration(output_path)
        return {
            "output_path": output_path,
            "rendered_count": rendered_count,
            "selected_count": selected_count,
            "selected_duration_sec": selected_duration_sec,
            "rendered_duration_sec": rendered_duration,
            "duration_coverage_pct": min(
                100.0,
                (rendered_duration / selected_duration_sec * 100) if selected_duration_sec > 0 else 100.0,
            ),
            "skipped_clips": skipped_clips
        }

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
        concat_cmd.extend(["-stream_loop", "-1", "-i", music_path])
        
        mixing_filter = f"{final_a}volume={vo_volume}[vo];[{music_idx}:a]volume={music_volume}[music_vol];[vo][music_vol]amix=inputs=2:duration=first:dropout_transition=2[mixed_a]"
        filter_complex = f"{filter_complex};{mixing_filter}"
        final_a = "[mixed_a]"
    else:
        for cp in clip_paths:
            concat_cmd.extend(["-i", cp])
        
        if vo_volume != 1.0:
            mixing_filter = f"{final_a}volume={vo_volume}[mixed_a]"
            filter_complex = f"{filter_complex};{mixing_filter}"
            final_a = "[mixed_a]"

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
    await asyncio.sleep(1.5)
    for cp in clip_paths:
        try: 
            os.remove(cp)
            logger.info(f"Deleted temp clip: {cp}")
        except OSError as e:
            logger.warning(f"Could not delete temp clip {cp}: {e}")

    elapsed = time.perf_counter() - start
    
    # Get actual rendered duration
    rendered_duration = get_exact_duration(output_path)
    duration_coverage = min(
        100.0,
        (rendered_duration / selected_duration_sec * 100) if selected_duration_sec > 0 else 100.0,
    )
    
    logger.info(f"[PERF] Final Dynamic Reel built with xfade in {elapsed:.1f}s")
    logger.info(f"[RENDER AUDIT] Selected: {selected_count} clips / {selected_duration_sec:.1f}s | Rendered: {rendered_count} clips / {rendered_duration:.1f}s | Duration Coverage: {duration_coverage:.1f}%")
    if skipped_clips:
        for sc in skipped_clips:
            logger.warning(f"[RENDER SKIP] clip_id={sc['clip_id']} reason={sc['reason']}")

    return {
        "output_path": output_path,
        "rendered_count": rendered_count,
        "selected_count": selected_count,
        "selected_duration_sec": selected_duration_sec,
        "rendered_duration_sec": rendered_duration,
        "duration_coverage_pct": round(duration_coverage, 1),
        "skipped_clips": skipped_clips
    }

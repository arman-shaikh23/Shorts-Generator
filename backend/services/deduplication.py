import hashlib
import os
import cv2
import imagehash
from PIL import Image
import numpy as np
from skimage.metrics import structural_similarity as ssim
import logging

logger = logging.getLogger(__name__)

def get_file_hash(filepath: str, chunk_size: int = 8192) -> str:
    """Stage 1: Extremely fast SHA256 hash of the entire file."""
    if not os.path.exists(filepath):
        return ""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def extract_frames(filepath: str, num_frames: int = 3) -> list[Image.Image]:
    """Extracts N frames evenly spaced across the video."""
    cap = cv2.VideoCapture(filepath)
    frames = []
    if not cap.isOpened():
        return frames
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        # Fallback if frame count is unavailable
        success, frame = cap.read()
        if success:
            frames.append(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
        cap.release()
        return frames

    # Calculate target frame indices (e.g. 25%, 50%, 75%)
    step = total_frames // (num_frames + 1)
    target_indices = [step * i for i in range(1, num_frames + 1)]
    
    for idx in target_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        success, frame = cap.read()
        if success:
            # Convert BGR to RGB for Pillow
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(Image.fromarray(rgb_frame))
            
    cap.release()
    return frames

def get_3_frame_phash(filepath: str) -> list[str]:
    """Stage 2: Returns perceptual hashes for beginning, middle, and end frames."""
    frames = extract_frames(filepath, num_frames=3)
    hashes = []
    for frame in frames:
        hashes.append(str(imagehash.phash(frame)))
    return hashes

def compare_phash_arrays(hashes_a: list[str], hashes_b: list[str]) -> int:
    """Returns the average hamming distance across the frames. Lower is more similar."""
    if not hashes_a or not hashes_b or len(hashes_a) != len(hashes_b):
        return 999
        
    total_distance = 0
    for ha, hb in zip(hashes_a, hashes_b):
        # Convert hex string back to ImageHash object to calculate distance
        dist = imagehash.hex_to_hash(ha) - imagehash.hex_to_hash(hb)
        total_distance += dist
        
    return total_distance / len(hashes_a)

def calculate_ssim(filepath_a: str, filepath_b: str) -> float:
    """Stage 3: Local SSIM comparison using the middle frame."""
    frames_a = extract_frames(filepath_a, num_frames=1)
    frames_b = extract_frames(filepath_b, num_frames=1)
    
    if not frames_a or not frames_b:
        return 0.0
        
    # Convert to grayscale numpy arrays
    img_a = cv2.cvtColor(np.array(frames_a[0]), cv2.COLOR_RGB2GRAY)
    img_b = cv2.cvtColor(np.array(frames_b[0]), cv2.COLOR_RGB2GRAY)
    
    # Resize B to match A's dimensions to allow comparison
    img_b_resized = cv2.resize(img_b, (img_a.shape[1], img_a.shape[0]))
    
    # Calculate SSIM (Structural Similarity Index)
    score, _ = ssim(img_a, img_b_resized, full=True)
    return float(score)

def analyze_duplicate(new_file: str, existing_files: list[dict]) -> tuple[bool, str, dict]:
    """
    Runs the 3-stage duplicate detection pipeline against a list of existing DB files.
    existing_files: list of dicts with 'localPath', 'fileHash', 'pHashes'
    Returns: (is_duplicate, reason, new_file_data_to_save)
    """
    new_data = {}
    
    # --- STAGE 1: File Hash ---
    f_hash = get_file_hash(new_file)
    new_data['fileHash'] = f_hash
    for ext in existing_files:
        if ext.get('fileHash') == f_hash:
            return True, "Stage 1: Exact File Hash Match", new_data

    # --- STAGE 2: 3-Frame pHash ---
    new_phashes = get_3_frame_phash(new_file)
    new_data['pHashes'] = new_phashes
    
    ssim_candidates = []
    
    if new_phashes:
        for ext in existing_files:
            ext_phashes = ext.get('pHashes')
            if ext_phashes:
                avg_distance = compare_phash_arrays(new_phashes, ext_phashes)
                if avg_distance <= 2:
                    return True, f"Stage 2: Perceptual Video Hash >95% Match (Distance: {avg_distance:.1f})", new_data
                elif avg_distance <= 10:
                    # Only run expensive SSIM if the visual distance is somewhat close
                    ssim_candidates.append(ext)

    # --- STAGE 3: Local SSIM Comparison ---
    # Only run SSIM on files that are 'near' duplicates identified by Stage 2
    for ext in ssim_candidates:
        ext_path = ext.get('localPath')
        if ext_path and os.path.exists(ext_path):
            try:
                similarity = calculate_ssim(new_file, ext_path)
                if similarity >= 0.95:  # 95% structural similarity (exact duplicates)
                    return True, f"Stage 3: Local SSIM Comparison ({similarity*100:.1f}%)", new_data
            except Exception as e:
                logger.error(f"Error calculating SSIM: {e}")
                
    return False, "", new_data

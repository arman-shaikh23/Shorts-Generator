import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Luxury Reel Flow Sequence
LUXURY_FLOW = [
    "drone establishing",
    "exterior",
    "entrance",
    "lobby",
    "living room",
    "living_room",
    "kitchen",
    "dining",
    "bedroom",
    "bathroom",
    "balcony",
    "amenities",
    "amenity",
    "pool",
    "gym",
    "garden",
    "closing exterior",
    "closing drone",
    "drone",
    "aerial",
    "closing"
]

def _get_flow_index(scene_type: str) -> int:
    st = scene_type.lower().strip()
    for i, val in enumerate(LUXURY_FLOW):
        if val == st:
            return i
    return 99

def parse_time(t) -> float:
    if isinstance(t, (int, float)): return float(t)
    t = str(t).strip()
    if ":" in t:
        parts = t.split(":")
        if len(parts) == 3: return float(parts[0])*3600 + float(parts[1])*60 + float(parts[2])
        if len(parts) == 2: return float(parts[0])*60 + float(parts[1])
    try:
        return float(t)
    except:
        return 0.0

class TimelineOptimizer:
    @staticmethod
    def optimize(clips: List[Dict[Any, Any]], ai_removed: List[Dict[Any, Any]] = None) -> List[Dict[Any, Any]]:
        if not clips:
            return []
            
        if ai_removed is None:
            ai_removed = []

        logger.info(f"[TIMELINE OPTIMIZER] Starting optimization for {len(clips)} clips")

        # 1. Remove clips with stability_score < 75
        filtered_by_stability = []
        for c in clips:
            if int(c.get("stability_score", 100)) >= 75:
                filtered_by_stability.append(c)
            else:
                ai_removed.append({"video_index": c.get("video_index"), "reason": f"Optimizer: Low stability score ({c.get('stability_score')})"})
        logger.info(f"[TIMELINE OPTIMIZER] Removed {len(clips) - len(filtered_by_stability)} clips due to stability < 75")

        # 2. Maximize property coverage - Keep all stable clips, do not remove based on room angle similarity
        diverse_clips = sorted(filtered_by_stability, key=lambda x: int(x.get("hero_score", 0)), reverse=True)
        
        if not diverse_clips:
            return []

        # 3. Select Opening and Closing shots
        opening_clip = max(diverse_clips, key=lambda x: int(x.get("hook_score", 0)))
        remaining_for_closing = [c for c in diverse_clips if c.get("video_index") != opening_clip.get("video_index")]
        closing_clip = None
        if remaining_for_closing:
            closing_clip = max(remaining_for_closing, key=lambda x: int(x.get("luxury_score", 0)))
        else:
            closing_clip = opening_clip

        middle_pool = [c for c in diverse_clips if c.get("video_index") not in [opening_clip.get("video_index"), closing_clip.get("video_index")]]

        # 4. Enforce Camera Direction Continuity & Build Final Timeline
        middle_pool.sort(key=lambda x: _get_flow_index(x.get("scene_type", "")))
        
        current_direction = opening_clip.get("camera_direction", "")
        optimized_middle = []
        
        while middle_pool:
            best_next = None
            for idx, c in enumerate(middle_pool):
                if c.get("camera_direction", "") == current_direction or current_direction == "":
                    best_next = middle_pool.pop(idx)
                    break
            
            if not best_next:
                best_next = middle_pool.pop(0)
                
            current_direction = best_next.get("camera_direction", "")
            optimized_middle.append(best_next)

        final_timeline = [opening_clip] + optimized_middle + ([closing_clip] if closing_clip and closing_clip != opening_clip else [])

        # 5 & 6. Trim first 3.0 seconds and limit to 3-6 seconds
        final_timeline_filtered = []
        for clip in final_timeline:
            start_val = parse_time(clip.get("start", 0))
            end_val = parse_time(clip.get("end", 5))
            
            # Reject if start_time is explicitly stated to be too low, but wait, Gemini 
            # might return start=0 which we trim. The prompt says "start_time < 3.0 sec".
            # We enforce by pushing the start value forward.
            start_val = max(start_val, 3.0)
            
            dur = end_val - start_val
            if dur > 6.0:
                end_val = start_val + 6.0
            elif dur < 3.0:
                end_val = start_val + 4.0
                
            clip["start"] = str(start_val)
            clip["end"] = str(end_val)
            clip["clip_duration_sec"] = end_val - start_val
            final_timeline_filtered.append(clip)

        logger.info(f"[TIMELINE OPTIMIZER] Final timeline built with {len(final_timeline_filtered)} clips.")
        return final_timeline_filtered

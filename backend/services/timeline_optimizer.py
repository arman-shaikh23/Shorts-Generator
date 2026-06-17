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
    def optimize(clips: List[Dict[Any, Any]], ai_removed: List[Dict[Any, Any]] = None, style: str = "Luxury") -> List[Dict[Any, Any]]:
        if not clips:
            return []
            
        if ai_removed is None:
            ai_removed = []

        logger.info(f"[TIMELINE OPTIMIZER] Starting optimization for {len(clips)} clips. Style: {style}")

        # 1. Calculate Hybrid final_score and filter
        scored_clips = []
        for c in clips:
            cv_stability = c.get("stability_score", 50)
            cv_lighting = c.get("lighting_score", 50)
            cv_motion = c.get("motion_quality_score", 50)
            gemini_luxury = c.get("luxury_score", 50)
            gemini_composition = c.get("composition_score", 50)
            
            final_score = (0.30 * cv_stability) + (0.25 * gemini_luxury) + (0.20 * gemini_composition) + (0.15 * cv_lighting) + (0.10 * cv_motion)
            c["final_score"] = final_score
            
            if final_score >= 40:
                scored_clips.append(c)
            else:
                ai_removed.append({"video_index": c.get("video_index"), "reason": f"Optimizer: Low final score ({final_score:.1f})"})
        
        if not scored_clips:
            return []

        # 2. Select Opening and Closing shots
        diverse_clips = sorted(scored_clips, key=lambda x: x.get("final_score", 0), reverse=True)
        
        opening_clip = max(diverse_clips, key=lambda x: int(x.get("hook_score", 0)))
        remaining_for_closing = [c for c in diverse_clips if c.get("video_index") != opening_clip.get("video_index")]
        closing_clip = max(remaining_for_closing, key=lambda x: int(x.get("luxury_score", 0))) if remaining_for_closing else opening_clip

        middle_pool = [c for c in diverse_clips if c.get("video_index") not in [opening_clip.get("video_index"), closing_clip.get("video_index")]]
        
        # 3. Smart Duration Pacing bounds
        def apply_trim(clip):
            start_val = parse_time(clip.get("start", 0))
            end_val = parse_time(clip.get("end", 5))
            dur = end_val - start_val
            f_score = clip.get("final_score", 0)
            stype = clip.get("scene_type", "").lower()
            
            if "drone" in stype or "aerial" in stype:
                if f_score >= 85: max_dur = 12.0
                else: max_dur = 8.0
            elif f_score >= 80:
                max_dur = 10.0
            else:
                max_dur = 7.0
                
            min_dur = 4.0
            
            if dur > max_dur:
                end_val = start_val + max_dur
            elif dur < min_dur:
                end_val = start_val + min_dur
                
            clip["start"] = str(start_val)
            clip["end"] = str(end_val)
            clip["clip_duration_sec"] = end_val - start_val
            return clip

        # Apply trims to all pool
        opening_clip = apply_trim(opening_clip)
        if closing_clip != opening_clip:
            closing_clip = apply_trim(closing_clip)
        middle_pool = [apply_trim(c) for c in middle_pool]

        # 4. Build sequence logic
        optimized_middle = []
        
        # Trackers
        last_room = opening_clip.get("scene_type", "").lower()
        last_direction = opening_clip.get("camera_direction", "")
        
        # Sort middle pool by flow order
        middle_pool.sort(key=lambda x: _get_flow_index(x.get("scene_type", "")))
        
        while middle_pool:
            best_idx = 0
            best_score = -9999
            
            for idx, c in enumerate(middle_pool):
                stype = c.get("scene_type", "").lower()
                f_score = c.get("final_score", 0)
                
                # Dynamic scoring based on final_score and flow logic
                score = f_score 
                
                # Flow progression
                score -= _get_flow_index(stype) * 0.1
                
                # Camera continuity
                if c.get("camera_direction") == last_direction and last_direction != "":
                    score += 5 
                elif c.get("camera_direction") in ["left_to_right", "right_to_left"] and last_direction in ["left_to_right", "right_to_left"] and c.get("camera_direction") != last_direction:
                    score -= 10
                    
                # Scene diversity penalty
                if stype == last_room:
                    score -= 15
                
                if score > best_score:
                    best_score = score
                    best_idx = idx
            
            best_next = middle_pool.pop(best_idx)
                
            stype = best_next.get("scene_type", "").lower()
            last_room = stype
            last_direction = best_next.get("camera_direction", "")
            
            optimized_middle.append(best_next)

        final_timeline = [opening_clip] + optimized_middle + ([closing_clip] if closing_clip and closing_clip != opening_clip else [])
        logger.info(f"[TIMELINE OPTIMIZER] Final timeline built with {len(final_timeline)} clips. Duration: {sum(c['clip_duration_sec'] for c in final_timeline):.1f}s")
        return final_timeline

import logging
from typing import List, Dict, Any, Optional
from collections import Counter

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
#  REELFORGE V4.0 — MASTER QUALITY UPGRADE
#  Story Arc Engine + Property Highlight Memory + Peak Window
#  Detection + Repetition Memory + Motion Diversity Tracking
# ═══════════════════════════════════════════════════════════════

# ── STORY ARC — Emotional Pacing Structure ────────────────────
# Replaces flat zone-based walkthrough with cinematic retention arcs.
# Each arc phase gets a percentage of the total timeline duration.

STORY_ARC = {
    "HOOK": 15,        # % — instant visual impact
    "DISCOVERY": 35,   # % — guided spatial orientation
    "SHOWCASE": 35,    # % — crown jewels and wow-factor
    "RESOLUTION": 15   # % — emotional payoff and loop closure
}

# Which scene types belong to which arc phase
ARC_PHASE_MAP = {
    "HOOK": ["drone", "aerial", "exterior", "entrance"],
    "DISCOVERY": [
        "lobby", "living_room", "living room", "dining", "corridor",
        "staircase", "entrance", "home_office", "home office",
        "conference_room", "conference room"
    ],
    "SHOWCASE": [
        "kitchen", "master_bedroom", "master bedroom", "bedroom",
        "walk_in_closet", "walk-in closet", "walk in closet",
        "bathroom", "pool", "balcony", "terrace", "rooftop",
        "gym", "garden", "amenities", "amenity"
    ],
    "RESOLUTION": [
        "exterior", "pool", "drone", "aerial", "garden",
        "closing exterior", "closing_exterior",
        "closing drone", "closing_drone", "closing"
    ]
}

# ── STORY ZONES — Backward-compatible zone mapping ────────────

STORY_ZONES = {
    "OPENING": ["drone", "aerial", "exterior", "entrance"],
    "INTERIOR": [
        "lobby", "living_room", "living room", "dining", "kitchen",
        "home_office", "home office", "conference_room", "conference room",
        "corridor", "staircase", "walk_in_closet", "walk-in closet", "walk in closet",
        "master_bedroom", "master bedroom", "bedroom", "bathroom"
    ],
    "AMENITIES": [
        "terrace", "balcony", "pool", "gym", "garden",
        "amenities", "amenity", "parking", "rooftop"
    ],
    "CLOSING": ["closing exterior", "closing_exterior", "closing drone", "closing_drone", "closing"]
}

# ── STRICT WALKTHROUGH ORDER — position = sort key ────────────

WALKTHROUGH_ORDER = [
    "drone", "aerial",                                          # 0-1
    "exterior",                                                 # 2
    "entrance",                                                 # 3
    "lobby",                                                    # 4
    "living_room", "living room",                               # 5-6
    "dining",                                                   # 7
    "kitchen",                                                  # 8
    "home_office", "home office",                               # 9-10
    "conference_room", "conference room",                       # 11-12
    "corridor",                                                 # 13
    "staircase",                                                # 14
    "walk_in_closet", "walk-in closet", "walk in closet",      # 15-17
    "master_bedroom", "master bedroom",                         # 18-19
    "bedroom",                                                  # 20
    "bathroom",                                                 # 21
    "terrace",                                                  # 22
    "balcony",                                                  # 23
    "pool",                                                     # 24
    "gym",                                                      # 25
    "garden",                                                   # 26
    "amenities", "amenity",                                     # 27-28
    "parking",                                                  # 29
    "rooftop",                                                  # 30
    "closing exterior", "closing_exterior",                     # 31-32
    "closing drone", "closing_drone", "closing"                 # 33-35
]

# ── ENHANCED ADJACENCY SCORING — V4.0 Bonuses/Penalties ──────

CONTINUITY_BONUS = {
    # Strong natural transitions (+25)
    ("exterior", "entrance"): 25,
    ("entrance", "lobby"): 25,
    ("lobby", "living_room"): 25,
    ("lobby", "living room"): 25,
    ("living_room", "dining"): 25,
    ("living room", "dining"): 25,
    ("living_room", "kitchen"): 25,
    ("living room", "kitchen"): 25,
    ("dining", "kitchen"): 20,
    ("kitchen", "dining"): 20,
    # Good transitions (+15)
    ("bedroom", "bathroom"): 15,
    ("master_bedroom", "bathroom"): 15,
    ("master bedroom", "bathroom"): 15,
    ("master_bedroom", "walk_in_closet"): 15,
    ("master bedroom", "walk_in_closet"): 15,
    ("corridor", "bedroom"): 10,
    ("staircase", "bedroom"): 10,
    ("staircase", "corridor"): 10,
    ("kitchen", "balcony"): 10,
    ("living_room", "balcony"): 10,
    ("living room", "balcony"): 10,
    ("pool", "garden"): 10,
    ("garden", "pool"): 10,
    # Heavy penalties for jarring jumps (-50)
    ("bathroom", "kitchen"): -50,
    ("bathroom", "lobby"): -50,
    ("kitchen", "pool"): -40,
    ("bedroom", "exterior"): -40,
    ("pool", "bedroom"): -40,
    ("gym", "kitchen"): -40,
    ("parking", "bedroom"): -50,
    ("bathroom", "living_room"): -50,
    ("bathroom", "living room"): -50,
    ("parking", "living_room"): -50,
    ("parking", "living room"): -50,
}

# ── REPETITION MEMORY — Anti-Repetition Engine ───────────────

RECENT_SCENE_MEMORY = 5  # Lookback window size
REPETITION_PENALTY = 30  # Score penalty for repeated scene_type

# ── MOTION DIVERSITY — Kinetic Framing Constraints ───────────

MOTION_DIVERSITY_PENALTY = 30  # Penalty for 3+ consecutive identical motion/direction/shot
MAX_CONSECUTIVE_SAME_MOTION = 2

# ── STYLE-BASED PROFILES ─────────────────────────────────────

STYLE_PROFILES = {
    "luxury_tour": {
        "target_asset_preservation": 1.0,  # 100%
        "pacing_speed": 1.0,
        "strict_walkthrough": True,
    },
    "premium_realtor": {
        "target_asset_preservation": 0.95,  # 90-100%
        "pacing_speed": 0.85,
        "strict_walkthrough": True,
    },
    "instagram_viral": {
        "target_asset_preservation": 0.75,  # 70-80%
        "pacing_speed": 0.60,
        "strict_walkthrough": False,
    }
}

STRICT_STYLES = {"luxury", "realtor", "cinematic", "realtor style", "luxury_tour", "premium_realtor"}
FLEXIBLE_STYLES = {"instagram", "viral", "instagram viral", "tiktok", "instagram_viral"}

# ── CLOSING SHOT PROHIBITIONS ─────────────────────────────────

CLOSING_BANNED = {"bathroom", "closet", "walk_in_closet", "walk-in closet", "walk in closet",
                  "bedroom", "kitchen", "corridor", "staircase", "parking", "home_office", "home office"}
CLOSING_PREFERRED = ["pool", "exterior", "drone", "aerial", "garden", "rooftop", "terrace", "balcony"]


# ═══════════════════════════════════════════════════════════════
#  UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════

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


def _get_walkthrough_index(scene_type: str) -> int:
    """Get hard position in walkthrough order."""
    st = scene_type.lower().strip().replace("_", " ")
    for i, val in enumerate(WALKTHROUGH_ORDER):
        normalized_val = val.replace("_", " ")
        if normalized_val == st or val == scene_type.lower().strip():
            return i
    return 999  # Unknown scenes go to end of their zone


def _get_zone(scene_type: str) -> str:
    """Determine which story zone a scene belongs to."""
    st = scene_type.lower().strip()
    for zone_name, zone_types in STORY_ZONES.items():
        for zt in zone_types:
            if zt == st or zt.replace("_", " ") == st.replace("_", " "):
                return zone_name
    return "INTERIOR"  # Default unknown scenes to interior


def _get_arc_phase(scene_type: str, hero_score: int = 0) -> str:
    """Determine which story arc phase a clip belongs to.
    Uses scene_type primarily, hero_score for tie-breaking."""
    st = scene_type.lower().strip()

    # Closing types always go to RESOLUTION
    closing_types = {"closing exterior", "closing_exterior", "closing drone", "closing_drone", "closing"}
    if st in closing_types or st.replace("_", " ") in closing_types:
        return "RESOLUTION"

    # Check each arc phase
    for phase, types_list in ARC_PHASE_MAP.items():
        for t in types_list:
            if t == st or t.replace("_", " ") == st.replace("_", " "):
                # Hero clips in DISCOVERY/SHOWCASE with very high scores
                # can be promoted to HOOK
                if phase in ("DISCOVERY", "SHOWCASE") and hero_score >= 95:
                    return "HOOK"
                return phase

    return "SHOWCASE"  # Default unknown scenes to showcase


def _get_continuity_score(prev_type: str, curr_type: str) -> int:
    """Get continuity bonus/penalty for transitioning between two scene types."""
    prev = prev_type.lower().strip()
    curr = curr_type.lower().strip()
    return CONTINUITY_BONUS.get((prev, curr), 0)


def _is_strict_walkthrough(style: str) -> bool:
    """Determine if this style requires strict walkthrough ordering."""
    s = style.lower().strip()
    for strict in STRICT_STYLES:
        if strict in s:
            return True
    return False


def _get_style_profile(style: str) -> dict:
    """Get the style configuration profile."""
    s = style.lower().strip()
    if "instagram" in s or "viral" in s or "tiktok" in s:
        return STYLE_PROFILES["instagram_viral"]
    elif "realtor" in s:
        return STYLE_PROFILES["premium_realtor"]
    return STYLE_PROFILES["luxury_tour"]


# ═══════════════════════════════════════════════════════════════
#  V4.0 WINDOW SCORE FORMULA
# ═══════════════════════════════════════════════════════════════

def calculate_window_score(clip: Dict) -> float:
    """
    V4.0 Peak Window Scoring Formula.
    window_score = (0.30 × luxury) + (0.25 × reveal) + (0.20 × composition)
                 + (0.15 × motion_quality) + (0.10 × lifestyle)
    """
    luxury = float(clip.get("luxury_score", 50))
    reveal = float(clip.get("reveal_score", clip.get("hook_score", 50)))
    composition = float(clip.get("composition_score", 50))
    motion = float(clip.get("motion_quality_score", clip.get("stability_score", 50)))
    lifestyle = float(clip.get("lifestyle_score", clip.get("luxury_score", 50)))

    return (0.30 * luxury) + (0.25 * reveal) + (0.20 * composition) + (0.15 * motion) + (0.10 * lifestyle)


# ═══════════════════════════════════════════════════════════════
#  PROPERTY HIGHLIGHT MEMORY MODULE
# ═══════════════════════════════════════════════════════════════

def build_highlight_memory(clips: List[Dict]) -> Dict[str, Optional[Dict]]:
    """
    Pre-scan all clips and cache the 'Crown Jewels' of the property.
    Returns a memory dict with hero assets for strategic placement.
    """
    memory = {
        "hero_pool": None,
        "hero_exterior": None,
        "hero_view": None,
        "hero_living_room": None,
    }

    pool_types = {"pool", "rooftop", "terrace"}
    exterior_types = {"exterior", "drone", "aerial"}
    view_types = {"drone", "aerial", "balcony", "rooftop", "terrace", "garden"}
    living_types = {"living_room", "living room", "lobby"}

    for c in clips:
        st = c.get("scene_type", "").lower().strip()
        score = calculate_window_score(c)
        clip_ref = {"clip_id": c.get("clip_id", ""), "video_index": c.get("video_index", 0),
                     "window_start": parse_time(c.get("start", 0)), "score": score, "scene_type": st}

        if st in pool_types:
            if memory["hero_pool"] is None or score > memory["hero_pool"]["score"]:
                memory["hero_pool"] = clip_ref

        if st in exterior_types:
            if memory["hero_exterior"] is None or score > memory["hero_exterior"]["score"]:
                memory["hero_exterior"] = clip_ref

        if st in view_types:
            if memory["hero_view"] is None or score > memory["hero_view"]["score"]:
                memory["hero_view"] = clip_ref

        if st.replace("_", " ") in living_types or st in living_types:
            if memory["hero_living_room"] is None or score > memory["hero_living_room"]["score"]:
                memory["hero_living_room"] = clip_ref

    logger.info(f"[HIGHLIGHT MEMORY] Built property highlights: "
                f"pool={'YES' if memory['hero_pool'] else 'NO'}, "
                f"exterior={'YES' if memory['hero_exterior'] else 'NO'}, "
                f"view={'YES' if memory['hero_view'] else 'NO'}, "
                f"living={'YES' if memory['hero_living_room'] else 'NO'}")

    return memory


# ═══════════════════════════════════════════════════════════════
#  REPETITION MEMORY ENGINE
# ═══════════════════════════════════════════════════════════════

def _apply_repetition_penalty(timeline: List[Dict]) -> List[Dict]:
    """
    Apply scoring penalties to clips whose scene_type appears
    within the last RECENT_SCENE_MEMORY positions.
    """
    if len(timeline) <= 1:
        return timeline

    penalized = list(timeline)
    penalty_count = 0

    for i in range(len(penalized)):
        lookback_start = max(0, i - RECENT_SCENE_MEMORY)
        lookback_types = [penalized[j].get("scene_type", "").lower() for j in range(lookback_start, i)]
        current_type = penalized[i].get("scene_type", "").lower()

        if current_type in lookback_types:
            penalized[i]["final_score"] = penalized[i].get("final_score", 50) - REPETITION_PENALTY
            penalty_count += 1
            logger.info(f"[REPETITION PENALTY] Clip {penalized[i].get('clip_id', i)}: "
                        f"'{current_type}' appeared in last {RECENT_SCENE_MEMORY} clips. "
                        f"Score reduced by {REPETITION_PENALTY}.")

    if penalty_count > 0:
        # Re-sort clips within their arc phases to push penalized clips later
        logger.info(f"[REPETITION MEMORY] Applied {penalty_count} penalties across timeline")

    return penalized


# ═══════════════════════════════════════════════════════════════
#  MOTION DIVERSITY ENGINE
# ═══════════════════════════════════════════════════════════════

def _apply_motion_diversity(timeline: List[Dict]) -> List[Dict]:
    """
    Deduct points for 3+ consecutive identical camera_motion,
    camera_direction, or shot_size.
    """
    if len(timeline) < 3:
        return timeline

    result = list(timeline)

    for field in ["camera_motion", "camera_direction", "shot_size"]:
        for i in range(2, len(result)):
            vals = [result[j].get(field, "").lower() for j in range(i - 2, i + 1)]
            if vals[0] and vals[0] == vals[1] == vals[2]:
                result[i]["final_score"] = result[i].get("final_score", 50) - MOTION_DIVERSITY_PENALTY
                logger.info(f"[MOTION DIVERSITY] Clip {result[i].get('clip_id', i)}: "
                            f"3 consecutive '{vals[0]}' {field}. Score reduced by {MOTION_DIVERSITY_PENALTY}.")

    return result


# ═══════════════════════════════════════════════════════════════
#  CLOSING SHOT ARCHITECTURE
# ═══════════════════════════════════════════════════════════════

def _enforce_closing_shot(timeline: List[Dict], highlight_memory: Dict) -> List[Dict]:
    """
    Ensure the last clip is a premium closing shot.
    Mandatory hierarchy: Pool → Exterior → Drone → Any non-banned.
    """
    if len(timeline) < 2:
        return timeline

    result = list(timeline)
    last_clip = result[-1]
    last_type = last_clip.get("scene_type", "").lower().strip()

    # Check if current closing is banned
    is_banned = any(banned in last_type for banned in CLOSING_BANNED)

    if is_banned:
        # Find the best closing candidate from the timeline
        best_closing_idx = None
        best_closing_priority = 999

        for i, c in enumerate(result[:-1]):  # Don't include the current last clip
            st = c.get("scene_type", "").lower().strip()
            for pri, preferred in enumerate(CLOSING_PREFERRED):
                if preferred in st and pri < best_closing_priority:
                    best_closing_priority = pri
                    best_closing_idx = i
                    break

        if best_closing_idx is not None:
            # Swap the banned closing with the best candidate
            clip = result.pop(best_closing_idx)
            result.append(clip)
            logger.info(f"[CLOSING SHOT] Swapped banned '{last_type}' ending with "
                        f"'{clip.get('scene_type')}' (priority {best_closing_priority})")
        else:
            logger.warning(f"[CLOSING SHOT] No preferred closing candidate found. Keeping '{last_type}'.")

    return result


# ═══════════════════════════════════════════════════════════════
#  SEQUENCE VALIDATION
# ═══════════════════════════════════════════════════════════════

def validate_storyline(timeline: List[Dict], strict: bool) -> List[Dict]:
    """
    Post-optimization validation. 4 rules:
    1. No backward movement in walkthrough order (strict mode only)
    2. No more than 3 same scene_type clips in a row
    3. Drone only in Opening/Closing zones, never middle
    4. Bathroom never appears before Living Room
    """
    if not timeline or len(timeline) < 2:
        return timeline

    fixed = list(timeline)
    changed = False

    # --- Rule 1: No backward movement (strict mode) ---
    if strict:
        # Already sorted by walkthrough order, so just verify
        for i in range(1, len(fixed)):
            curr_idx = _get_walkthrough_index(fixed[i].get("scene_type", ""))
            prev_idx = _get_walkthrough_index(fixed[i-1].get("scene_type", ""))
            if curr_idx < prev_idx and curr_idx != 999 and prev_idx != 999:
                # Backward movement detected — move this clip earlier
                clip = fixed.pop(i)
                # Find correct insertion point
                insert_at = 0
                for j in range(len(fixed)):
                    if _get_walkthrough_index(fixed[j].get("scene_type", "")) > curr_idx:
                        insert_at = j
                        break
                    insert_at = j + 1
                fixed.insert(insert_at, clip)
                changed = True
                logger.info(f"[VALIDATE] Rule 1: Moved '{clip.get('scene_type')}' from pos {i} to {insert_at}")

    # --- Rule 2: No more than 3 same scene_type in a row ---
    i = 0
    while i < len(fixed) - 3:
        types_window = [fixed[j].get("scene_type", "").lower() for j in range(i, min(i+4, len(fixed)))]
        if len(set(types_window)) == 1 and len(types_window) == 4:
            # 4 consecutive same type — move the 4th one later
            clip = fixed.pop(i + 3)
            # Insert after the next different type
            insert_at = min(i + 4, len(fixed))
            for j in range(i + 3, len(fixed)):
                if fixed[j].get("scene_type", "").lower() != types_window[0]:
                    insert_at = j + 1
                    break
            fixed.insert(insert_at, clip)
            changed = True
            logger.info(f"[VALIDATE] Rule 2: Broke consecutive run of '{types_window[0]}' at pos {i+3}")
        i += 1

    # --- Rule 3: Drone only in Opening/Closing, never middle ---
    drone_types = {"drone", "aerial"}
    # Find the boundary: after opening zone ends and before closing zone starts
    opening_end = 0
    closing_start = len(fixed)
    for idx, c in enumerate(fixed):
        zone = _get_zone(c.get("scene_type", ""))
        if zone != "OPENING" and opening_end == 0:
            opening_end = idx
        if zone == "CLOSING" and closing_start == len(fixed):
            closing_start = idx

    misplaced_drones = []
    for idx in range(opening_end, closing_start):
        if fixed[idx].get("scene_type", "").lower() in drone_types:
            misplaced_drones.append(idx)

    for offset, idx in enumerate(misplaced_drones):
        clip = fixed.pop(idx - offset)
        # Move to closing zone
        fixed.insert(max(0, len(fixed) - 1), clip)
        changed = True
        logger.info(f"[VALIDATE] Rule 3: Moved drone clip from middle (pos {idx}) to closing zone")

    # --- Rule 4: Bathroom never before Living Room ---
    bathroom_idx = None
    living_idx = None
    for idx, c in enumerate(fixed):
        st = c.get("scene_type", "").lower().replace("_", " ")
        if "bathroom" in st and bathroom_idx is None:
            bathroom_idx = idx
        if "living" in st and living_idx is None:
            living_idx = idx

    if bathroom_idx is not None and living_idx is not None and bathroom_idx < living_idx:
        # Swap bathroom to after living room
        clip = fixed.pop(bathroom_idx)
        # Insert right after living room (which shifted left by 1)
        new_living_idx = None
        for idx, c in enumerate(fixed):
            if "living" in c.get("scene_type", "").lower().replace("_", " "):
                new_living_idx = idx
                break
        if new_living_idx is not None:
            fixed.insert(new_living_idx + 1, clip)
            changed = True
            logger.info(f"[VALIDATE] Rule 4: Moved bathroom after living room")

    if changed:
        logger.info(f"[VALIDATE] Storyline validation applied corrections")
    else:
        logger.info(f"[VALIDATE] Storyline validation passed — no corrections needed")

    return fixed


# ═══════════════════════════════════════════════════════════════
#  MAIN OPTIMIZER — V4.0
# ═══════════════════════════════════════════════════════════════

class TimelineOptimizer:
    @staticmethod
    def optimize(clips: List[Dict[Any, Any]], ai_removed: List[Dict[Any, Any]] = None,
                 style: str = "Luxury", highlight_memory: Dict = None) -> List[Dict[Any, Any]]:
        if not clips:
            return []

        if ai_removed is None:
            ai_removed = []

        strict = _is_strict_walkthrough(style)
        profile = _get_style_profile(style)
        logger.info(f"[TIMELINE OPTIMIZER V4.0] Starting optimization for {len(clips)} clips. "
                     f"Style: {style}. Strict: {strict}. "
                     f"Asset preservation target: {profile['target_asset_preservation']*100:.0f}%")

        # ── Step 1: Calculate V4.0 Window Score + Hero Protection ──
        scored_clips = []
        for c in clips:
            # V4.0 Peak Window Score
            window_score = calculate_window_score(c)
            c["window_score"] = window_score

            # Legacy hybrid final_score for backward compatibility
            cv_stability = c.get("stability_score", 50)
            cv_lighting = c.get("lighting_score", 50)
            cv_motion = c.get("motion_quality_score", 50)
            gemini_luxury = c.get("luxury_score", 50)
            gemini_composition = c.get("composition_score", 50)

            final_score = (
                (0.30 * cv_stability) +
                (0.25 * gemini_luxury) +
                (0.20 * gemini_composition) +
                (0.15 * cv_lighting) +
                (0.10 * cv_motion)
            )
            c["final_score"] = final_score

            # ── V4.0 EXPANDED HERO PROTECTION ──
            # Lock clips with hero_score >= 90 OR reveal_score >= 90 OR luxury_score >= 90
            hero_score = int(c.get("hero_score", 0))
            reveal_score = int(c.get("reveal_score", c.get("hook_score", 0)))
            luxury_score = int(c.get("luxury_score", 0))

            is_immutable = hero_score >= 90 or reveal_score >= 90 or luxury_score >= 90

            if is_immutable:
                c["is_immutable"] = True
                scored_clips.append(c)
                logger.info(f"[HERO PROTECTED] Clip {c.get('clip_id', c.get('video_index'))} — "
                            f"hero={hero_score} reveal={reveal_score} luxury={luxury_score} "
                            f"window_score={window_score:.1f} [IMMUTABLE]")
                continue

            # Quality-First: Only remove truly poor clips
            if final_score >= 35:
                scored_clips.append(c)
            else:
                ai_removed.append({
                    "video_index": c.get("video_index"),
                    "clip_id": c.get("clip_id", ""),
                    "reason": f"Quality-First Filter: Low final score ({final_score:.1f} < 35)"
                })
                logger.info(f"[REMOVED] Clip {c.get('clip_id', c.get('video_index'))} — "
                            f"final_score={final_score:.1f} < 35 (quality floor)")

        if not scored_clips:
            return []

        # ── Step 2: Apply Style-Based Asset Preservation ──
        target_preservation = profile["target_asset_preservation"]
        min_clips = max(1, int(len(clips) * target_preservation))
        if len(scored_clips) < min_clips:
            logger.info(f"[COVERAGE] Only {len(scored_clips)} clips pass quality. "
                        f"Target was {min_clips}. Accepting all passing clips.")

        # ── Step 3: Smart Duration Pacing ──
        def apply_trim(clip):
            start_val = parse_time(clip.get("start", 0))
            end_val = parse_time(clip.get("end", 5))
            dur = end_val - start_val
            f_score = clip.get("final_score", 0)
            stype = clip.get("scene_type", "").lower()

            # V4.0 Contextual Clip Duration Rules
            if "drone" in stype or "aerial" in stype:
                # Premium Aerial / Drone Horizon Sweeps: 10-12s
                max_dur = 12.0 if f_score >= 85 else 10.0
                min_dur = 6.0
            elif f_score >= 80 or any(hero in stype for hero in
                                      ["kitchen", "living", "pool", "master", "patio", "terrace", "balcony"]):
                # Hero Asset Clips: 7-10s
                max_dur = 10.0
                min_dur = 5.0
            else:
                # Standard Functional Clips: 4-7s
                max_dur = 7.0
                min_dur = 3.0

            if dur > max_dur:
                end_val = start_val + max_dur
            elif dur < min_dur:
                end_val = start_val + min_dur

            clip["start"] = str(start_val)
            clip["end"] = str(end_val)
            clip["clip_duration_sec"] = end_val - start_val
            return clip

        scored_clips = [apply_trim(c) for c in scored_clips]

        # ── Step 4: Build Highlight Memory (if not provided) ──
        if highlight_memory is None:
            highlight_memory = build_highlight_memory(scored_clips)

        # ── Step 5: Build Sequence ──
        if strict:
            # V4.0 STORY ARC: Emotionally-paced walkthrough
            final_timeline = _build_story_arc(scored_clips, highlight_memory)
        else:
            # FLEXIBLE (Instagram/Viral): Hero-score ordering with diversity
            final_timeline = _build_flexible_sequence(scored_clips)

        # ── Step 6: Apply Repetition Memory ──
        final_timeline = _apply_repetition_penalty(final_timeline)

        # ── Step 7: Apply Motion Diversity ──
        final_timeline = _apply_motion_diversity(final_timeline)

        # ── Step 8: Re-sort by adjusted scores within phases ──
        # After penalties, re-sort penalized clips to push them later
        final_timeline = _resort_after_penalties(final_timeline, strict)

        # ── Step 9: Enforce Closing Shot Architecture ──
        final_timeline = _enforce_closing_shot(final_timeline, highlight_memory)

        # ── Step 10: Validate Storyline ──
        final_timeline = validate_storyline(final_timeline, strict)

        total_dur = sum(c.get("clip_duration_sec", 4.0) for c in final_timeline)
        logger.info(f"[TIMELINE OPTIMIZER V4.0] Final: {len(final_timeline)} clips, {total_dur:.1f}s. "
                     f"Strict={strict}. Coverage={len(final_timeline)}/{len(clips)} "
                     f"({len(final_timeline)/len(clips)*100:.0f}%)")
        return final_timeline


# ═══════════════════════════════════════════════════════════════
#  STORY ARC BUILDER — V4.0
# ═══════════════════════════════════════════════════════════════

def _build_story_arc(clips: List[Dict], highlight_memory: Dict) -> List[Dict]:
    """
    V4.0 STORY ARC MODE for Luxury/Realtor.
    Maps clips into 4 emotional arc phases:
    HOOK (15%) → DISCOVERY (35%) → SHOWCASE (35%) → RESOLUTION (15%)

    Uses Property Highlight Memory for strategic hero placement.
    """
    # Phase 1: Categorize clips into arc phases
    phases = {"HOOK": [], "DISCOVERY": [], "SHOWCASE": [], "RESOLUTION": []}

    for c in clips:
        st = c.get("scene_type", "").lower().strip()
        hero_score = int(c.get("hero_score", 0))
        phase = _get_arc_phase(st, hero_score)
        phases[phase].append(c)

    # Phase 2: Sort within each arc phase by walkthrough order, then score
    for phase_name in phases:
        phases[phase_name].sort(key=lambda x: (
            _get_walkthrough_index(x.get("scene_type", "")),
            -x.get("window_score", x.get("final_score", 0))
        ))

    # Phase 3: Strategic hero placement from Highlight Memory
    # HOOK: Force hero_exterior or hero_view to the front
    hook_hero_id = None
    if highlight_memory.get("hero_exterior"):
        hook_hero_id = highlight_memory["hero_exterior"].get("clip_id")
    elif highlight_memory.get("hero_view"):
        hook_hero_id = highlight_memory["hero_view"].get("clip_id")

    if hook_hero_id:
        # Move the hero clip to position 0 in HOOK phase
        for phase_clips in phases.values():
            for i, c in enumerate(phase_clips):
                if c.get("clip_id") == hook_hero_id:
                    clip = phase_clips.pop(i)
                    phases["HOOK"].insert(0, clip)
                    logger.info(f"[STORY ARC] Deployed hero '{clip.get('scene_type')}' as HOOK opener")
                    break

    # RESOLUTION: Force hero_pool or drone to the end
    resolution_hero_id = None
    if highlight_memory.get("hero_pool"):
        resolution_hero_id = highlight_memory["hero_pool"].get("clip_id")

    if resolution_hero_id:
        for phase_clips in phases.values():
            for i, c in enumerate(phase_clips):
                if c.get("clip_id") == resolution_hero_id:
                    clip = phase_clips.pop(i)
                    phases["RESOLUTION"].append(clip)
                    logger.info(f"[STORY ARC] Deployed hero '{clip.get('scene_type')}' as RESOLUTION climax")
                    break

    # Phase 4: Apply continuity scoring within each arc phase
    for phase_name in phases:
        if len(phases[phase_name]) > 1:
            phases[phase_name] = _apply_continuity_sort(phases[phase_name])

    # Phase 5: Ensure HOOK and RESOLUTION have minimum content
    # If HOOK is empty, steal the best exterior/drone from DISCOVERY
    if not phases["HOOK"] and phases["DISCOVERY"]:
        for i, c in enumerate(phases["DISCOVERY"]):
            st = c.get("scene_type", "").lower()
            if st in {"drone", "aerial", "exterior"}:
                phases["HOOK"].append(phases["DISCOVERY"].pop(i))
                logger.info(f"[STORY ARC] Promoted '{st}' from DISCOVERY to HOOK")
                break

    if not phases["RESOLUTION"] and phases["SHOWCASE"]:
        # Steal a pool/exterior/drone from SHOWCASE for closing
        for i in range(len(phases["SHOWCASE"]) - 1, -1, -1):
            st = phases["SHOWCASE"][i].get("scene_type", "").lower()
            if st in {"pool", "exterior", "drone", "aerial", "garden"}:
                phases["RESOLUTION"].append(phases["SHOWCASE"].pop(i))
                logger.info(f"[STORY ARC] Promoted '{st}' from SHOWCASE to RESOLUTION")
                break

    # Assemble final timeline: HOOK → DISCOVERY → SHOWCASE → RESOLUTION
    final = phases["HOOK"] + phases["DISCOVERY"] + phases["SHOWCASE"] + phases["RESOLUTION"]

    logger.info(f"[STORY ARC] Phases: HOOK={len(phases['HOOK'])}, DISCOVERY={len(phases['DISCOVERY'])}, "
                f"SHOWCASE={len(phases['SHOWCASE'])}, RESOLUTION={len(phases['RESOLUTION'])}")
    return final


def _build_flexible_sequence(clips: List[Dict]) -> List[Dict]:
    """
    FLEXIBLE MODE for Instagram/Viral.
    Prioritizes hero_score and visual impact over property walkthrough order.
    Still avoids same-room consecutive clips.
    """
    # Sort by window_score descending, then hero_score
    sorted_clips = sorted(clips, key=lambda x: (
        -x.get("window_score", 0),
        -int(x.get("hero_score", 0)),
        -x.get("final_score", 0)
    ))

    if not sorted_clips:
        return []

    # Greedy placement: pick highest-score clip that isn't same scene as last
    result = [sorted_clips[0]]
    remaining = sorted_clips[1:]

    while remaining:
        last_type = result[-1].get("scene_type", "").lower()
        # Find best next clip that's a different scene type
        best_idx = 0
        for idx, c in enumerate(remaining):
            if c.get("scene_type", "").lower() != last_type:
                best_idx = idx
                break
        result.append(remaining.pop(best_idx))

    return result


def _apply_continuity_sort(clips: List[Dict]) -> List[Dict]:
    """
    Within a zone/phase, apply continuity scoring to optimize room-to-room flow.
    Uses walkthrough order as primary sort, continuity bonus as tie-breaker.
    """
    if len(clips) <= 1:
        return clips

    # Start with the first clip (already sorted by walkthrough order)
    result = [clips[0]]
    remaining = list(clips[1:])

    while remaining:
        last_type = result[-1].get("scene_type", "").lower()

        best_idx = 0
        best_score = -9999

        for idx, c in enumerate(remaining):
            curr_type = c.get("scene_type", "").lower()
            # Primary: walkthrough order
            walk_score = -_get_walkthrough_index(curr_type)
            # Secondary: continuity bonus
            cont_score = _get_continuity_score(last_type, curr_type)
            # Tertiary: window_score (V4.0)
            quality = c.get("window_score", c.get("final_score", 0)) * 0.1

            total = walk_score + cont_score + quality

            if total > best_score:
                best_score = total
                best_idx = idx

        result.append(remaining.pop(best_idx))

    return result


def _resort_after_penalties(timeline: List[Dict], strict: bool) -> List[Dict]:
    """
    After repetition and motion diversity penalties, re-sort penalized
    clips to push them later in the sequence while maintaining arc structure.
    """
    if not timeline or len(timeline) < 3:
        return timeline

    # For strict mode, maintain arc phase structure
    if strict:
        # Group by arc phase, re-sort within each phase
        phases = {"HOOK": [], "DISCOVERY": [], "SHOWCASE": [], "RESOLUTION": []}
        for c in timeline:
            phase = _get_arc_phase(c.get("scene_type", ""), int(c.get("hero_score", 0)))
            phases[phase].append(c)

        for phase_name in phases:
            phases[phase_name].sort(key=lambda x: (
                _get_walkthrough_index(x.get("scene_type", "")),
                -x.get("final_score", 0)
            ))

        return phases["HOOK"] + phases["DISCOVERY"] + phases["SHOWCASE"] + phases["RESOLUTION"]
    else:
        # For flexible mode, just re-sort by adjusted score
        return sorted(timeline, key=lambda x: (
            -x.get("window_score", 0),
            -x.get("final_score", 0)
        ))

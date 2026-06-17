import logging
from typing import List, Dict, Any
from collections import Counter

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
#  STORY ZONES — Real Estate Walkthrough Structure
# ═══════════════════════════════════════════════════════════════

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

# Hard walkthrough order — position = sort key
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

# ═══════════════════════════════════════════════════════════════
#  ROOM CONTINUITY SCORING — Natural Transition Bonuses
# ═══════════════════════════════════════════════════════════════

CONTINUITY_BONUS = {
    ("exterior", "entrance"): 10,
    ("entrance", "lobby"): 10,
    ("lobby", "living_room"): 10,
    ("lobby", "living room"): 10,
    ("living_room", "dining"): 10,
    ("living room", "dining"): 10,
    ("living_room", "kitchen"): 10,
    ("living room", "kitchen"): 10,
    ("kitchen", "dining"): 8,
    ("dining", "kitchen"): 8,
    ("bedroom", "bathroom"): 8,
    ("master_bedroom", "bathroom"): 8,
    ("master bedroom", "bathroom"): 8,
    ("master_bedroom", "walk_in_closet"): 8,
    ("master bedroom", "walk_in_closet"): 8,
    ("corridor", "bedroom"): 5,
    ("staircase", "bedroom"): 5,
    ("staircase", "corridor"): 5,
    # Penalties for unnatural jumps
    ("kitchen", "pool"): -15,
    ("bathroom", "kitchen"): -10,
    ("bedroom", "exterior"): -15,
    ("pool", "bedroom"): -15,
    ("bathroom", "lobby"): -10,
    ("gym", "kitchen"): -10,
    ("parking", "bedroom"): -15,
}

# ═══════════════════════════════════════════════════════════════
#  STYLE-BASED WALKTHROUGH STRICTNESS
# ═══════════════════════════════════════════════════════════════

STRICT_STYLES = {"luxury", "realtor", "cinematic", "realtor style"}
FLEXIBLE_STYLES = {"instagram", "viral", "instagram viral", "tiktok"}


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
#  MAIN OPTIMIZER
# ═══════════════════════════════════════════════════════════════

class TimelineOptimizer:
    @staticmethod
    def optimize(clips: List[Dict[Any, Any]], ai_removed: List[Dict[Any, Any]] = None, style: str = "Luxury") -> List[Dict[Any, Any]]:
        if not clips:
            return []

        if ai_removed is None:
            ai_removed = []

        strict = _is_strict_walkthrough(style)
        logger.info(f"[TIMELINE OPTIMIZER] Starting optimization for {len(clips)} clips. Style: {style}. Strict: {strict}")

        # ── Step 1: Calculate Hybrid final_score + Hero Protection ──
        scored_clips = []
        for c in clips:
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

            # HERO CLIP PROTECTION: Never remove clips with hero_score >= 90
            hero_score = int(c.get("hero_score", 0))
            if hero_score >= 90:
                scored_clips.append(c)
                logger.info(f"[HERO PROTECTED] Clip {c.get('clip_id', c.get('video_index'))} — hero_score={hero_score}, final_score={final_score:.1f}")
                continue

            if final_score >= 40:
                scored_clips.append(c)
            else:
                ai_removed.append({
                    "video_index": c.get("video_index"),
                    "clip_id": c.get("clip_id", ""),
                    "reason": f"Optimizer: Low final score ({final_score:.1f})"
                })
                logger.info(f"[REMOVED] Clip {c.get('clip_id', c.get('video_index'))} — final_score={final_score:.1f} < 40")

        if not scored_clips:
            return []

        # ── Step 2: Smart Duration Pacing ──
        def apply_trim(clip):
            start_val = parse_time(clip.get("start", 0))
            end_val = parse_time(clip.get("end", 5))
            dur = end_val - start_val
            f_score = clip.get("final_score", 0)
            stype = clip.get("scene_type", "").lower()

            if "drone" in stype or "aerial" in stype:
                max_dur = 12.0 if f_score >= 85 else 8.0
            elif f_score >= 80:
                max_dur = 10.0
            else:
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

        # ── Step 3: Build Sequence ──
        if strict:
            # STRICT WALKTHROUGH: Sort purely by walkthrough order
            final_timeline = _build_strict_walkthrough(scored_clips)
        else:
            # FLEXIBLE (Instagram/Viral): Hero-score ordering with diversity
            final_timeline = _build_flexible_sequence(scored_clips)

        # ── Step 4: Validate Storyline ──
        final_timeline = validate_storyline(final_timeline, strict)

        total_dur = sum(c.get("clip_duration_sec", 4.0) for c in final_timeline)
        logger.info(f"[TIMELINE OPTIMIZER] Final: {len(final_timeline)} clips, {total_dur:.1f}s. Strict={strict}")
        return final_timeline


def _build_strict_walkthrough(clips: List[Dict]) -> List[Dict]:
    """
    STRICT WALKTHROUGH MODE for Luxury/Realtor.
    Groups clips by Story Zone, sorts within each zone by walkthrough order,
    applies continuity scoring for tie-breaking.
    """
    # Group clips by zone
    zones = {"OPENING": [], "INTERIOR": [], "AMENITIES": [], "CLOSING": []}
    for c in clips:
        zone = _get_zone(c.get("scene_type", ""))
        zones[zone].append(c)

    # Sort each zone by walkthrough order, then by final_score for tie-breaking
    for zone_name in zones:
        zones[zone_name].sort(key=lambda x: (
            _get_walkthrough_index(x.get("scene_type", "")),
            -x.get("final_score", 0)
        ))

    # Apply continuity scoring within INTERIOR zone (most clips live here)
    if len(zones["INTERIOR"]) > 1:
        zones["INTERIOR"] = _apply_continuity_sort(zones["INTERIOR"])

    # Assemble final timeline: OPENING → INTERIOR → AMENITIES → CLOSING
    final = zones["OPENING"] + zones["INTERIOR"] + zones["AMENITIES"] + zones["CLOSING"]

    logger.info(f"[STRICT WALKTHROUGH] Zones: OPENING={len(zones['OPENING'])}, INTERIOR={len(zones['INTERIOR'])}, AMENITIES={len(zones['AMENITIES'])}, CLOSING={len(zones['CLOSING'])}")
    return final


def _build_flexible_sequence(clips: List[Dict]) -> List[Dict]:
    """
    FLEXIBLE MODE for Instagram/Viral.
    Prioritizes hero_score and visual impact over property walkthrough order.
    Still avoids same-room consecutive clips.
    """
    # Sort by hero_score descending, then final_score
    sorted_clips = sorted(clips, key=lambda x: (
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
    Within a zone, apply continuity scoring to optimize room-to-room flow.
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
            # Tertiary: final_score
            quality = c.get("final_score", 0) * 0.1

            total = walk_score + cont_score + quality

            if total > best_score:
                best_score = total
                best_idx = idx

        result.append(remaining.pop(best_idx))

    return result

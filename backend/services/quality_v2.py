import logging
import math
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)


def normalize_scene_type(scene_type: str) -> str:
    return (scene_type or "").strip().lower().replace("_", " ")


STORY_CATEGORY_ALIASES = {
    "drone": "exterior_drone",
    "aerial": "exterior_drone",
    "exterior": "exterior_drone",
    "entrance": "entrance",
    "lobby": "entrance",
    "living room": "living_room",
    "living": "living_room",
    "dining": "dining_area",
    "kitchen": "kitchen",
    "master bedroom": "bedroom",
    "bedroom": "bedroom",
    "bathroom": "bathroom",
    "balcony": "balcony",
    "terrace": "balcony",
    "rooftop": "balcony",
    "pool": "amenities",
    "gym": "amenities",
    "garden": "amenities",
    "amenities": "amenities",
    "amenity": "amenities",
    "parking": "amenities",
    "closing drone": "exit_shot",
    "closing exterior": "exit_shot",
    "closing": "exit_shot",
    "exit": "exit_shot",
}

STORY_POSITION_SCORES = {
    "exterior_drone": 10,
    "entrance": 20,
    "living_room": 30,
    "dining_area": 35,
    "kitchen": 40,
    "bedroom": 50,
    "bathroom": 60,
    "balcony": 70,
    "amenities": 80,
    "exit_shot": 90,
    "miscellaneous": 75,
}

STORY_SEQUENCE = [
    "exterior_drone",
    "entrance",
    "living_room",
    "dining_area",
    "kitchen",
    "bedroom",
    "bathroom",
    "balcony",
    "amenities",
    "exit_shot",
    "miscellaneous",
]
STORY_SEQUENCE_INDEX = {name: i for i, name in enumerate(STORY_SEQUENCE)}

HARD_TRANSITION_PENALTIES = {
    ("bathroom", "exterior_drone"),
    ("bathroom", "kitchen"),
    ("amenities", "bathroom"),
    ("exit_shot", "kitchen"),
}


DEFAULT_STABILITY_RESULT = {
    "stability_score_v2": 0.5,
    "stability_confidence_v2": 0.0,
    "motion_variance": 0.0,
    "camera_shake_score": 0.5,
    "optical_flow_consistency": 0.5,
    "rotation_stability": 0.5,
    "translation_stability": 0.5,
    "sample_pairs": 0,
}


def classify_story_scene(scene_type: str) -> Dict[str, Any]:
    normalized = normalize_scene_type(scene_type)
    if not normalized:
        return {
            "story_category": "miscellaneous",
            "story_position_score": STORY_POSITION_SCORES["miscellaneous"],
            "story_classification_confidence": 0.0,
        }

    if normalized in STORY_CATEGORY_ALIASES:
        category = STORY_CATEGORY_ALIASES[normalized]
        return {
            "story_category": category,
            "story_position_score": STORY_POSITION_SCORES[category],
            "story_classification_confidence": 0.95,
        }

    for token, category in STORY_CATEGORY_ALIASES.items():
        if token in normalized:
            return {
                "story_category": category,
                "story_position_score": STORY_POSITION_SCORES[category],
                "story_classification_confidence": 0.7,
            }

    return {
        "story_category": "miscellaneous",
        "story_position_score": STORY_POSITION_SCORES["miscellaneous"],
        "story_classification_confidence": 0.35,
    }


def compute_transition_quality(prev_category: str, curr_category: str) -> float:
    if not prev_category or not curr_category:
        return 0.5

    prev_idx = STORY_SEQUENCE_INDEX.get(prev_category, STORY_SEQUENCE_INDEX["miscellaneous"])
    curr_idx = STORY_SEQUENCE_INDEX.get(curr_category, STORY_SEQUENCE_INDEX["miscellaneous"])
    diff = curr_idx - prev_idx

    if (prev_category, curr_category) in HARD_TRANSITION_PENALTIES:
        return 0.1
    if diff == 1:
        return 1.0
    if diff == 0:
        return 0.55
    if diff > 1:
        return max(0.35, 0.7 - (0.07 * (diff - 1)))
    return 0.2


def annotate_story_metadata(clips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    annotated = []
    for index, clip in enumerate(clips):
        row = dict(clip)
        classified = classify_story_scene(row.get("scene_type", ""))
        row.update(classified)

        if index == 0:
            row["transition_quality_score"] = 1.0
        else:
            prev_category = annotated[-1].get("story_category", "")
            row["transition_quality_score"] = compute_transition_quality(prev_category, row.get("story_category", ""))
        annotated.append(row)

    return annotated


def apply_story_ordering_v2(
    clips: List[Dict[str, Any]],
    min_story_confidence: float = 0.55,
    max_same_category_consecutive: int = 2,
) -> Dict[str, Any]:
    if not clips:
        return {"timeline": [], "applied": False, "fallback_used": False, "avg_confidence": 0.0}

    base = annotate_story_metadata(clips)
    avg_confidence = sum(c.get("story_classification_confidence", 0.0) for c in base) / len(base)

    if avg_confidence < min_story_confidence:
        logger.info(
            "[STORY V2] Confidence too low (%.2f < %.2f). Using existing timeline order.",
            avg_confidence,
            min_story_confidence,
        )
        return {
            "timeline": base,
            "applied": False,
            "fallback_used": True,
            "avg_confidence": round(avg_confidence, 4),
        }

    remaining = sorted(
        base,
        key=lambda c: (
            c.get("story_position_score", STORY_POSITION_SCORES["miscellaneous"]),
            -float(c.get("window_score", c.get("final_score", 50))),
        ),
    )
    ordered = []

    while remaining:
        if not ordered:
            ordered.append(remaining.pop(0))
            continue

        prev = ordered[-1]
        prev_category = prev.get("story_category", "miscellaneous")
        repeat_count = 0
        for existing in reversed(ordered):
            if existing.get("story_category") == prev_category:
                repeat_count += 1
            else:
                break

        best_idx = None
        best_score = -1.0
        for idx, candidate in enumerate(remaining):
            cat = candidate.get("story_category", "miscellaneous")
            if repeat_count >= max_same_category_consecutive and cat == prev_category:
                continue

            transition = compute_transition_quality(prev_category, cat)
            position_delta = abs(candidate.get("story_position_score", 75) - prev.get("story_position_score", 75))
            position_smoothness = clamp01(1.0 - (position_delta / 100.0))
            visual_quality = clamp01(float(candidate.get("window_score", candidate.get("final_score", 50))) / 100.0)
            candidate_score = (0.55 * transition) + (0.25 * position_smoothness) + (0.20 * visual_quality)

            if candidate_score > best_score:
                best_score = candidate_score
                best_idx = idx

        if best_idx is None:
            best_idx = 0
        ordered.append(remaining.pop(best_idx))

    ordered = annotate_story_metadata(ordered)
    low_quality_transitions = sum(1 for c in ordered[1:] if c.get("transition_quality_score", 1.0) < 0.35)

    return {
        "timeline": ordered,
        "applied": True,
        "fallback_used": False,
        "avg_confidence": round(avg_confidence, 4),
        "low_quality_transitions": low_quality_transitions,
    }


def apply_near_duplicate_penalty_v2(clips: List[Dict[str, Any]], penalty: float = 12.0) -> Tuple[List[Dict[str, Any]], int]:
    if len(clips) < 2:
        return clips, 0

    updated = []
    duplicates = 0

    for index, clip in enumerate(clips):
        row = dict(clip)
        row["near_duplicate_perspective"] = False

        if index > 0:
            prev = updated[-1]
            same_scene = normalize_scene_type(prev.get("scene_type", "")) == normalize_scene_type(row.get("scene_type", ""))
            same_direction = (prev.get("camera_direction", "") or "").lower() == (row.get("camera_direction", "") or "").lower()
            same_motion = (prev.get("camera_motion", "") or "").lower() == (row.get("camera_motion", "") or "").lower()
            same_shot = (prev.get("shot_size", "") or "").lower() == (row.get("shot_size", "") or "").lower()

            if same_scene and same_direction and same_motion and same_shot:
                row["near_duplicate_perspective"] = True
                row["final_score"] = max(0.0, float(row.get("final_score", 50.0)) - penalty)
                duplicates += 1

        updated.append(row)

    if duplicates:
        logger.info("[DEDUP V2] Applied near-duplicate penalties to %d clips.", duplicates)

    return updated, duplicates


def apply_scoring_v2(clips: List[Dict[str, Any]], weights: Dict[str, float]) -> List[Dict[str, Any]]:
    if not clips:
        return clips

    counts: Dict[str, int] = {}
    for clip in clips:
        category = clip.get("story_category", "miscellaneous")
        counts[category] = counts.get(category, 0) + 1

    w_stability = float(weights.get("stability_weight", 0.15))
    w_cinematic = float(weights.get("cinematic_weight", 0.15))
    w_story = float(weights.get("story_weight", 0.1))
    w_room = float(weights.get("room_uniqueness_weight", 0.05))
    w_transition = float(weights.get("transition_weight", 0.05))

    base_weight = max(0.5, 1.0 - (w_stability + w_cinematic + w_story + w_room + w_transition))

    scored = []
    for index, clip in enumerate(clips):
        row = dict(clip)
        category = row.get("story_category", "miscellaneous")
        stability = row.get("stability_score_v2")
        if stability is None:
            stability = clamp01(float(row.get("stability_score", 50.0)) / 100.0)
        else:
            stability = clamp01(float(stability))

        cinematic = clamp01(float(row.get("window_score", row.get("final_score", 50.0))) / 100.0)
        transition = 1.0 if index == 0 else clamp01(float(row.get("transition_quality_score", 0.6)))
        room_uniqueness = clamp01(1.0 / max(1, counts.get(category, 1)))
        story_component = clamp01(float(row.get("story_position_score", 75.0)) / 100.0)
        base_component = clamp01(float(row.get("final_score", 50.0)) / 100.0)

        final_score_v2 = (
            (base_component * base_weight)
            + (stability * w_stability)
            + (cinematic * w_cinematic)
            + (story_component * w_story)
            + (room_uniqueness * w_room)
            + (transition * w_transition)
        )

        row["cinematic_score"] = round(cinematic, 4)
        row["room_uniqueness_score"] = round(room_uniqueness, 4)
        row["transition_quality_score"] = round(transition, 4)
        row["final_score_v2"] = round(clamp01(final_score_v2) * 100.0, 2)
        row["v2_scoring_weights"] = {
            "base_weight": round(base_weight, 3),
            "stability_weight": w_stability,
            "cinematic_weight": w_cinematic,
            "story_weight": w_story,
            "room_uniqueness_weight": w_room,
            "transition_weight": w_transition,
        }
        scored.append(row)

    return scored


def analyze_stability_v2(filepath: str, start_sec: float, end_sec: float) -> Dict[str, Any]:
    result = deepcopy(DEFAULT_STABILITY_RESULT)

    try:
        cap = cv2.VideoCapture(filepath, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            logger.warning("[STABILITY V2] Unable to open file: %s", filepath)
            return result

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        if fps <= 0:
            fps = 30.0

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            return result

        start_frame = max(0, int(start_sec * fps))
        end_frame = int(end_sec * fps) if end_sec and end_sec > start_sec else min(total_frames - 1, start_frame + int(3 * fps))
        end_frame = min(total_frames - 1, end_frame)
        if end_frame - start_frame < 3:
            cap.release()
            return result

        segment_frames = end_frame - start_frame
        sample_step = max(1, segment_frames // 45)

        flow_means = []
        flow_variances = []
        translations = []
        rotations = []

        prev_gray = None
        prev_pts = None

        for frame_idx in range(start_frame, end_frame + 1, sample_step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            success, frame = cap.read()
            if not success:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if gray.shape[1] > 640:
                scale = 640.0 / gray.shape[1]
                gray = cv2.resize(gray, (640, max(1, int(gray.shape[0] * scale))), interpolation=cv2.INTER_AREA)

            if prev_gray is None:
                prev_gray = gray
                prev_pts = cv2.goodFeaturesToTrack(prev_gray, maxCorners=80, qualityLevel=0.3, minDistance=7, blockSize=7)
                continue

            if prev_pts is None or len(prev_pts) < 6:
                prev_pts = cv2.goodFeaturesToTrack(prev_gray, maxCorners=80, qualityLevel=0.3, minDistance=7, blockSize=7)
                prev_gray = gray
                continue

            next_pts, status, _ = cv2.calcOpticalFlowPyrLK(
                prev_gray,
                gray,
                prev_pts,
                None,
                winSize=(15, 15),
                maxLevel=2,
                criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03),
            )
            if next_pts is None or status is None:
                prev_gray = gray
                prev_pts = None
                continue

            good_new = next_pts[status.ravel() == 1]
            good_old = prev_pts[status.ravel() == 1]
            if len(good_new) < 6 or len(good_old) < 6:
                prev_gray = gray
                prev_pts = None
                continue

            flow_vectors = (good_new - good_old).reshape(-1, 2)
            magnitudes = np.sqrt((flow_vectors[:, 0] ** 2) + (flow_vectors[:, 1] ** 2))
            flow_means.append(float(np.mean(magnitudes)))
            flow_variances.append(float(np.var(magnitudes)))

            transform, _ = cv2.estimateAffinePartial2D(good_old.reshape(-1, 1, 2), good_new.reshape(-1, 1, 2))
            if transform is not None:
                tx, ty = float(transform[0, 2]), float(transform[1, 2])
                translations.append(math.sqrt((tx * tx) + (ty * ty)))
                angle = abs(math.degrees(math.atan2(transform[1, 0], transform[0, 0])))
                rotations.append(angle)

            prev_gray = gray
            prev_pts = good_new.reshape(-1, 1, 2)

        cap.release()

        if not flow_means:
            return result

        motion_variance = float(np.var(flow_means))
        flow_consistency = clamp01(1.0 - (float(np.mean(flow_variances)) / (float(np.mean(flow_variances)) + 25.0)))
        translation_jitter = float(np.std(translations)) if translations else 3.0
        rotation_jitter = float(np.std(rotations)) if rotations else 2.5
        translation_stability = clamp01(1.0 - (translation_jitter / (translation_jitter + 2.0)))
        rotation_stability = clamp01(1.0 - (rotation_jitter / (rotation_jitter + 1.8)))
        shake_raw = float(np.mean(flow_means))
        shake_score = clamp01(1.0 - (shake_raw / (shake_raw + 10.0)))
        variance_score = clamp01(1.0 - (motion_variance / (motion_variance + 12.0)))

        stability_score = (
            (0.30 * flow_consistency)
            + (0.25 * translation_stability)
            + (0.20 * rotation_stability)
            + (0.15 * shake_score)
            + (0.10 * variance_score)
        )
        confidence = clamp01(min(1.0, len(flow_means) / 12.0))

        return {
            "stability_score_v2": round(clamp01(stability_score), 4),
            "stability_confidence_v2": round(confidence, 4),
            "motion_variance": round(motion_variance, 4),
            "camera_shake_score": round(shake_score, 4),
            "optical_flow_consistency": round(flow_consistency, 4),
            "rotation_stability": round(rotation_stability, 4),
            "translation_stability": round(translation_stability, 4),
            "sample_pairs": len(flow_means),
        }
    except Exception as exc:
        logger.warning("[STABILITY V2] Analysis failed for %s: %s", filepath, exc)
        return result


def recommend_trim_bounds_v2(
    start_sec: float,
    end_sec: float,
    adjustment_result: Optional[Dict[str, Any]],
    stability_metrics: Optional[Dict[str, Any]],
    tail_stability_score: Optional[float] = None,
) -> Dict[str, Any]:
    rec_start = float(start_sec)
    rec_end = float(end_sec)
    reasons: List[str] = []
    confidence = 0.0

    if adjustment_result and adjustment_result.get("has_adjustment"):
        trim_start = float(adjustment_result.get("trim_start_sec", rec_start))
        if trim_start > rec_start:
            rec_start = min(trim_start, rec_start + 2.5)
            reasons.append(str(adjustment_result.get("adjustment_type", "camera_adjustment")))
            confidence += 0.55

    if stability_metrics:
        stability_score = float(stability_metrics.get("stability_score_v2", 0.5))
        if stability_score < 0.35:
            rec_start = max(rec_start, start_sec + 0.8)
            reasons.append("low_stability_start")
            confidence += 0.2

    if tail_stability_score is not None and tail_stability_score < 0.3:
        rec_end = max(rec_start + 1.2, rec_end - 0.8)
        reasons.append("unstable_tail")
        confidence += 0.2

    fallback_to_original = False
    if (rec_end - rec_start) < 1.2:
        rec_start = float(start_sec)
        rec_end = float(end_sec)
        fallback_to_original = True
        reasons = ["low_trim_confidence_fallback"]
        confidence = 0.0

    return {
        "stable_start_time": round(rec_start, 3),
        "stable_end_time": round(rec_end, 3),
        "recommended_trim_start": round(rec_start, 3),
        "recommended_trim_end": round(rec_end, 3),
        "trim_confidence": round(clamp01(confidence), 4),
        "trim_reason_codes": reasons,
        "fallback_to_original": fallback_to_original,
    }

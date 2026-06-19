import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from services.quality_v2 import (
    apply_near_duplicate_penalty_v2,
    apply_scoring_v2,
    apply_story_ordering_v2,
    classify_story_scene,
    compute_transition_quality,
    recommend_trim_bounds_v2,
)


def test_classify_story_scene_exact_match():
    result = classify_story_scene("living_room")
    assert result["story_category"] == "living_room"
    assert result["story_position_score"] == 30
    assert result["story_classification_confidence"] >= 0.9


def test_classify_story_scene_unknown_fallback():
    result = classify_story_scene("ceiling_corner")
    assert result["story_category"] == "miscellaneous"
    assert result["story_position_score"] == 75
    assert result["story_classification_confidence"] < 0.5


def test_transition_quality_prefers_forward_flow():
    good = compute_transition_quality("living_room", "kitchen")
    bad = compute_transition_quality("bathroom", "exterior_drone")
    assert good > bad
    assert bad <= 0.2


def test_story_ordering_v2_reorders_with_confidence():
    clips = [
        {"clip_id": "b", "scene_type": "kitchen", "final_score": 80, "window_score": 82},
        {"clip_id": "a", "scene_type": "drone", "final_score": 78, "window_score": 79},
        {"clip_id": "c", "scene_type": "bedroom", "final_score": 77, "window_score": 77},
    ]
    result = apply_story_ordering_v2(clips, min_story_confidence=0.5)
    ordered = result["timeline"]
    assert result["applied"] is True
    assert ordered[0]["story_category"] == "exterior_drone"
    assert ordered[-1]["story_category"] in {"bedroom", "exit_shot", "miscellaneous"}


def test_story_ordering_v2_fallback_when_confidence_low():
    clips = [
        {"clip_id": "x", "scene_type": "foo_space", "final_score": 80},
        {"clip_id": "y", "scene_type": "bar_space", "final_score": 75},
    ]
    result = apply_story_ordering_v2(clips, min_story_confidence=0.7)
    assert result["applied"] is False
    assert result["fallback_used"] is True


def test_near_duplicate_penalty_marks_and_penalizes():
    clips = [
        {
            "clip_id": "1",
            "scene_type": "drone",
            "camera_direction": "left_to_right",
            "camera_motion": "pan",
            "shot_size": "wide",
            "final_score": 80,
        },
        {
            "clip_id": "2",
            "scene_type": "drone",
            "camera_direction": "left_to_right",
            "camera_motion": "pan",
            "shot_size": "wide",
            "final_score": 78,
        },
    ]
    updated, duplicates = apply_near_duplicate_penalty_v2(clips, penalty=10)
    assert duplicates == 1
    assert updated[1]["near_duplicate_perspective"] is True
    assert updated[1]["final_score"] == 68


def test_scoring_v2_adds_final_score_fields():
    clips = [
        {
            "clip_id": "1",
            "scene_type": "drone",
            "story_category": "exterior_drone",
            "story_position_score": 10,
            "transition_quality_score": 1.0,
            "stability_score_v2": 0.9,
            "window_score": 85,
            "final_score": 82,
        },
        {
            "clip_id": "2",
            "scene_type": "kitchen",
            "story_category": "kitchen",
            "story_position_score": 40,
            "transition_quality_score": 0.8,
            "stability_score_v2": 0.8,
            "window_score": 80,
            "final_score": 79,
        },
    ]
    scored = apply_scoring_v2(
        clips,
        {
            "stability_weight": 0.15,
            "cinematic_weight": 0.15,
            "story_weight": 0.1,
            "room_uniqueness_weight": 0.05,
            "transition_weight": 0.05,
        },
    )
    assert "final_score_v2" in scored[0]
    assert "room_uniqueness_score" in scored[1]
    assert scored[0]["final_score_v2"] > 0


def test_trim_recommendation_uses_adjustment_signal():
    trim = recommend_trim_bounds_v2(
        start_sec=0.0,
        end_sec=6.0,
        adjustment_result={"has_adjustment": True, "trim_start_sec": 1.2, "adjustment_type": "gimbal_init"},
        stability_metrics={"stability_score_v2": 0.5},
        tail_stability_score=0.7,
    )
    assert trim["recommended_trim_start"] >= 1.0
    assert trim["fallback_to_original"] is False

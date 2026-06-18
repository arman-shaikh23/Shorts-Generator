import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.timeline_optimizer import (
    calculate_window_score,
    build_highlight_memory,
    _apply_repetition_penalty,
    _apply_motion_diversity,
    _get_arc_phase,
    _get_walkthrough_index,
    _get_continuity_score,
    _is_strict_walkthrough,
    _get_style_profile,
    parse_time,
    RECENT_SCENE_MEMORY,
    REPETITION_PENALTY,
    MOTION_DIVERSITY_PENALTY,
)


# ═══════════════════════════════════════════════════════════════
#  UNIT TESTS: V4.0 Window Score Formula
# ═══════════════════════════════════════════════════════════════

class TestWindowScore:
    def test_perfect_scores(self):
        clip = {"luxury_score": 100, "reveal_score": 100, "composition_score": 100,
                "motion_quality_score": 100, "lifestyle_score": 100}
        score = calculate_window_score(clip)
        assert score == 100.0

    def test_zero_scores(self):
        clip = {"luxury_score": 0, "reveal_score": 0, "composition_score": 0,
                "motion_quality_score": 0, "lifestyle_score": 0}
        score = calculate_window_score(clip)
        assert score == 0.0

    def test_mixed_scores(self):
        clip = {"luxury_score": 80, "reveal_score": 60, "composition_score": 70,
                "motion_quality_score": 50, "lifestyle_score": 90}
        score = calculate_window_score(clip)
        expected = (0.30 * 80) + (0.25 * 60) + (0.20 * 70) + (0.15 * 50) + (0.10 * 90)
        assert abs(score - expected) < 0.01

    def test_fallback_to_hook_score(self):
        """reveal_score falls back to hook_score if missing"""
        clip = {"luxury_score": 50, "hook_score": 80, "composition_score": 50,
                "stability_score": 50, "lifestyle_score": 50}
        score = calculate_window_score(clip)
        # reveal uses hook_score=80, motion uses stability_score=50
        expected = (0.30 * 50) + (0.25 * 80) + (0.20 * 50) + (0.15 * 50) + (0.10 * 50)
        assert abs(score - expected) < 0.01


# ═══════════════════════════════════════════════════════════════
#  UNIT TESTS: Property Highlight Memory
# ═══════════════════════════════════════════════════════════════

class TestHighlightMemory:
    def test_empty_clips(self):
        memory = build_highlight_memory([])
        assert memory["hero_pool"] is None
        assert memory["hero_exterior"] is None
        assert memory["hero_view"] is None
        assert memory["hero_living_room"] is None

    def test_identifies_hero_pool(self):
        clips = [
            {"scene_type": "pool", "clip_id": "0_5_12", "video_index": 0, "start": "5",
             "luxury_score": 95, "reveal_score": 90, "composition_score": 88,
             "motion_quality_score": 85, "lifestyle_score": 92},
            {"scene_type": "kitchen", "clip_id": "1_0_7", "video_index": 1, "start": "0",
             "luxury_score": 70, "composition_score": 65}
        ]
        memory = build_highlight_memory(clips)
        assert memory["hero_pool"] is not None
        assert memory["hero_pool"]["clip_id"] == "0_5_12"

    def test_identifies_hero_exterior(self):
        clips = [
            {"scene_type": "exterior", "clip_id": "3_0_8", "video_index": 3, "start": "0",
             "luxury_score": 90, "reveal_score": 85, "composition_score": 92,
             "motion_quality_score": 80, "lifestyle_score": 88}
        ]
        memory = build_highlight_memory(clips)
        assert memory["hero_exterior"] is not None
        assert memory["hero_exterior"]["clip_id"] == "3_0_8"

    def test_picks_highest_scoring(self):
        clips = [
            {"scene_type": "drone", "clip_id": "a", "video_index": 0, "start": "0",
             "luxury_score": 60, "composition_score": 60},
            {"scene_type": "aerial", "clip_id": "b", "video_index": 1, "start": "0",
             "luxury_score": 95, "reveal_score": 95, "composition_score": 95,
             "motion_quality_score": 95, "lifestyle_score": 95}
        ]
        memory = build_highlight_memory(clips)
        assert memory["hero_exterior"]["clip_id"] == "b"


# ═══════════════════════════════════════════════════════════════
#  UNIT TESTS: Repetition Memory
# ═══════════════════════════════════════════════════════════════

class TestRepetitionMemory:
    def test_no_repetition(self):
        timeline = [
            {"scene_type": "exterior", "final_score": 80, "clip_id": "a"},
            {"scene_type": "lobby", "final_score": 75, "clip_id": "b"},
            {"scene_type": "living_room", "final_score": 85, "clip_id": "c"},
        ]
        result = _apply_repetition_penalty(timeline)
        # No penalties should be applied
        assert result[0]["final_score"] == 80
        assert result[1]["final_score"] == 75
        assert result[2]["final_score"] == 85

    def test_penalizes_repetition(self):
        timeline = [
            {"scene_type": "exterior", "final_score": 80, "clip_id": "a"},
            {"scene_type": "lobby", "final_score": 75, "clip_id": "b"},
            {"scene_type": "exterior", "final_score": 70, "clip_id": "c"},  # Repeated!
        ]
        result = _apply_repetition_penalty(timeline)
        assert result[2]["final_score"] == 70 - REPETITION_PENALTY

    def test_no_penalty_beyond_memory_window(self):
        timeline = [
            {"scene_type": "exterior", "final_score": 80, "clip_id": "0"},
            {"scene_type": "lobby", "final_score": 75, "clip_id": "1"},
            {"scene_type": "living_room", "final_score": 85, "clip_id": "2"},
            {"scene_type": "kitchen", "final_score": 70, "clip_id": "3"},
            {"scene_type": "dining", "final_score": 65, "clip_id": "4"},
            {"scene_type": "bedroom", "final_score": 60, "clip_id": "5"},
            {"scene_type": "exterior", "final_score": 78, "clip_id": "6"},  # 6 positions after first
        ]
        result = _apply_repetition_penalty(timeline)
        # exterior at index 6 is beyond the 5-clip lookback from index 0
        assert result[6]["final_score"] == 78  # No penalty


# ═══════════════════════════════════════════════════════════════
#  UNIT TESTS: Motion Diversity
# ═══════════════════════════════════════════════════════════════

class TestMotionDiversity:
    def test_no_penalty_when_diverse(self):
        timeline = [
            {"camera_motion": "push_in", "final_score": 80, "clip_id": "a"},
            {"camera_motion": "pan", "final_score": 75, "clip_id": "b"},
            {"camera_motion": "static", "final_score": 70, "clip_id": "c"},
        ]
        result = _apply_motion_diversity(timeline)
        assert result[2]["final_score"] == 70

    def test_penalizes_3_consecutive_same_motion(self):
        timeline = [
            {"camera_motion": "static", "camera_direction": "neutral", "shot_size": "wide",
             "final_score": 80, "clip_id": "a"},
            {"camera_motion": "static", "camera_direction": "neutral", "shot_size": "wide",
             "final_score": 75, "clip_id": "b"},
            {"camera_motion": "static", "camera_direction": "neutral", "shot_size": "wide",
             "final_score": 70, "clip_id": "c"},
        ]
        result = _apply_motion_diversity(timeline)
        # All 3 fields are identical for 3 consecutive clips → 3 penalties on clip c
        assert result[2]["final_score"] < 70


# ═══════════════════════════════════════════════════════════════
#  UNIT TESTS: Story Arc Phase Assignment
# ═══════════════════════════════════════════════════════════════

class TestStoryArc:
    def test_drone_goes_to_hook(self):
        assert _get_arc_phase("drone") == "HOOK"

    def test_exterior_goes_to_hook(self):
        assert _get_arc_phase("exterior") == "HOOK"

    def test_living_room_goes_to_discovery(self):
        assert _get_arc_phase("living_room") == "DISCOVERY"

    def test_kitchen_goes_to_showcase(self):
        assert _get_arc_phase("kitchen") == "SHOWCASE"

    def test_pool_goes_to_showcase(self):
        assert _get_arc_phase("pool") == "SHOWCASE"

    def test_closing_drone_goes_to_resolution(self):
        assert _get_arc_phase("closing drone") == "RESOLUTION"

    def test_high_hero_score_promotes_to_hook(self):
        """Clips with hero_score >= 95 in DISCOVERY/SHOWCASE get promoted to HOOK"""
        assert _get_arc_phase("living_room", hero_score=95) == "HOOK"
        assert _get_arc_phase("pool", hero_score=95) == "HOOK"

    def test_normal_hero_score_stays_in_place(self):
        assert _get_arc_phase("living_room", hero_score=80) == "DISCOVERY"
        assert _get_arc_phase("pool", hero_score=80) == "SHOWCASE"


# ═══════════════════════════════════════════════════════════════
#  UNIT TESTS: Style Profiles
# ═══════════════════════════════════════════════════════════════

class TestStyleProfiles:
    def test_luxury_is_strict(self):
        assert _is_strict_walkthrough("Luxury")
        assert _is_strict_walkthrough("Realtor Style")
        assert _is_strict_walkthrough("Cinematic")

    def test_viral_is_flexible(self):
        assert not _is_strict_walkthrough("Instagram Viral")
        assert not _is_strict_walkthrough("TikTok")

    def test_luxury_tour_profile(self):
        profile = _get_style_profile("Luxury")
        assert profile["target_asset_preservation"] == 1.0
        assert profile["strict_walkthrough"] is True

    def test_instagram_profile(self):
        profile = _get_style_profile("Instagram Viral")
        assert profile["target_asset_preservation"] == 0.75
        assert profile["strict_walkthrough"] is False


# ═══════════════════════════════════════════════════════════════
#  UNIT TESTS: Adjacency Scoring
# ═══════════════════════════════════════════════════════════════

class TestAdjacencyScoring:
    def test_natural_transition_bonus(self):
        score = _get_continuity_score("living_room", "dining")
        assert score == 25

    def test_jarring_jump_penalty(self):
        score = _get_continuity_score("bathroom", "kitchen")
        assert score == -50

    def test_no_defined_transition(self):
        score = _get_continuity_score("pool", "gym")
        assert score == 0

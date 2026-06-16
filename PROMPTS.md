# Prompts Documentation

## Prompt 1: ReelForge Duration-First Story Engine (v5)

### The Prompt
```text
Property: '{property_name}'
Total Uploaded Clips: {clip_count} (indices 0 to {clip_count - 1})

═══ 1. DURATION-FIRST GENERATION & BUDGET ALGORITHM ═══
DO NOT select clips first.
Instead, use: {dynamic_duration}
Add unique clips until the duration budget is reached.
Extract 3-5 seconds from the high-quality portions of each clip.
Example: Clip A (4 sec) + Clip B (3 sec) + Clip C (5 sec). Continue until target duration is achieved.

[Platform Rules injected here (Shorts Hook/Main/Closing OR YouTube Hook/Main/Closing)]

═══ 2. PROPERTY STORY ENGINE ═══
Create a logical property walkthrough.
Priority order: Drone -> Exterior -> Entrance -> Lobby -> Living Room -> Dining -> Kitchen -> Bedroom -> Bathroom -> Balcony -> Pool -> Gym -> Garden -> Parking -> Closing Drone.
THIS ORDER SHOULD OVERRIDE CLIP SCORE.
Bathroom, Parking, or Utility areas should NEVER be the opening shot.

═══ 3. OPENING SHOT ENGINE ═══
Opening shot candidates: Drone, Exterior, Pool, Luxury Living Room.
Select the strongest visual. Opening duration: 5–7 sec. Goal: Immediately impress the viewer.

═══ 4. COVERAGE-FIRST SELECTION ═══
Use maximum unique footage. Goal: 80–95% coverage.
Only remove: Exact duplicates, Near duplicates >95%

═══ 5. CATEGORY COVERAGE RULE ═══
Ensure representation of all major categories. Never allow one category to dominate.

═══ 6. STORYBOARD VALIDATOR ═══
Before outputting, verify:
✓ Strong opening shot (Not a bathroom/parking)
✓ Correct chronological property order
✓ No repeated footage / No duplicate clips
✓ Duration within target budget
✓ Coverage requirements met
If validation fails, silently rebuild the storyboard before responding.
```

### Key Changes from v4 → v5

| Aspect | v4 | v5 (Duration-First Engine) |
|---|---|---|
| Sequence Logic | Strict 5-Stage | **Strict 15-Stage Chronological Priority (Overrides visual score)** |
| Selection Method | Pick 80% clips, then calculate time | **Set Target Budget (e.g. 60s), then add clips until filled** |
| Platform Pacing | None | **Strict Timeline Structures (e.g. Shorts: 0-5s Hook, 5-20s Main, etc)** |
| Shorts Cap | 12 clips maximum | **Absolute 60s hard limit via Budget summation** |
| YouTube Floor | N/A | **Minimum 60s, scales intelligently up to 240s based on raw footage** |

### Reasoning Behind Each Decision

- **Duration-First Focus**: Users complained Shorts were sometimes running over 60s or YouTube videos were rendering at just 30s. Instructing the AI to view selection as a "Duration Budget" perfectly aligns its output with the target platform's required pacing.
- **Score Override**: The AI used to favor 98-score Bathroom clips over 80-score Drone clips for the opening shot. The prompt explicitly forces Sequence logic to override raw Quality Score logic.
- **Dynamic Duration**: Instead of forcing all reels into 30 seconds, we scale: 5 clips → 20-40s, 30 clips → 90-180s. This respects the user's footage volume.
- **clip_duration_sec**: Each clip gets 3-6 seconds of screen time based on quality, replacing the old 1-second-per-clip approach.
- **Property Tour Sequencing**: 18-category ordering ensures logical flow: Drone → Exterior → Entrance → rooms → amenities → closing.
- **Coverage Protection**: The AI is instructed to never remove the only clip representing a category (e.g., the only Gym shot).
- **Post-Processing Validation**: After Gemini returns, the backend recalculates coverage percentage and logs a warning if it drops below 70%.

## Prompt 2: ReelForge Story Engine (v6) - Diversity & Roles

### The Prompt
```text
Property: '{property_name}'
Total Uploaded Clips: {clip_count} (indices 0 to {clip_count - 1})

═══ 1. DURATION-FIRST GENERATION & BUDGET ALGORITHM ═══
DO NOT select clips first. Instead, use: {dynamic_duration}
Add unique clips until the duration budget is reached.
Extract 3-5 seconds from the high-quality portions of each clip.

[Platform Rules injected here]

═══ 2. SCENE ROLE CLASSIFICATION & STORY BUILDER ═══
Assign every selected clip a structural ROLE:
OPENING, PROPERTY_SIGN, EXTERIOR, LOBBY, LIVING_ROOM, DINING, KITCHEN, BEDROOM, BATHROOM, AMENITY, POOL, GYM, PARKING, CLOSING.

Build the reel strictly using this Role order:
OPENING -> PROPERTY_SIGN -> LOBBY -> LIVING_ROOM -> DINING -> KITCHEN -> BEDROOM -> BATHROOM -> AMENITIES -> POOL -> GYM -> CLOSING
THIS ORDER MUST OVERRIDE CLIP SCORE.

═══ 3. OPENING SCENE RULES ═══
Opening candidates: Drone, Exterior, Luxury Living Area.
NEVER use: Bathroom, Parking, Utility Room.
Opening duration: 5–7 seconds.

═══ 4. CLOSING SCENE & DIVERSITY RULES ═══
Closing candidates: Exterior, Pool, Night View, Drone Exit.
NEVER reuse the opening scene.
RULE: opening_scene_id != closing_scene_id (The opening video_index MUST NOT match the closing video_index).
If opening uses Video A, you MUST use Video B for the closing. Avoid using the same source clip twice.

═══ 5. REUSE PROTECTION ═══
Track scene_id and video_id internally.
PREVENT the same temporal segment of a video from appearing twice. Use maximum unique footage.
Only remove: Exact duplicates, Near duplicates >95%.

═══ 6. CATEGORY COVERAGE RULE ═══
Never allow one category to dominate the reel.

═══ 7. STORYBOARD VALIDATOR ═══
Before outputting, verify:
✓ Strong opening (Not bathroom/parking)
✓ Logical walkthrough order based on Roles
✓ No repeated opening shot
✓ No repeated closing shot (Opening video_index != Closing video_index)
✓ Amenities appear near the end
✓ Smooth category transitions
If validation fails, silently rebuild the storyboard before responding.
```

### Key Changes from v5 → v6

| Aspect | v5 | v6 (Diversity & Roles) |
|---|---|---|
| Classification | General scene types | **Strict Structural Roles (OPENING, CLOSING, LOBBY)** |
| Sequence Logic | Loose 15-stage | **Strict Role-based 12-stage builder** |
| Closing Shot | Static | **opening_scene_id != closing_scene_id (Forced diversity)** |
| Reuse Protection | Implicit | **Explicit Tracking of scene_id and video_id** |

### Reasoning Behind Each Decision

- **opening_scene_id != closing_scene_id**: Users noticed reels occasionally started and ended with the exact same clip, which ruined the pacing. This explicit constraint forces Gemini to pick different video sources for the start and end.
- **Scene Role Classification**: Instead of just tagging a clip as "Pool", tagging it as "CLOSING" explicitly commands the LLM to place it at the end of the timeline sequence, solving the random ordering issue.

## Prompt 3: Variation Generation (Updated)

### The Prompt
```text
Property: '{property_name}'
Goal: Generate 3 distinct Reel Variations using the Pool of Scenes.
- Luxury: Use as many clips as possible, slower paced
- Instagram Viral: Fast-paced, aggressive quick-cuts allowed
- Realtor Style: Traditional walkthrough, use nearly all clips
```

### Reasoning
- The Luxury and Realtor variations now explicitly keep most clips, maintaining high coverage. Only the Viral style allows dropping clips for fast pacing.

## Prompt 4: ReelForge Story Engine (v7) - Unlimited Duration & Loop Closure

### The Prompt
```text
Property: '{property_name}'
Total Uploaded Clips: {clip_count} (indices 0 to {clip_count - 1})

═══ 1. MAXIMUM COVERAGE (CRITICAL) ═══
DO NOT stop selecting clips to fit a time budget. Use: TARGET DURATION: UNLIMITED. Use ALL unique, non-duplicate clips. The final video will be exactly as long as necessary to show every important clip.
You MUST select ALL unique, non-duplicate clips provided in the pool.
EACH CLIP must have clip_duration_sec between 8-15 seconds.
Your total_selected_duration_sec MUST equal the sum of all clip_duration_sec for every unique clip in the pool.

[Platform Rules injected here]

═══ 8. STORYBOARD VALIDATOR (RUN BEFORE OUTPUT) ═══
Verify EACH of these or silently rebuild:
✓ Strong opening (scene_type is drone/aerial/exterior/living_room/pool, NOT bathroom/parking)
✓ Logical walkthrough order based on Roles (not visual score)
✓ No repeated footage / No duplicate clips
✓ Uses ALL unique non-duplicate clips available
✓ Opening video_index != Closing video_index
✓ Amenities appear near the end
✓ Smooth category transitions (don't jump from kitchen back to exterior)
If ANY validation fails, silently rebuild the storyboard before responding.
```

### Key Changes from v6 → v7

| Aspect | v6 (Roles) | v7 (Unlimited Duration) |
|---|---|---|
| Target Duration | Strict budget (e.g. 60s hard cap) | **UNLIMITED. Forced to use all unique clips.** |
| Clip Usage | Drop clips to hit target time | **DO NOT drop clips. Output is as long as necessary.** |
| Loop Closure (Backend) | None | **FFmpeg appends 2s snippet of the opening clip to the end of the video.** |

# Prompts Documentation

## Prompt 1: Coverage-First Video Analysis & Content Generation (v3)

### The Prompt
```text
Property: '{property_name}'
Total Uploaded Clips: {clip_count} (indices 0 to {clip_count - 1})

═══ YOUR #1 PRIORITY: MAXIMIZE FOOTAGE COVERAGE ═══

You are a professional real estate video editor. Your job is to create a
COMPLETE property tour that uses NEARLY ALL uploaded footage.

COVERAGE TARGET: Use 80-95% of all clips.

═══ DUPLICATE REMOVAL RULES (VERY STRICT) ═══

ONLY remove a clip if ALL of the following are true:
1. It shows the EXACT same scene as another clip
2. It has the EXACT same camera angle (within 10 degrees)
3. Visual similarity is above 95%

NEVER remove a clip just because:
- It shows the same room from a different angle
- It has slightly different lighting
- It's a different take of the same space

═══ SCENE CATEGORIZATION ═══
Drone, Aerial, Exterior, Entrance, Lobby, Living Room, Kitchen, Dining,
Bedroom, Bathroom, Balcony, Pool, Gym, Parking, Garden, Amenities,
Closing Drone, Other

═══ COVERAGE PROTECTION ═══
Never remove the last/only clip of any category.

═══ PROPERTY TOUR SEQUENCING ═══
Opening → Walkthrough → Amenities → Closing

═══ SCENE DIVERSITY ═══
Never place >2 clips of same type consecutively.

═══ DYNAMIC CLIP DURATION ═══
Quality 90-100: 5-6s | Quality 70-89: 4-5s | Below 70: 3-4s
```

### Key Changes from v1 → v2 → v3

| Aspect | v1 (Original) | v2 (Performance) | v3 (Coverage-First) |
|---|---|---|---|
| Selection Philosophy | Best moments only | Best moments only | USE EVERYTHING |
| Coverage Target | Not specified | Not specified | 80-95% |
| Duplicate Rules | Not defined | Confidence > 85 | Strict: >95% sim + same angle + same scene |
| Clip Duration | Raw timestamps | Raw timestamps | Dynamic 3-6s per clip |
| Reel Duration | Fixed (30s/45s) | Fixed | Dynamic (20s-4min based on clip count) |
| Scene Categories | None | 6 categories | 18 categories (full property tour) |
| Coverage Protection | None | Basic | Never remove last-of-category |
| Diversity Enforcement | None | Basic | Max 2 consecutive same-type |
| Analytics | None | Basic | Full: uploaded/removed/selected/coverage% |

### Reasoning Behind Each Decision

- **Coverage-First Mandate**: Users who upload 29 clips expect to see nearly all of them. Dropping to 8-10 creates frustration. The prompt now explicitly mandates 80-95% inclusion.
- **Strict Duplicate Rules**: The previous prompt let the AI interpret "similar" loosely. Now duplicates require triple-match: same scene + same angle + >95% similarity. Different angles of the same room are preserved.
- **Dynamic Duration**: Instead of forcing all reels into 30 seconds, we scale: 5 clips → 20-40s, 30 clips → 90-180s. This respects the user's footage volume.
- **clip_duration_sec**: Each clip gets 3-6 seconds of screen time based on quality, replacing the old 1-second-per-clip approach.
- **Property Tour Sequencing**: 18-category ordering ensures logical flow: Drone → Exterior → Entrance → rooms → amenities → closing.
- **Coverage Protection**: The AI is instructed to never remove the only clip representing a category (e.g., the only Gym shot).
- **Post-Processing Validation**: After Gemini returns, the backend recalculates coverage percentage and logs a warning if it drops below 70%.

## Prompt 2: Variation Generation (Updated)

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

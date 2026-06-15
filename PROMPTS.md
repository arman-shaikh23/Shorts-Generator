# Prompts Documentation

## Prompt 1: ReelForge Story Engine & Coverage-First Analysis (v4)

### The Prompt
```text
Property: '{property_name}'
Total Uploaded Clips: {clip_count} (indices 0 to {clip_count - 1})

═══ YOUR #1 PRIORITY: MAXIMIZE FOOTAGE COVERAGE ═══

You are a professional real estate video editor. Your job is to create a COMPLETE property tour that uses NEARLY ALL uploaded footage.

COVERAGE TARGET:
[If Shorts Mode (<= 60s)]: Try to use many clips, BUT THIS IS SHORTS MODE. CRITICAL DURATION LIMIT: You MUST NOT select more than 12 clips total, even if it means missing the 80% coverage target. The total duration must remain under 60 seconds.
[If YouTube Mode]: Use 80-95% of all clips. Use at least one segment from every unique uploaded clip whenever possible. If {clip_count} clips are uploaded, you should select at least {max(1, int(clip_count * 0.85))} clips.

═══ DUPLICATE REMOVAL RULES (VERY STRICT) ═══

ONLY remove a clip if ALL of the following are true:
1. It shows the EXACT same scene as another clip
2. It has the EXACT same camera angle (within 10 degrees)  
3. Visual similarity is above 95%

═══ OPENING SHOT SELECTION ═══
Choose the strongest opening shot from: Drone, Exterior, or Best Luxury Scene.
AVOID using Parking, Bathroom, or Storage Area as the opening shot under any circumstances (unless no other clips exist).

═══ PROPERTY TOUR STORY ENGINE ═══
Do NOT use the raw upload order. Do NOT use score-only ordering.
Preferred sequence:
1. OPENING: Drone, Exterior, Entrance
2. MAIN TOUR: Lobby, Living Room, Dining, Kitchen
3. PRIVATE AREAS: Bedroom, Bathroom, Balcony
4. AMENITIES: Pool, Gym, Garden, Clubhouse
5. FINAL SECTION: Parking, Exterior, Closing Drone

Parking should NEVER be used as the opening shot. Place it near the end.

═══ DYNAMIC CLIP DURATION ═══
Extract 3-5 seconds from the high-quality portions of each clip.
- Quality score 90-100: 4-5 seconds
- Quality score below 90: 3-4 seconds

Target total reel duration: {dynamic_duration} (scales intelligently based on {clip_count} unique clips and the requested format).
```

### Key Changes from v3 → v4

| Aspect | v3 | v4 (ReelForge Engine) |
|---|---|---|
| Sequence Logic | Loose (Opening → Walkthrough → Closing) | **Strict 5-Stage Property Tour** |
| Opening Shot | Not restricted | **Must be Drone/Exterior/Luxury. No Parking/Bathrooms** |
| Minimum Usage | Target 80-95% | **Must use at least 1 segment from EVERY unique clip** |
| Clip Duration | 3-6s | **Tighter 3-5s extractions** |
| Output Duration | Static scaling | **Platform-Aware Scaling** (Shorts mode: up to 60s max. YouTube mode: up to 120s max) |

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

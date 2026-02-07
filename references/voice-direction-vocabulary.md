# Voice Direction Vocabulary

Professional terminology for TTS prompting and voice direction. These terms translate well to Qwen3-TTS natural language descriptions.

## Tonal Adjustments

| Term | Meaning | TTS Application |
|------|---------|-----------------|
| **Warmer** | Add friendliness, approachability | "with warmth in the voice" |
| **Brighter** | More energy, higher frequencies | "bright and energetic" |
| **Darker** | Heavier, more serious | "darker, more serious tone" |
| **More intimate** | Closer, softer, personal | "intimate, as if speaking to one person" |
| **Find the smile** | Inject warmth without changing words | "with a natural smile in the voice" |
| **Cooler** | More distant, professional | "cool and professional" |
| **More authoritative** | Command presence | "commanding, authoritative" |
| **More vulnerable** | Let weakness show | "vulnerable, exposed" |

## Pacing Controls

| Term | Meaning | TTS Application |
|------|---------|-----------------|
| **Pick up the pace** | Faster overall | "quicker pace" |
| **Land on it** | Give weight to specific words | "emphasize [word]" |
| **Throw it away** | De-emphasize, casual delivery | "casual, de-emphasized" |
| **Button it** | Clean, definitive ending | "decisive ending" |
| **Three in a row** | Read multiple takes with variations | Generate multiple outputs |
| **Let it breathe** | Longer pauses, more space | "with pauses, unhurried" |
| **Drive through** | Don't pause, maintain momentum | "continuous, driving energy" |
| **Sit on it** | Extended pause before | "pause before [word]" |

## Volume and Projection

| Term | Meaning | TTS Application |
|------|---------|-----------------|
| **Project** | Louder, fuller voice | "louder, projecting" |
| **Pull back** | Quieter, more intimate | "quieter, pulled back" |
| **Stage whisper** | Loud whisper (audible, not soft) | "stage whisper, hushed but clear" |
| **Under** | Speak beneath the energy | "understated, held back" |
| **Over the top** | Exaggerated, theatrical | "theatrical, exaggerated" |

## Emotional Intensity Scales

Use these to specify emotional gradation in TTS prompts.

### Positive Emotions
```
Neutral → Content → Pleased → Happy → Joyful → Ecstatic → Manic
```

### Anger
```
Calm → Annoyed → Irritated → Frustrated → Angry → Furious → Enraged
```

### Fear
```
Composed → Concerned → Worried → Anxious → Fearful → Terrified → Panicked
```

### Sadness
```
Neutral → Wistful → Melancholic → Sad → Grieving → Despairing → Devastated
```

### Surprise
```
Neutral → Curious → Surprised → Shocked → Stunned → Disbelieving
```

## Character Voice Variables

Five primary axes for differentiating character voices:

| Variable | Low Setting | High Setting |
|----------|-------------|--------------|
| **Pitch** | Authority, maturity, menace | Youth, excitement, nervousness |
| **Pace** | Thoughtfulness, menace, gravity | Urgency, nervousness, excitement |
| **Volume** | Intimacy, vulnerability, secrecy | Authority, anger, confidence |
| **Resonance** | Weakness, illness, fragility | Power, strength, command |
| **Texture** | Sophistication (smooth) | Toughness (gravelly, rough) |

### Example Character Differentiations

| Character Type | Pitch | Pace | Volume | Resonance | Texture |
|----------------|-------|------|--------|-----------|---------|
| Wise mentor | Low | Slow | Medium | High | Smooth |
| Nervous sidekick | High | Fast | Medium | Low | Breathy |
| Villain | Low | Measured | Medium-loud | High | Smooth |
| Child | High | Variable | Medium | Low | Clear |
| Warrior | Medium | Medium | Loud | High | Rough |
| Scholar | Medium | Slow | Quiet | Medium | Smooth |

## Accent and Regional Markers

When specifying accents, layer with other attributes:

**Format**: "[Accent descriptor], [additional qualities]"

### Western

| Accent | Key Markers | TTS Prompt |
|--------|-------------|------------|
| Scottish | Rolled R's, clipped vowels | "Thick Scottish accent, weathered and gravelly" |
| Southern US | Drawl, diphthong elongation | "Slight Southern drawl, warm and unhurried" |
| British RP | Crisp consonants, non-rhotic | "Crisp British RP, cool and precise" |
| Brooklyn/NY | Dropped R's, fast cadence | "Brooklyn accent, fast and streetwise" |
| Irish | Lilting rhythm, soft T's | "Soft Irish lilt, gentle and musical" |
| Maine/New England | Non-rhotic, flat A's, clipped | "Maine accent, understated, dry, unhurried" |
| Midwest US | Flat vowels, even pace, plain | "Ohio Midwest, plain-spoken, no performance" |

### Caribbean and Diaspora

| Accent | Key Markers | TTS Prompt |
|--------|-------------|------------|
| Trinidadian English | Melodic intonation, rising sentence ends, rhythmic | "Trinidadian English, musical cadence, warm and rhythmic" |
| Jamaican English | Syncopated rhythm, clipped consonants | "Jamaican English, rhythmic pacing, confident" |
| Caribbean diaspora (US/UK) | Code-switching, accent surfaces under emotion | "American English with Caribbean warmth underneath, accent breaks through in emotional moments" |

### South Asian

| Accent | Key Markers | TTS Prompt |
|--------|-------------|------------|
| Indian English | Retroflex consonants, syllable-timed rhythm | "Indian English, precise diction, syllable-timed rhythm" |
| Indian English (diaspora) | Hybrid intonation, code-switches with Hindi/Tamil/etc. | "American-educated Indian English, slight Indian musicality, surfaces when emotional or speaking to elders" |

### Code-Switching

When characters shift between registers or languages:

| Pattern | Direction | TTS Application |
|---------|-----------|-----------------|
| Formal → vernacular | Under stress, intimacy | "Formal diction that loosens under emotion" |
| English → heritage language | Endearments, exclamations, prayer | Embed transliterated words with accent context |
| Educated → regional | With family, when angry | "Educated American that drops into [regional] with family" |

**Example**: A Caribbean-American character speaks Standard American English at work, then shifts to Trinidadian cadence at home. In TTS, use separate voice prompts or embed context: "American English, but warmer and more rhythmic when speaking to family."

## Texture Vocabulary

| Term | Description | Character Association |
|------|-------------|----------------------|
| **Smooth** | No rasp, even tone | Sophisticates, diplomats, seducers |
| **Gravelly** | Rough, textured | Warriors, drinkers, world-weary |
| **Husky** | Low, slightly rough | Attractive, experienced |
| **Breathy** | Air in voice | Nervous, intimate, exhausted |
| **Nasal** | Resonance in nose | Nerdy, sickly, whiny |
| **Raspy** | Harsh texture | Illness, damage, age |
| **Silky** | Very smooth, controlled | Manipulators, performers |
| **Reedy** | Thin, high | Age, weakness, youth |

## Composite TTS Prompts

Layer attributes for complete character voices:

### Narrator Examples

**Literary Fiction**:
"Perfect audio quality. Male narrator, late forties, American with Mid-Atlantic polish. Warm baritone, measured pace. Intelligent and contemplative, never rushed. Intimate, as if reading to one person."

**Thriller**:
"Perfect audio quality. Male narrator, thirties, American neutral. Clear and direct, driving pace. Controlled tension in the voice. Professional but with urgency underneath."

**Children's**:
"Perfect audio quality. Female narrator, early thirties. Warm and expressive, bright but not shrill. Natural smile in the voice. Varies pace for drama—slows for suspense, quickens for excitement."

### Character Examples

**Gruff Mentor**:
"Elderly male, thick Scottish accent. Gravelly, weathered voice. Slow and deliberate, weight behind every word. World-weary but with buried warmth."

**Young Villain**:
"Male, mid-twenties, aristocratic British. Smooth and controlled. Medium pace, never hurried. Cold underneath the polish. Quiet menace."

**Comic Relief**:
"Male, forties, slight Brooklyn accent. Fast-talking, nervous energy. Higher pitch, variable pace. Finds humor in everything. Self-deprecating."

## Emotional Direction in Dialogue

For dialogue passages, mark emotional shifts:

```
[calm]"I understand what you're saying."
[rising frustration]"But that's not the point."
[barely controlled anger]"The point is you lied to me."
[quiet, dangerous]"And I don't forgive liars."
```

Qwen3-TTS can interpret these as natural language cues embedded in the prompt or provided as context.

## Session Recording Notes

When directing TTS for a full audiobook:

1. **Establish baseline** for each character before production
2. **Document voice settings** in persona files for consistency
3. **Generate test passages** before committing to full chapters
4. **Check character consistency** across chapter breaks
5. **Note any drift** in voice characteristics over long passages

## Troubleshooting Common Issues

| Problem | Directorial Fix |
|---------|-----------------|
| Monotone output | Add emotional markers, specify "varied intonation" |
| Too fast | Specify "measured pace" or "unhurried" |
| Too theatrical | Specify "naturalistic" or "understated" |
| Characters sound same | Differentiate on pitch, pace, texture, accent |
| Emotional disconnect | Provide character context, not just voice description |
| Robotic | Add "natural breaths" or "conversational" |

# StorytellingReferenceBank

Professional storytelling toolkit with integrated TTS audiobook production.

## Your Role

You are auditor, editor, author, architect, detective, and copywriter. Adapt fluidly based on project phase:

- **Early phases**: Big-picture structural feedback, brainstorming, world-building
- **Mid phases**: Scene-level craft, character consistency, pacing
- **Late phases**: Line-by-line editing, polish, production prep

## Core Principles

- **Be direct, clear, unbiased, and forthright.** No hedging.
- **No "safe" writing.** Take risks. Have something to say. Don't sand down edges.
- **Prose style varies by project.** Match the work's needs, not a default voice.
- **Both planning and discovery.** Some projects need outlines; others emerge through drafting.

## Project Structure

```
personas/           # TTS voice personas (Qwen3-TTS compatible)
templates/
  structures/       # Story frameworks (Three-Act, Save the Cat, etc.)
  characters/       # Character sheet templates
  worlds/           # World-building frameworks
style-guides/       # Genre-specific guidelines
audiobook-specs/    # Production specifications
projects/           # Active works
scripts/            # Automation tools
references/         # Research, influences
```

## TTS Production (Qwen3-TTS)

Voice personas use natural language descriptions—no SSML. Key parameters:

- **Age/gender**: "Elderly male", "Young woman in her twenties"
- **Accent**: "Thick Scottish", "Slight Southern drawl"
- **Texture**: "Gravelly", "Smooth", "Breathy", "Husky"
- **Pace**: "Slow and deliberate", "Quick, nervous energy"
- **Emotional baseline**: "Warm", "World-weary", "Playful"

See `@personas/schema.json` for structure, `@audiobook-specs/` for ACX compliance.

## Story Framework Quick Reference

| Framework | Use For | Key Insight |
|-----------|---------|-------------|
| Three-Act | Macro structure | 25/50/25 proportions |
| Save the Cat | Beat-level precision | 15 beats at specific percentages |
| Kishotenketsu | Low-conflict narratives | Twist without antagonist |
| Scene-Sequel | Pacing control | Goal→Conflict→Disaster / Reaction→Dilemma→Decision |

Full templates in `@templates/structures/`.

## Children's Picture Books

**Critical constraints**:
- 500-600 words maximum (ages 3-8)
- 32 pages = 13-14 spreads for story
- Page turns create drama—end spreads with tension
- Rhyme is risky; must work without it for translation

Benchmarks: *Goodnight Moon* (131 words), *Where the Wild Things Are* (336 words).

See `@style-guides/childrens-picture-book.md`.

## Audiobook Specs (ACX/Audible)

| Parameter | Requirement |
|-----------|-------------|
| Format | MP3, CBR 192 kbps, 44.1 kHz |
| RMS Levels | -23 dB to -18 dB |
| Peak Values | -3 dB maximum |
| Noise Floor | -60 dB RMS maximum |
| Room Tone | 0.5-1 sec start, up to 5 sec end |

See `@audiobook-specs/acx-requirements.md`.

## Workflow

1. **New project**: Create folder in `projects/`, define genre/tone/audience
2. **Character work**: Use `@templates/characters/` sheets, store in project's `story-bible/`
3. **Structure**: Select framework from `@templates/structures/`, adapt to project
4. **Drafting**: Progressive disclosure—load only relevant context per scene
5. **Revision**: Big-picture first, line-level as approaching final
6. **TTS prep**: Define character personas, generate chapter-by-chapter
7. **Production**: Apply post-processing chain, verify ACX compliance

## Context Management

- Generate chapter summaries after completion to compress history
- Use `/clear` between distinct writing sessions
- Reference only relevant character/world entries per scene
- Maintain continuity logs for facts (eye colors, locations, timeline)

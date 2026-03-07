# StorytellingReferenceBank

Professional storytelling toolkit with TTS audiobook production.

## Role

Auditor, editor, author, architect. Adapt by phase:
- **Early**: Structure, world-building, brainstorming
- **Mid**: Scene craft, character consistency, pacing
- **Late**: Line editing, polish, production

## Principles

- **Direct and forthright.** No hedging.
- **No safe writing.** Take risks. Have something to say.
- **Style varies by project.** Match the work's needs.

## Foundational Craft → `@references/the-craft-of-lasting-work.md`

What makes work endure:
- Truth over comfort
- Omit strategically (Hemingway's iceberg)
- Specificity reaches universal
- Voice is irreducible
- Make demands on the reader

Techniques: `@references/master-techniques.md`

Dialogue: `@references/dialogue-craft.md`

What's failing (diagnostic): `@references/common-pitfalls.md`

## Navigation

**Complete file index**: `@INDEX.md` — topic-to-file lookup for all resources.

## Structure

```
templates/structures/     # Frameworks (Three-Act, Save the Cat, Rasa, Jo-ha-kyū)
templates/characters/     # Character sheets
templates/worlds/         # World-building
templates/series/         # Series bible
templates/revision-workflow.md
style-guides/            # Genre conventions (genre-guide.md)
personas/                # TTS voices (schema + examples/)
audiobook-specs/         # ACX compliance + sound design spec
scripts/                 # Production pipeline (see scripts/README.md)
projects/                # Active works
references/              # Craft principles, voice vocabulary
docs/                    # Production guides, commercial checklist, sound design
docs/archive/            # Historical audits and validation reports
```

## Quick Reference

### Frameworks → `@templates/structures/`

| Framework | Use | File |
|-----------|-----|------|
| Three-Act | Macro structure | `three-act.md` |
| Save the Cat | Beat precision | `save-the-cat.md` |
| Scene-Sequel | Pacing | `scene-sequel.md` |
| Kishotenketsu | No-conflict | `kishotenketsu.md` |
| Rasa, Jo-ha-kyū, Griot | Global | `global-frameworks.md` |

### Genres → `@style-guides/genre-guide.md`

All genres: literary, thriller, romance, fantasy, SF, mystery, horror, memoir, non-fiction.

Children's picture books: `@style-guides/childrens-picture-book.md` (≤600 words, 32 pages)

### TTS Production → `@audiobook-specs/acx-requirements.md`

ACX specs, post-processing chain, common rejections.

Sound design: `@audiobook-specs/sound-design-spec.md` (cue format) → `@docs/sound-design-architecture.md` (system design)

Voice direction: `@references/voice-direction-vocabulary.md`

### Commercial → `@docs/commercial-production-checklist.md`

Rights, QC, platforms, pricing, direct sales.

Voice cloning: `@docs/voice-cloning-workflow.md`

## Workflow

1. **New project**: `projects/[name]/` with `drafts/`, `story-bible/`, `personas/`
2. **Structure**: Select framework from `templates/structures/`
3. **Draft**: Progressive disclosure — load only relevant context
4. **Revise**: `@templates/revision-workflow.md` (per-scene: `@templates/scene-card.md`)
5. **Preflight**: `scripts/preflight_check.py`
6. **Produce**: `scripts/batch_produce.py` or `scripts/web_studio.py`

## Conventions

### `@` References

`@path/file` means "relative to repo root." In project files, `@personas/name.json` refers to the project's own `personas/` directory — not the root `personas/` library.

### Project Structure

Each project follows: `projects/[name]/drafts/`, `story-bible/characters/`, `personas/`, `speaker-map.json`. Character sheets link to persona JSON via `## TTS Persona Link`.

## Context Management

- Chapter summaries after completion
- `/clear` between sessions
- Continuity logs for facts
- Reference only relevant entries per scene

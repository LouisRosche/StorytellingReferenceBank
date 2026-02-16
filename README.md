# StorytellingReferenceBank

Professional storytelling toolkit with TTS audiobook production.

## Quick Start

1. **Principles & Role**: See [CLAUDE.md](CLAUDE.md)
2. **Find any file**: See [INDEX.md](INDEX.md)
3. **New project**: Create `projects/[name]/` with `drafts/`, `story-bible/`, `personas/`

## Structure

```
templates/       Narrative frameworks, character sheets, world-building
style-guides/    Genre conventions
references/      Craft principles
personas/        TTS voice definitions
audiobook-specs/ ACX compliance
scripts/         Production pipeline
docs/            Setup guides, checklists
projects/        Active works
```

## Key Workflows

| Task | Start Here |
|------|------------|
| Structure a story | `templates/structures/` |
| Develop characters | `templates/characters/character-sheet.md` |
| Match genre conventions | `style-guides/genre-guide.md` |
| Produce audiobook | `scripts/batch_produce.py` |
| Validate ACX compliance | `scripts/acx_validator.py` |

## Setup

**First time?** See [Getting Started](docs/GETTING-STARTED.md) — from clone to first production run.

- Python 3.10+
- GPU recommended for TTS (CPU fallback available)
- See `requirements.txt` and `docs/PRODUCTION-SETUP.md` for hardware details

## License

MIT. See [LICENSE](LICENSE).

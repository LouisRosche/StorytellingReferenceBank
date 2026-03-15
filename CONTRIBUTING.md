# Contributing

## Setup

```bash
git clone <repo-url> && cd StorytellingReferenceBank
python -m venv .venv && source .venv/bin/activate
make install-dev
```

Or manually:

```bash
pip install -r requirements.txt
pip install pytest ruff
```

## Running Checks

| Command | What it does |
|---------|-------------|
| `make check` | Runs tests, persona validation, and dependency check |
| `make lint` | Linting only |
| `make lint-fix` | Auto-fix lint issues |

Run `make check` before every PR. No exceptions.

## Adding a Persona

1. Follow the schema at `personas/schema.json`.
2. See working examples in `personas/examples/`.
3. Validate with `make validate`.

## Adding a TTS Provider

1. Read the guide in `scripts/tts_providers/README.md`.
2. Extend the `base.py` interface.
3. Add tests for your provider.

## Adding a Template or Reference

1. Place the file in the appropriate directory (`templates/`, `references/`, `style-guides/`, etc.).
2. Update `INDEX.md` with the new entry so others can find it.

## Pull Requests

- Run `make check` and confirm it passes.
- Keep changes focused. One concern per PR.
- Describe **what** changed and **why** in the PR description.
- If adding new files, confirm they appear in `INDEX.md`.

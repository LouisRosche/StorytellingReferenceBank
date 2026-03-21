> **ARCHIVED**: 2026-03. Snapshot of pipeline state at time of audit. CI, coverage, and storefront testing have been strengthened since.

# Pipeline, Workflow & Tooling Audit — March 2026

## Scope

Full audit of production pipelines, CI/CD workflows, test infrastructure, scripts,
and supporting tooling across the StorytellingReferenceBank repository.

---

## Executive Summary

The repository is production-capable with a well-architected 6-stage TTS pipeline,
5 provider backends, comprehensive documentation, and a growing test suite.
This audit identified concrete gaps in test coverage, CI strictness, and
operational tooling — and applied fixes where immediate action was warranted.

**Changes applied in this audit:**
- Fixed `conftest.py` sys.path bug (was adding nonexistent `scripts/scripts/`)
- Added 47 new unit tests across 2 new test files
- Un-silenced storefront lint in CI (was `|| true`, hiding real failures)
- Added student-portal validation job to CI
- Added `pytest-cov` to dev dependencies
- Added `make test-coverage` target
- Added `--tb=short` to CI pytest for cleaner failure output
- Cleaned up `make clean` to remove coverage artifacts

---

## What We Found

### 1. Test Coverage

**Before audit: 5 test files, ~60 tests**

| Module | Had Tests | Gap |
|--------|-----------|-----|
| `acx_validator.py` | Yes | — |
| `audio_postprocess.py` | Yes | — |
| `dialogue_parser.py` | Yes | — |
| `multispeaker_tts.py` (SpeakerMap) | Yes | — |
| `tts_generator.py` (imports only) | Partial | No unit tests for chunking edge cases |
| `manuscript_to_chapters.py` | **No** | Now covered (32 tests added) |
| `batch_produce.py` | **No** | Config/report structures now covered (15 tests added) |
| `preflight_check.py` | **No** | Still untested |
| `persona_compatibility.py` | **No** | Still untested |
| `persona_regression.py` | **No** | Still untested |
| `inspect_manuscript.py` | **No** | Still untested |
| `validate_personas.py` | **No** | Run in CI but no unit tests |
| `web_studio.py` | **No** | Gradio UI — integration test candidate |
| Storefront (Next.js) | **No** | No Jest/Vitest configured |

**After audit: 7 test files, 107 tests** (all passing)

### 2. CI/CD Pipeline

**Fixed:**
- Storefront lint was silenced with `|| true` — real ESLint failures were invisible. Now fails the build properly.
- Added `student-portal-check` job: validates `library.json`, `codes.json`, and HTML parse integrity.
- Added `--tb=short` to pytest for cleaner CI output.

**Still silent (intentionally):**
- `pip audit || true` — dependency advisories are informational, not blocking. Reasonable.
- `npm audit --audit-level=high || true` — same rationale.

**What's missing from CI:**
- No test coverage reporting (pytest-cov added to deps; not yet wired into CI upload)
- No Python version matrix (only 3.11 tested; project requires >=3.10)
- No storefront unit/integration tests
- No release/deployment workflow
- No CODEOWNERS file for review routing

### 3. conftest.py Bug

The shared pytest `conftest.py` was adding `scripts/scripts/` (nonexistent) to `sys.path` instead of `scripts/`. This was masked because every individual test file redundantly does its own `sys.path.insert`. Fixed by removing the erroneous `/ "scripts"` suffix.

### 4. Script Robustness

**Strengths:**
- Graceful degradation for all optional dependencies (pyloudnorm, silero-vad, pedalboard, textstat, ebooklib, resemblyzer)
- Per-chapter error isolation in `batch_produce.py` — one chapter failing doesn't abort the run
- Comprehensive preflight validation catches issues before expensive GPU work
- Content-type auto-detection with genre-specific mastering presets

**Observations:**
- `test_pipeline.py` returns `True`/`None` from test functions — pytest warns about non-None returns. These were written as standalone scripts first, then adapted to pytest. Not broken, but noisy.
- `test_dialogue_parser.py` and `test_speaker_map.py` include standalone `run_tests()` runners — redundant with pytest but harmless.
- Several scripts do `sys.path.insert(0, ...)` at module level. Works, but a proper package structure (with `__init__.py` or `src/` layout) would be cleaner.

### 5. Storefront

**Strengths:**
- HMAC-signed download URLs with `crypto.timingSafeEqual` (timing-attack resistant)
- Stripe webhook signature verification
- Idempotent webhook processing
- Runtime env validation with fail-fast

**Gaps:**
- No test framework configured (no Jest, Vitest, or Playwright)
- `package.json` has no `test` script
- No API route tests (checkout, webhooks, download)
- No component tests
- ESLint config appears incomplete (lint was silenced in CI)

### 6. Student Portal

**Strengths:**
- Simple, auditable architecture (static HTML + client-side SHA-256 validation)
- No server, no database — low attack surface
- `manage_student_codes.py` for administration

**Gaps:**
- No CI validation before this audit (now added)
- No accessibility testing
- Client-side code validation is bypassable (by design for a low-stakes portal, but worth noting)

---

## What We Wonder

1. **Why no package structure?** Scripts use `sys.path.insert` hacks. A proper `src/` layout with `__init__.py` would make imports cleaner and enable `pip install -e .` to Just Work for all modules. Is there a reason to avoid this?

2. **Storefront testing strategy?** The storefront handles real money (Stripe). No tests at all is a risk. Even basic API route tests with mocked Stripe would catch regressions.

3. **Pipeline resumability?** `batch_produce.py` tracks per-chapter status, but there's no `--resume` flag to skip already-completed chapters. For a 34-chapter novel like The Listener, a failed run at chapter 30 means re-generating 29 chapters.

4. **Sound design integration?** Sound cues are extracted and saved to JSON, but there's no script that actually mixes them back into the mastered audio. Is this manual? Planned?

5. **Persona regression golden references?** `persona_regression.py` and `personas/golden/` exist, but the `passages/` directory appears empty. Are golden audio references being captured?

6. **Web studio coverage?** `web_studio.py` is 28KB of Gradio UI with no tests. Is it actively used or experimental?

---

## Recommendations for Future Development

### High Priority

1. **Add `--resume` to `batch_produce.py`**
   Check for existing `production_report.json` and skip chapters marked as completed. For long novels, this turns a 4-hour failure into a 10-minute fix.

2. **Storefront test infrastructure**
   Add Vitest + React Testing Library. Start with API route tests for `/api/checkout`, `/api/webhooks/stripe`, and `/api/download`. Mock Stripe SDK. Add `"test": "vitest"` to `package.json`.

3. **Wire pytest-cov into CI**
   Add `--cov=scripts --cov-report=xml` to the CI pytest step. Upload to Codecov or similar. Establish a coverage floor (current estimated: ~40-50% of script lines).

4. **Proper Python package structure**
   Move scripts to `src/storytelling/` with `__init__.py`. Remove all `sys.path.insert` hacks. Update imports. This is a one-time migration that pays dividends in maintainability.

### Medium Priority

5. **Python version matrix in CI**
   Add 3.10 and 3.12 to the test matrix. The project declares `>=3.10` but only tests on 3.11.

6. **Unit tests for remaining scripts**
   Priority order: `preflight_check.py` (validation logic), `persona_compatibility.py` (scoring algorithms), `validate_personas.py` (schema checks).

7. **Sound cue mixing pipeline**
   Script to merge extracted sound cues back into mastered chapter audio at their marked positions. This is the missing link between cue extraction and final delivery.

8. **Populate golden references**
   Generate and commit baseline audio for each example persona. Run `persona_regression.py` in CI to catch voice drift.

### Lower Priority

9. **Release workflow**
   GitHub Actions workflow for tagged releases: run full test suite, build storefront, package artifacts.

10. **CODEOWNERS**
    Route `scripts/` changes to pipeline maintainers, `storefront/` to web maintainers.

11. **Accessibility audit for student portal**
    Run axe-core or Lighthouse CI against `student-portal/index.html`.

12. **Consolidate standalone test runners**
    Remove `run_tests()` / `if __name__ == "__main__"` blocks from test files. Pytest handles everything. The standalone runners add maintenance burden without value.

---

## Files Changed in This Audit

| File | Change |
|------|--------|
| `scripts/tests/conftest.py` | Fixed sys.path bug |
| `scripts/tests/test_manuscript_to_chapters.py` | **New** — 32 tests |
| `scripts/tests/test_batch_produce.py` | **New** — 15 tests |
| `.github/workflows/ci.yml` | Un-silenced storefront lint, added student-portal job, added `--tb=short` |
| `pyproject.toml` | Added `pytest-cov` to dev deps |
| `Makefile` | Added `test-coverage` target, updated `clean` |
| `docs/archive/PIPELINE-AUDIT-2026-03.md` | **New** — this report |

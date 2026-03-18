# Index

Topic-to-file reference. One authoritative source per topic.

## Craft & Theory

| Topic | Source |
|-------|--------|
| Why work endures | `references/the-craft-of-lasting-work.md` |
| Practical techniques | `references/master-techniques.md` |
| Dialogue craft | `references/dialogue-craft.md` |
| Common pitfalls (diagnostic) | `references/common-pitfalls.md` |
| Revision process | `templates/revision-workflow.md` |
| Scene planning (per-scene card) | `templates/scene-card.md` |

## Missouri Learning Standards — All Subjects (Grades 5–12)

For a 5–12 public charter school in St. Louis, MO. Cross-curricular scientist story planning.

| Subject | Source |
|---------|--------|
| Science (NGSS / MLS-S): full standards, STL hooks | `references/ngss-standards-5-12.md` |
| English Language Arts (MLS-ELA): all strands, RST/WHST | `references/mls-ela-5-12.md` |
| Social Studies (MLS-SS): history, civics, economics, geography | `references/mls-social-studies-5-12.md` |
| Mathematics (MLS-Math): practices + content K–12 | `references/mls-math-5-12.md` |
| Fine Arts, Health/PE, World Languages | `references/mls-arts-health-languages-5-12.md` |
| Cross-curricular planning matrix + worked scientist examples | `references/cross-curricular-story-matrix.md` |
| Scientist story planning guide + roster (20+ scientists) | `references/ngss-scientist-story-guide.md` |
| Scientist story planning template | `templates/structures/scientist-story.md` |

## Story Structure

| Topic | Source |
|-------|--------|
| Three-Act | `templates/structures/three-act.md` |
| Save the Cat (15 beats) | `templates/structures/save-the-cat.md` |
| Scene-Sequel pacing | `templates/structures/scene-sequel.md` |
| Kishotenketsu | `templates/structures/kishotenketsu.md` |
| Rasa, Jo-ha-kyū, Griot | `templates/structures/global-frameworks.md` |
| Scientist Story (NGSS-aligned) | `templates/structures/scientist-story.md` |

## Genre

| Topic | Source |
|-------|--------|
| All genres (literary→self-help) | `style-guides/genre-guide.md` |
| Children's picture books | `style-guides/childrens-picture-book.md` |

## Characters & Worlds

| Topic | Source |
|-------|--------|
| Character development | `templates/characters/character-sheet.md` |
| Antagonist development | `templates/characters/antagonist-sheet.md` |
| Subplot tracking | `templates/subplot-tracker.md` |
| World-building | `templates/worlds/world-building-framework.md` |
| Series continuity | `templates/series/series-bible.md` |

## TTS & Audio

| Topic | Source |
|-------|--------|
| ACX technical specs | `audiobook-specs/acx-requirements.md` |
| Sound design cue format | `audiobook-specs/sound-design-spec.md` |
| Sound design architecture | `docs/sound-design-architecture.md` |
| Sound design tool evaluation | `docs/sound-design-research.md` |
| Voice direction vocabulary | `references/voice-direction-vocabulary.md` |
| Voice cloning | `docs/voice-cloning-workflow.md` |
| Persona schema | `personas/schema.json` |
| Persona taxonomy | `personas/taxonomy.md` |
| Library coverage status | `personas/library-status.md` |
| Golden references | `personas/golden/README.md` |

## Bespoke Personalities Product

| Topic | Source |
|-------|--------|
| Product architecture | `docs/bespoke-personalities-product.md` |
| Voice taxonomy & math | `personas/taxonomy.md` |
| Library status | `personas/library-status.md` |
| Compatibility scoring | `scripts/persona_compatibility.py` |
| Regression testing | `scripts/persona_regression.py` |

## Production

| Topic | Source |
|-------|--------|
| **Getting started** | `docs/GETTING-STARTED.md` |
| Commercial checklist | `docs/commercial-production-checklist.md` |
| Hardware/setup | `docs/PRODUCTION-SETUP.md` |
| Scripts overview | `scripts/README.md` |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/batch_produce.py` | Full pipeline orchestration |
| `scripts/tts_generator.py` | TTS generation |
| `scripts/audio_postprocess.py` | ACX-compliant mastering |
| `scripts/acx_validator.py` | Compliance checking |
| `scripts/manuscript_to_chapters.py` | Manuscript splitting |
| `scripts/dialogue_parser.py` | Multi-speaker extraction |
| `scripts/multispeaker_tts.py` | Multi-voice generation |
| `scripts/inspect_manuscript.py` | Manuscript analysis |
| `scripts/preflight_check.py` | Pre-production validation |
| `scripts/persona_compatibility.py` | Story-persona matching |
| `scripts/persona_regression.py` | Voice consistency testing |
| `scripts/web_studio.py` | Gradio web interface |
| `scripts/validate_personas.py` | Persona schema validation |
| `scripts/manage_student_codes.py` | Student access code admin |

## Storefront

| Topic | Source |
|-------|--------|
| Storefront overview | `storefront/README.md` |
| Stripe checkout API | `storefront/src/app/api/checkout/route.ts` |
| Download delivery API | `storefront/src/app/api/download/route.ts` |
| Webhook handler | `storefront/src/app/api/webhooks/stripe/route.ts` |

## Student Portal

| Topic | Source |
|-------|--------|
| Portal application | `student-portal/index.html` |
| Deployment guide | `student-portal/DEPLOY.md` |
| Content manifest | `student-portal/library.json` |
| Access code management | `scripts/manage_student_codes.py` |

## Testing

| Topic | Source |
|-------|--------|
| Test configuration | `scripts/tests/conftest.py` |
| Pipeline tests | `scripts/tests/test_pipeline.py` |
| ACX validator tests | `scripts/tests/test_acx_validator.py` |
| Audio processing tests | `scripts/tests/test_audio_postprocess.py` |
| Dialogue parser tests | `scripts/tests/test_dialogue_parser.py` |
| Speaker map tests | `scripts/tests/test_speaker_map.py` |
| Manuscript splitter tests | `scripts/tests/test_manuscript_to_chapters.py` |
| Batch produce tests | `scripts/tests/test_batch_produce.py` |

## Build & Config

| Topic | Source |
|-------|--------|
| Makefile targets | `Makefile` |
| Python packaging | `pyproject.toml` |
| CI pipeline | `.github/workflows/ci.yml` |
| Core dependencies | `requirements.txt` |

## Contributing

| Topic | Source |
|-------|--------|
| How to contribute | `CONTRIBUTING.md` |

## Archive

| Document | Purpose |
|----------|---------|
| `docs/archive/OPPORTUNITIES-ANALYSIS-2026-03.md` | Forward-looking opportunities & priority matrix |
| `docs/archive/TTS-PIPELINE-EVALUATION-2026-01.md` | TTS engine comparison |
| `docs/archive/REPO-AUDIT-SWOT-2026-01.md` | Repository strengths/gaps analysis |
| `docs/archive/framework-validation-2026-01.md` | Framework coverage validation |
| `docs/archive/PIPELINE-AUDIT-2026-03.md` | Pipeline, workflow & tooling audit |

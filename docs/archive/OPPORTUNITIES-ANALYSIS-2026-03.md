> **ARCHIVED**: 2026-03-15. Several items completed since writing: CONTRIBUTING.md exists, Priority 3 personas created (comedy, horror, australian, child), The Listener expanded to 34 chapters, student portal deployed, storefront built.

# Opportunities Analysis — March 2026

**Date**: 2026-03-15
**Scope**: Forward-looking opportunities based on current repo state
**Prior audit**: `REPO-AUDIT-SWOT-2026-01.md` (January 28, 2026)

---

## What's Changed Since the January SWOT

The January audit scored the repo 8.2/10 and identified it as "production-ready with clear expansion roadmap." Since then:

| Accomplishment | Impact |
|---------------|--------|
| **The Listener**: 34 chapters (~271K words) complete | First novel-length manuscript; validates long-form pipeline design |
| **The House Remains**: 2 chapters drafted | Second literary drama project started |
| **The Weight of Mangoes**: 2 chapters + full story bible | Third project with comprehensive planning |
| **Revision pass** (PR #20): continuity fixes across projects | Quality hardening |
| **Student portal**: code-gated library with GitHub Pages deploy | New user segment (educators) served |
| **Full MLS coverage**: ELA, math, social studies, arts (grades 5–12) | Educational standards complete for Missouri charter context |
| **Kokoro provider**: lightweight TTS for fast iteration | Draft-mode workflow enabled |
| **ElevenLabs provider**: cloud TTS option | Provider diversity increased to 5 |
| **Antagonist sheet, subplot tracker, scene-sequel reference** | Templates gap-filled |

**Net assessment**: The January SWOT's top two recommendations — "create golden references" and "add a novel-length test project" — are now half-addressed. The Listener exists but hasn't been production-tested. Golden references remain pending.

---

## I. High-Impact Opportunities

### 1. Produce The Listener End-to-End

**The gap**: A 271K-word, 34-chapter thriller manuscript sits complete but unproduced. This is the single highest-value validation the pipeline can undergo.

**What it proves**:
- Long-form chapter splitting at scale (34 chapters, varying lengths)
- Multi-speaker TTS with 9 personas across sustained narrative
- Audio post-processing on hours of content (estimated 25-30 hours of audio)
- ACX compliance for a commercial-length work
- Batch orchestration performance and error recovery

**What to do**:
1. Run `scripts/preflight_check.py` against The Listener project
2. Execute `batch_produce.py` in dry-run mode to surface any issues
3. Produce one chapter (chapter-03, first non-setup chapter) as a proof run
4. Full batch production with timing benchmarks
5. Write a production report comparable to Luna's `PRODUCTION-TEST-REPORT.md`

**Effort**: Medium (infrastructure exists; this is execution)
**Impact**: Critical — transforms the repo from "picture-book tested" to "novel-length validated"

---

### 2. Generate Golden References

**The gap**: All 15 personas show "pending generation" in `personas/library-status.md`. The regression testing infrastructure (`persona_regression.py`, golden passages, MFCC fingerprinting) is complete but has no ground truth.

**What it enables**:
- Persona drift detection when models update
- Automated quality gates in the production pipeline
- Confidence that TTS provider switches don't degrade voice quality
- A baseline for the bespoke-personalities product (Phase 2 prerequisite)

**What to do**:
1. Generate candidate audio for each persona using `personas/golden/passages/standard-narrative.txt`
2. Human review each candidate (or at minimum, spot-check 5 representative personas)
3. Normalize and commit approved audio as golden references
4. Update persona JSON files with `quality.golden_reference` paths
5. Run regression suite to establish baseline metrics

**Effort**: Medium (requires TTS hardware for generation + human ear for approval)
**Impact**: High — unblocks the entire quality operations layer

---

### 3. Sound Design Implementation

**The gap**: Architecture is fully designed (`docs/sound-design-architecture.md`) with system diagrams, provider abstraction, cue format, and mixing strategy. Zero implementation exists.

**What it enables**:
- Ambient music and SFX in audiobooks (competitive differentiator)
- Enhanced children's audiobook production (Luna would benefit immediately)
- A second product axis beyond voice (sound + voice = immersive audio)

**What to do**:
1. Implement cue parser (extract `[SFX:...]`, `[MUSIC:...]` from manuscripts)
2. Build asset resolution layer (local library → AI generation fallback)
3. Create mixing engine (narration + sound layers with ducking)
4. Integrate with `batch_produce.py` as optional pipeline stage
5. Test with Luna (shortest, simplest manuscript)

**Effort**: High (new subsystem, multiple components)
**Impact**: High — differentiator in a crowded TTS-audiobook space

---

### 4. CI/CD Pipeline

**The gap**: No automated testing on push/PR. The Makefile has `test`, `validate`, `lint`, and `check` targets but nothing triggers them automatically.

**What it enables**:
- Catch persona schema regressions before merge
- Validate Python quality on every PR
- Run preflight checks automatically
- Protect against accidental breakage as the codebase grows

**What to do**:
1. Add `.github/workflows/ci.yml` with: lint (`ruff`), test (`pytest`), persona validation
2. Use `test-quick` target (no GPU) for CI; full test locally
3. Add status badges to README
4. Consider a nightly job that runs `preflight_check.py` against all projects

**Effort**: Low (all targets exist; just needs wiring)
**Impact**: Medium — prevents regressions, signals maturity to contributors

---

## II. Strategic Opportunities

### 5. The Listener as a Commercial Showcase

The Listener isn't just a test manuscript — it's a 34-chapter psychological thriller with 9 distinct character voices. If produced well, it becomes:

- **A demo reel** for the entire pipeline (link in README, share with potential users)
- **A case study** showing craft philosophy → manuscript → audiobook
- **A stress test** for every system in the repo simultaneously

Consider producing select chapters (prologue, a dialogue-heavy chapter, the climax) as publicly shareable samples.

---

### 6. Educator Pipeline: Scientist Stories → Audiobook

The educational standards coverage (NGSS + MLS, grades 5–12) combined with the scientist-story template creates an unexploited pipeline:

```
Scientist selection → Story planning (cross-curricular matrix)
  → Manuscript drafting → TTS production → Student portal delivery
```

No one else offers this. A teacher could:
1. Pick a scientist from the 20+ exemplar roster
2. Use the scientist-story template to align with NGSS + MLS standards
3. Draft (or have students draft) the story
4. Produce an audiobook with the children's narrator persona
5. Distribute via the student portal

**What to do**: Create one end-to-end example. Pick a scientist from `references/ngss-scientist-story-guide.md`, draft a 600-word story using `templates/structures/scientist-story.md`, produce it, and deploy to the student portal. Document the workflow.

**Effort**: Medium
**Impact**: High for the educational market — demonstrates a complete value chain

---

### 7. Priority 3 Personas

Four personas are planned but uncreated:

| Persona | Gap Filled | Why It Matters |
|---------|-----------|---------------|
| `narrator-comedy` | Humor/satire genre | No current persona handles comedic timing |
| `narrator-horror` | Dark/horror genre | The Listener (thriller) is close but horror needs different texture |
| `narrator-australian` | AU/NZ accent | 6/8 accent regions covered; this fills a commercial gap |
| `character-child` | Under-12 voice | Luna has child characters but no child persona; picture books need this |

Creating these brings the library to 19 personas (within the 15–18 optimal range from the taxonomy, with room for the coverage improvement).

**Effort**: Low per persona (schema and examples exist as templates)
**Impact**: Medium — closes known dimensional gaps

---

### 8. Bespoke Personalities Product: Phase 2

Phase 1 (base library) is complete. Phase 2 (Quality Ops) is designed but not wired:

| Component | Status | What Remains |
|-----------|--------|-------------|
| `persona_compatibility.py` | Script exists | Wire to web studio; add story metadata input |
| `persona_regression.py` | Script exists | Needs golden references (see Opportunity #2) |
| Automated QC pipeline | Designed in `bespoke-personalities-product.md` | Implement quality gates in `batch_produce.py` |

The compatibility scoring algorithm is fully specified (§4.2 of the product doc). Wiring it into `web_studio.py` as a "Find My Narrator" tab would be a tangible product feature.

**Effort**: Medium
**Impact**: Medium-high — moves from toolkit to product

---

## III. Quick Wins

### 9. Makefile Targets for All Projects

Currently, `dry-run` and `inspect` only target Luna. Add targets for The Listener, The Weight of Mangoes, and The House Remains.

```makefile
dry-run-listener:
	$(PY) scripts/batch_produce.py \
		projects/the-listener/drafts/chapter-03.txt \
		--persona projects/the-listener/personas/narrator-thriller.json \
		--dry-run --verbose

inspect-listener:
	$(PY) scripts/inspect_manuscript.py \
		projects/the-listener/drafts/chapter-03.txt \
		--speaker-map projects/the-listener/speaker-map.json
```

**Effort**: Minimal
**Impact**: Low but removes friction for working with non-Luna projects

---

### 10. Type Annotations for Core Scripts

The January SWOT noted "no typing stubs or mypy configuration." The scripts are clean Python but lack type hints. Adding them to the core pipeline scripts (`batch_produce.py`, `tts_generator.py`, `audio_postprocess.py`) would:

- Enable IDE support for contributors
- Catch interface mismatches between scripts
- Prepare for `mypy --strict` in CI

**Effort**: Low-medium (scripts are well-structured; types are inferrable)
**Impact**: Low — code quality improvement, contributor experience

---

### 11. CONTRIBUTING.md

The January SWOT flagged "bus factor of 1" and "no contributor docs." A minimal `CONTRIBUTING.md` covering:

- How to set up the dev environment (`make install-dev`)
- How to run tests (`make check`)
- How to add a new persona (follow schema + examples)
- How to add a new TTS provider (follow `tts_providers/README.md`)
- PR expectations

**Effort**: Minimal
**Impact**: Low but removes barrier to collaboration

---

## IV. Priority Matrix

| # | Opportunity | Effort | Impact | Dependencies |
|---|-----------|--------|--------|-------------|
| 1 | **Produce The Listener** | Medium | Critical | TTS hardware |
| 2 | **Generate golden references** | Medium | High | TTS hardware |
| 4 | **CI/CD pipeline** | Low | Medium | None |
| 9 | **Makefile targets for all projects** | Minimal | Low | None |
| 11 | **CONTRIBUTING.md** | Minimal | Low | None |
| 7 | **Priority 3 personas** | Low | Medium | None |
| 6 | **Educator pipeline example** | Medium | High | Persona for children's |
| 3 | **Sound design implementation** | High | High | Architecture review |
| 8 | **Bespoke product Phase 2** | Medium | Medium-high | Golden references (#2) |
| 5 | **Listener as showcase** | Medium | Medium | Production run (#1) |
| 10 | **Type annotations** | Low-medium | Low | None |

**Recommended sequence**:
1. Quick wins first: CI/CD (#4), Makefile (#9), CONTRIBUTING.md (#11)
2. Infrastructure: Golden references (#2), Priority 3 personas (#7)
3. Validation: Produce The Listener (#1)
4. Product: Educator pipeline (#6), Bespoke Phase 2 (#8)
5. Differentiation: Sound design (#3)

---

## V. What NOT to Do

These look tempting but would be premature:

| Temptation | Why Not |
|-----------|---------|
| Add more TTS providers | 5 providers is sufficient; diminishing returns |
| Build a SaaS platform | Validate the pipeline at scale first (Opportunity #1) |
| Expand to 25+ personas | 15–19 covers 80%+ of space; more adds redundancy risk |
| Add non-English manuscripts | French and Hindi personas exist but no non-English project validates them; add one project first, not many |
| Rewrite scripts in a framework | The scripts work. They're modular. Don't abstract what isn't hurting |

---

## VI. Metrics to Track

| Metric | Current | Target | How to Measure |
|--------|---------|--------|---------------|
| Projects production-tested | 1 (Luna) | 3 | Production reports in each project |
| Golden references populated | 0/15 | 15/15 | `personas/library-status.md` |
| CI pipeline | None | Green on every PR | GitHub Actions status |
| Persona coverage score | 76% | 82% (with Priority 3) | `personas/library-status.md` |
| Longest production-validated manuscript | ~2,600 words | ~271,000 words | The Listener production report |
| Test coverage | Integration only | Integration + unit | `pytest --cov` |

---

*Analysis conducted 2026-03-15*
*Branch: claude/analyze-repo-opportunities-82P16*

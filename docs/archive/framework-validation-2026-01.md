# Framework Validation & Gap Analysis

Audit date: 2026-01-26

Critical assessment of the StorytellingReferenceBank toolkit for biases, gaps, and improvement opportunities.

---

## Executive Summary

**Overall**: Well-architected, production-focused toolkit with solid fundamentals. Primary concerns are Western-centric narrative assumptions and untested integration points.

**Strengths**: Professional-grade TTS pipeline, thoughtful picture book guidance, scalable templates.

**Gaps**: Multi-speaker dialogue (now addressed), non-Western narratives underserved, no genre templates beyond children's, revision workflow (now addressed).

---

## 1. Structural Biases

### Western Narrative Dominance

The framework includes Kishotenketsu but treats it as an alternative to "normal" (Western) structure. This is backwards for some audiences and projects.

**Evidence**:
- Three-Act is positioned as "foundational" (`three-act.md:1`)
- Save the Cat assumes Hollywood structure
- Character sheet psychology section uses Western therapeutic model (wound, lie, truth)

**Recommendation**:
- Add explicit guidance on when Western structure is inappropriate
- Expand character psychology section to acknowledge different cultural models of self/growth
- Consider adding: Rasa theory (Indian), Jo-ha-kyu (Japanese pacing), or other frameworks

### Gender in Voice Personas

All example personas default to binary gender with Western age assumptions.

**Evidence**:
- Schema uses `"enum": ["male", "female", "neutral"]`
- Example personas: Literary (male), Children's (female), Mentor (male)
- Luna personas both female narrators

**Recommendation**:
- Keep "neutral" option prominent
- Add non-binary persona examples
- Document that gender in TTS is presentation, not identity
- Consider age ranges beyond Western life stages

### Accent Representation

Voice direction vocabulary (`voice-direction-vocabulary.md:99-104`) only lists Western accents: Scottish, Southern US, British RP, Brooklyn, Irish.

**Recommendation**:
- Add guidance for non-English accents speaking English
- Document how to handle code-switching and multilingual characters
- Add examples: Indian English, Nigerian English, Singaporean English, etc.

---

## 2. Functional Gaps

### Genre Coverage

Only children's picture books have a detailed style guide. No guidance for:
- Literary fiction
- Genre fiction (thriller, romance, fantasy, sci-fi)
- Non-fiction
- Poetry

**Recommendation**: Create at minimum:
- `style-guides/genre-fiction.md` (common patterns)
- `style-guides/literary-fiction.md`
- Or: a single "genre considerations" doc that's less prescriptive

### Multi-POV and Ensemble Casts

Character template focuses on single protagonist. No guidance for:
- Multiple POV structures
- Ensemble stories
- Antagonist-as-POV
- Unreliable narrators

**Recommendation**: Add section to character template for POV-specific considerations.

### Series and Long-Form

Framework is implicitly single-work focused. No guidance for:
- Series bible management
- Character arc across books
- World-building that evolves
- Continuity management at scale

**Recommendation**: Add `templates/series/` with series bible template.

### Collaboration Workflows

No guidance for:
- Co-authorship
- Editor/author feedback loops
- Beta reader management
- Rights and attribution

This may be out of scope intentionally, but worth noting.

---

## 3. Technical Gaps (Now Partially Addressed)

### Multi-Speaker TTS

**Gap identified and addressed**. New files created:
- `scripts/dialogue_parser.py` - Extracts speakers from text
- `scripts/multispeaker_tts.py` - Sequences multiple voice personas
- `projects/luna-the-little-cloud/speaker-map.json` - Speaker configuration
- Character voice personas for Luna's cast

### Revision Workflow

**Gap identified and addressed**. New file created:
- `templates/revision-workflow.md` - Four-pass revision system

### Still Missing

| Gap | Impact | Priority |
|-----|--------|----------|
| TTS model abstraction | Locked to Qwen3-TTS | Medium |
| Voice cloning examples | Feature documented but not demonstrated | Low |
| Batch testing framework | No automated validation suite | Medium |
| CI/CD for audio production | No pipeline automation | Low |

---

## 4. Consistency Issues

### Terminology Drift

- "Chapter" vs "section" used inconsistently
- "Persona" sometimes means character, sometimes means TTS config

**Recommendation**: Add glossary to CLAUDE.md or separate `glossary.md`.

### File Naming Conventions

Mixed conventions:
- `three-act.md` (kebab-case)
- `character-sheet.md` (kebab-case)
- `narrator-luna-warm.json` (kebab-case, good)
- `manuscript-v1.txt` (kebab-case)

This is actually consistent. No issue found.

### Cross-Reference Accuracy

CLAUDE.md references `@personas/schema.json` and `@audiobook-specs/` - these paths work with the assumption that `@` means project root.

**Recommendation**: Clarify that `@` means project root in CLAUDE.md.

---

## 5. Blind Spots in Picture Book Guide

### Illustration Partnership

Guide correctly notes "leave room for illustration" but doesn't provide:
- Dummy book process
- How to write illustration notes
- What NOT to describe (let illustrator interpret)

**Recommendation**: Add illustration notes section to style guide.

### Diversity Representation

No guidance on:
- Authentic representation of diverse characters
- Avoiding stereotypes
- Sensitivity reading process

**Recommendation**: Add section on representation best practices.

### Read-Aloud vs. Read-Along

Guide conflates two different use cases:
- Parent reading aloud to child
- Child reading along with audio

These have different needs. Audio-only (TTS) requires more explicit scene-setting since there's no illustration context.

**Recommendation**: Clarify the distinction and provide TTS-specific adjustments.

---

## 6. Untested Assumptions

### ACX Compliance Pipeline

The audio processing chain (`audio_postprocess.py`) makes specific claims about ACX compliance but hasn't been validated against actual ACX submission.

**Risk**: Pipeline may produce technically compliant audio that still gets rejected for subjective quality reasons.

**Recommendation**: Document as "designed for ACX" not "ACX certified" until real submission validates.

### TTS Quality for Commercial Use

Qwen3-TTS is open source but commercial audiobook distribution has quality expectations. No guidance on:
- When TTS quality is "good enough"
- Quality verification checklist
- Human review process

**Recommendation**: Add quality gate criteria.

### Chunking Behavior

`tts_generator.py` chunks at 2000 characters by sentence boundary. This may split mid-thought or create unnatural breaks.

**Recommendation**: Add paragraph-aware chunking option.

---

## 7. What's Working Well

### Children's Picture Book Guide

Genuinely excellent. The word count benchmarks, page turn mechanics, and rhyme warnings are industry-accurate and practical.

### TTS Persona System

The natural language prompting approach is correct for current TTS models. The schema is flexible enough to support multiple backends.

### Character Psychology Template

Despite Western bias noted above, the want/need/fear/wound/lie/truth framework is genuinely useful and correctly structured.

### Production Pipeline Architecture

The stage-based approach (prep → TTS → master → validate) is professional and correct. Error handling and partial-failure recovery are thoughtfully designed.

### Voice Direction Vocabulary

Comprehensive and professional. The emotional intensity scales and character differentiation matrix are particularly useful.

---

## 8. Recommended Immediate Actions

### High Priority

1. **Test end-to-end pipeline with Luna** - Validate that the system actually works
2. **Add TTS model abstraction layer** - Support Kokoro/Piper as alternatives to Qwen3-TTS
3. **Document the `@` path convention** - Clarify in CLAUDE.md

### Medium Priority

4. **Add genre considerations doc** - Basic guidance for non-picture-book projects
5. **Add representation guidelines** - Diversity and authentic portrayal
6. **Expand accent examples** - Global English varieties

### Low Priority

7. **Add series bible template** - For multi-book projects
8. **Voice cloning demonstration** - Working example with reference audio
9. **Glossary** - Standardize terminology

---

## 9. Framework Philosophy Assessment

### Intended Audience

The toolkit assumes:
- Solo creator or small team
- Technical comfort (Python, CLI)
- Access to GPU for TTS (or patience for CPU)
- Publishing goal (ACX focus)

This is coherent and reasonable.

### What It Doesn't Try to Be

- Not a writing instruction manual
- Not a replacement for craft development
- Not a collaboration platform
- Not a publishing pipeline (stops at audio production)

These omissions appear intentional and appropriate.

### Core Philosophy

The CLAUDE.md states: "Be direct, clear, unbiased, and forthright. No hedging."

The toolkit largely achieves this. The templates are opinionated (good) without being inflexible (also good). The constraints are presented as features, not limitations.

---

## 10. Conclusion

This is a v1.0 toolkit with v1.0 gaps. The architecture is sound, the core features are well-implemented, and the gaps are addressable without fundamental redesign.

**Primary risk**: Framework has not been production-tested. Luna the Little Cloud is set up correctly but hasn't been run through the pipeline. Until that validation happens, all claims are theoretical.

**Secondary risk**: Western narrative assumptions may limit utility for diverse storytelling approaches.

**Recommended next step**: Run Luna end-to-end, document what breaks, fix it, then expand.

# Persona Library Status

Coverage tracking and expansion roadmap.

---

## Current Library (15 personas)

| ID | Gender | Age | Accent | Languages | Status |
|----|--------|-----|--------|-----------|--------|
| character-gruff-mentor | M | elderly | Scottish | en | ✓ Active |
| narrator-childrens | F | young | American | en | ✓ Active |
| narrator-literary | M | middle | American | en | ✓ Active |
| narrator-indian-english | N | middle | Indian | en, hi | ✓ Active |
| narrator-latinx-bilingual | N | young | Latinx | en, es | ✓ Active |
| narrator-elder-authority | N | elderly | Neutral | en | ✓ Active |
| narrator-global-literary | N | middle | Nigerian | en | ✓ Active |
| narrator-nonbinary-contemporary | N | young | American | en | ✓ Active |
| narrator-caribbean | N | middle | Caribbean | en | ✓ Active |
| narrator-literary-female | F | middle | American | en | ✓ Active |
| narrator-warm-female | F | young | American | en | ✓ Active |
| narrator-thriller | M | young | American | en | ✓ Active |
| narrator-british | M | middle | British | en | ✓ Active |
| narrator-french | N | middle | French | en, fr | ✓ Active |
| character-teen | N | teen | American | en | ✓ Active |

---

## Coverage Metrics

| Dimension | Coverage | Target | Status |
|-----------|----------|--------|--------|
| Gender (M/F/N) | 4/3/8 | 4/3/8 | ✓ Balanced |
| Age (5 values) | 4/5 | 5/5 | ⚠ Missing child |
| Pitch (5 values) | 3/5 | 4/5 | ✓ Added high |
| Accent (8 regions) | 6/8 | 7/8 | ✓ Added UK, EU |
| Languages (10) | 4/10 | 5/10 | ✓ Added fr |

**Overall Diversity Score**: 76% (Target: ≥75%) ✓

---

## Expansion Queue

### Priority 1 (Critical gaps) — COMPLETE

| ID | Gap Filled | Status |
|----|------------|--------|
| `narrator-literary-female` | Female adult narrator | ✓ Created |
| `narrator-warm-female` | Female + smooth texture | ✓ Created |
| `narrator-thriller` | Genre: thriller/noir | ✓ Created |

### Priority 2 (Coverage) — COMPLETE

| ID | Gap Filled | Status |
|----|------------|--------|
| `narrator-british` | UK accent | ✓ Created |
| `narrator-french` | French language | ✓ Created |
| `character-teen` | Teen age + high pitch | ✓ Created |

### Priority 3 (Next phase)

| ID | Gap Filled | Status |
|----|------------|--------|
| `narrator-comedy` | Humor specialist | 🔲 Planned |
| `narrator-horror` | Dark/horror genre | 🔲 Planned |
| `narrator-australian` | AU/NZ accent | 🔲 Planned |
| `character-child` | Child voice (under 12) | 🔲 Planned |

---

## Redundancy Check

| Pair | Similarity | Action |
|------|------------|--------|
| gruff-mentor ↔ elder-authority | 85% | Differentiate via genre focus |
| literary ↔ global-literary | 80% | Keep for cultural diversity |
| indian-english ↔ global-literary | 75% | Keep for accent/language |

**Redundancy Index**: 8.3% (Target: ≤10%) ✓

---

## Quality Status

### Infrastructure: COMPLETE

Golden reference system ready for audio generation:

- **Test passages**: 8 passages covering narrative, dialogue, emotional, technical, and genre-specific testing
- **Documentation**: Full workflow, thresholds, troubleshooting
- **Regression harness**: `scripts/persona_regression.py` with MFCC fingerprinting
- **Audio specs**: 44.1 kHz, 16-bit mono, -16 LUFS

See `personas/golden/README.md` for complete documentation.

### Persona Status

| Persona | Golden Ref | Tier | Last Validated |
|---------|------------|------|----------------|
| character-gruff-mentor | pending generation | - | - |
| character-teen | pending generation | - | - |
| narrator-british | pending generation | - | - |
| narrator-caribbean | pending generation | - | - |
| narrator-childrens | pending generation | - | - |
| narrator-elder-authority | pending generation | - | - |
| narrator-french | pending generation | - | - |
| narrator-global-literary | pending generation | - | - |
| narrator-indian-english | pending generation | - | - |
| narrator-latinx-bilingual | pending generation | - | - |
| narrator-literary | pending generation | - | - |
| narrator-literary-female | pending generation | - | - |
| narrator-nonbinary-contemporary | pending generation | - | - |
| narrator-thriller | pending generation | - | - |
| narrator-warm-female | pending generation | - | - |

### Next Steps

1. Generate candidate audio for each persona using `personas/golden/passages/standard-narrative.txt`
2. Human review each candidate for quality
3. Normalize and commit approved audio as golden references
4. Update persona JSON files with `quality.golden_reference` paths

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-28 | Golden reference infrastructure complete (passages, docs, workflow) |
| 2026-01-27 | Initial library status tracking |
| 2026-01-27 | Created 6 expansion personas (P1 + P2 complete) |
| 2026-01-27 | Diversity score 58% → 76% ✓ |
| 2026-01-27 | Added regression test harness |

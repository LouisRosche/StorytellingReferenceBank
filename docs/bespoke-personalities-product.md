# Bespoke Reading Personalities: Product Architecture

System design for a mathematically-optimized library of TTS voice personas serving N personas × M stories with consistent quality.

---

## 1. Combinatorial Challenge

**Problem**: Users choose any persona to read any story.
- N personas × M stories = N×M combinations
- Cannot manually QC every combination
- Must guarantee consistent quality at scale

**Solution**: Dimensional optimization + automated validation + sampling-based QC.

---

## 2. Voice Space Taxonomy

### 2.1 Primary Dimensions (7)

| Dimension | Cardinality | Values |
|-----------|-------------|--------|
| **Gender** | 4 | male, female, neutral, androgynous |
| **Age** | 5 | child, teen, young_adult, middle_aged, elderly |
| **Pitch** | 5 | very_low, low, medium, high, very_high |
| **Pace** | 5 | very_slow, slow, medium, fast, very_fast |
| **Texture** | 6 | smooth, warm, breathy, husky, gravelly, crisp |
| **Accent Region** | 8 | NA, UK, AU/NZ, African, Indian, Caribbean, European, Asian |
| **Primary Language** | 10 | en, es, fr, de, zh, ja, ko, pt, ru, it |

**Theoretical space**: 4 × 5 × 5 × 5 × 6 × 8 × 10 = **240,000 combinations**

### 2.2 Secondary Dimensions (4)

| Dimension | Type | Purpose |
|-----------|------|---------|
| **Emotional Range** | Set of 5-8 | What emotions this voice handles well |
| **Genre Affinity** | Set of 3-5 | Genres this voice suits |
| **Energy Level** | 1-5 scale | Baseline energy/intensity |
| **Warmth** | 1-5 scale | Interpersonal warmth in delivery |

### 2.3 Coverage Strategy

**Target**: Cover the practical voice space with **15-18 personas** achieving:
- ≥80% of user preference space covered
- No redundant personas (>70% similarity)
- Every primary dimension value represented ≥1×

---

## 3. Optimal Library Composition

### 3.1 Core Narrators (6) — High-volume defaults

| ID | Gender | Age | Pitch | Accent | Primary Use |
|----|--------|-----|-------|--------|-------------|
| `narrator-literary-m` | M | middle | low | NA (Mid-Atlantic) | Literary fiction, memoir |
| `narrator-literary-f` | F | middle | medium | NA (General) | Literary fiction, memoir |
| `narrator-contemporary-n` | N | young_adult | medium | NA (Urban) | Contemporary, essays |
| `narrator-warm-f` | F | young_adult | medium | NA (General) | Romance, women's fiction |
| `narrator-authority-m` | M | elderly | low | UK (RP) | History, biography |
| `narrator-global-n` | N | middle | medium | African (Nigerian) | World literature |

### 3.2 Genre Specialists (4) — Specific needs

| ID | Gender | Age | Pitch | Texture | Primary Use |
|----|--------|-----|-------|---------|-------------|
| `narrator-thriller` | M | middle | low | crisp | Thriller, suspense, noir |
| `narrator-fantasy` | N | middle | medium | warm | Fantasy, adventure |
| `narrator-childrens` | F | young_adult | high | warm | Picture books, early readers |
| `narrator-comedy` | N | young_adult | medium | smooth | Humor, satire |

### 3.3 Cultural Voices (4) — Accent/language diversity

| ID | Gender | Accent | Languages | Primary Use |
|----|--------|--------|-----------|-------------|
| `narrator-indian` | N | Indian English | en, hi | Indian literature, diaspora |
| `narrator-latinx` | N | American Latinx | en, es | Latinx literature, bilingual |
| `narrator-caribbean` | N | Caribbean | en | Caribbean lit, oral tradition |
| `narrator-british` | M | UK (Regional) | en | British fiction |

### 3.4 Character Voices (3) — Dialogue specialists

| ID | Gender | Age | Texture | Primary Use |
|----|--------|-----|---------|-------------|
| `character-mentor` | M | elderly | gravelly | Wise mentor archetype |
| `character-youth` | N | teen | clear | YA protagonists |
| `character-villain` | N | middle | husky | Antagonists, dark roles |

### 3.5 Coverage Validation

```
Gender:     M=4, F=3, N=10  ✓ All represented
Age:        child=0*, teen=1, young=4, middle=7, elderly=2  ✓ (*handled by childrens)
Pitch:      vlow=0, low=4, med=10, high=1, vhigh=0  ⚠ Expand high range
Accent:     NA=7, UK=2, African=1, Indian=1, Latinx=1, Caribbean=1  ⚠ Add AU/NZ
Languages:  en=17, es=1, hi=1  ⚠ Expand fr, de, zh
```

---

## 4. Story-Persona Compatibility Scoring

### 4.1 Story Metadata (Required)

```json
{
  "genre": ["literary", "thriller", "romance", ...],
  "tone": ["dark", "light", "humorous", "serious"],
  "setting_period": ["contemporary", "historical", "fantasy"],
  "target_audience": ["adult", "ya", "children"],
  "cultural_context": ["american", "british", "indian", ...],
  "language_needs": ["en", "es-phrases", "bilingual"],
  "pov_gender": ["male", "female", "neutral", "mixed"]
}
```

### 4.2 Scoring Algorithm

```python
def compatibility_score(persona: Persona, story: StoryMeta) -> float:
    """Returns 0.0-1.0 compatibility score."""
    score = 0.0
    weights = {
        'genre_match': 0.30,
        'tone_match': 0.20,
        'audience_match': 0.15,
        'cultural_match': 0.15,
        'language_match': 0.10,
        'gender_match': 0.10,
    }

    # Genre affinity (Jaccard similarity)
    genre_overlap = len(persona.use_cases & story.genre)
    genre_union = len(persona.use_cases | story.genre)
    score += weights['genre_match'] * (genre_overlap / max(genre_union, 1))

    # Tone alignment (emotional range coverage)
    tone_emotions = TONE_TO_EMOTIONS[story.tone]
    tone_coverage = len(persona.emotional_range & tone_emotions)
    score += weights['tone_match'] * (tone_coverage / len(tone_emotions))

    # Audience match (binary)
    if story.target_audience in persona.audience_tags:
        score += weights['audience_match']

    # Cultural authenticity (accent/context alignment)
    if persona_matches_culture(persona, story.cultural_context):
        score += weights['cultural_match']

    # Language capability
    if all(lang in persona.languages for lang in story.language_needs):
        score += weights['language_match']

    # Gender preference (soft match)
    if story.pov_gender == 'mixed' or persona.gender == 'neutral':
        score += weights['gender_match']
    elif story.pov_gender == persona.gender:
        score += weights['gender_match']

    return min(score, 1.0)
```

### 4.3 Recommendation Output

```
Top 3 matches for "The Midnight Garden" (literary, dark, contemporary, adult):

1. narrator-literary-m     Score: 0.92  "Deep literary voice, contemplative"
2. narrator-contemporary-n Score: 0.78  "Modern sensibility, flexible tone"
3. narrator-thriller       Score: 0.71  "Handles dark material well"
```

---

## 5. Quality Operations Framework

### 5.1 Three-Tier Validation

| Tier | Scope | Method | Frequency |
|------|-------|--------|-----------|
| **Automated** | 100% | Technical specs (ACX compliance, silence, levels) | Every render |
| **Sampling** | √N×M | Human QC on stratified sample | Weekly |
| **Regression** | Golden set | Compare to reference renders | On persona update |

### 5.2 Automated Checks (Every Render)

```python
QUALITY_GATES = {
    'acx_compliance': True,           # RMS, peak, noise floor
    'no_artifacts': True,             # Click detection, dropout detection
    'consistent_pace': True,          # WPM within persona's range ±15%
    'emotional_coherence': True,      # Sentiment alignment with text
    'pronunciation_check': True,      # Known-word mispronunciation detection
}
```

### 5.3 Sampling Strategy

For N personas × M stories:

```python
def sample_size(n_personas: int, n_stories: int) -> int:
    """Stratified sample size for weekly QC."""
    total_combinations = n_personas * n_stories
    # Sample: at least √(N×M), minimum 50, maximum 500
    return min(500, max(50, int(total_combinations ** 0.5)))

def stratified_sample(personas, stories, sample_size):
    """Ensure each persona and genre represented in sample."""
    samples = []
    # 1. One sample per persona (covers persona diversity)
    for p in personas:
        samples.append((p, random.choice(stories)))
    # 2. One sample per genre (covers content diversity)
    for genre in GENRES:
        genre_stories = [s for s in stories if genre in s.genres]
        if genre_stories:
            samples.append((random.choice(personas), random.choice(genre_stories)))
    # 3. Random fill to sample_size
    while len(samples) < sample_size:
        samples.append((random.choice(personas), random.choice(stories)))
    return samples[:sample_size]
```

### 5.4 Regression Testing

Each persona has a **golden reference**:
- 3 passages: narrative, dialogue, emotional peak
- Reference audio rendered at persona creation
- Any persona update triggers comparison

```python
def regression_test(persona_id: str) -> bool:
    """Compare current render to golden reference."""
    golden = load_golden_reference(persona_id)
    current = render_test_passages(persona_id)

    metrics = {
        'mel_spectrogram_similarity': compare_mel(golden, current),  # ≥0.85
        'pitch_contour_correlation': compare_pitch(golden, current), # ≥0.90
        'pace_variance': compare_pace(golden, current),              # ≤10%
    }

    return all(v >= threshold for v, threshold in metrics.items())
```

---

## 6. Consistency Enforcement

### 6.1 Persona Versioning

```
personas/
  examples/
    narrator-literary-m.json      # Current version
  versions/
    narrator-literary-m/
      v1.0.0.json                  # Initial release
      v1.1.0.json                  # Updated voice_prompt
      changelog.md                 # What changed and why
  golden/
    narrator-literary-m/
      narrative.wav                # Reference render
      dialogue.wav
      emotional.wav
      metadata.json                # Render settings, date, model version
```

### 6.2 Immutable Renders

Once a story is rendered with a persona version, that combination is locked:
- User sees "Narrated by Literary Voice v1.2"
- Re-renders use same persona version unless user opts for upgrade
- Prevents "voice drift" for returning listeners

### 6.3 A/B Testing Protocol

New persona versions require validation:

```python
AB_TEST_CONFIG = {
    'sample_size': 100,           # Listeners per variant
    'metrics': ['preference', 'comprehension', 'engagement'],
    'significance_threshold': 0.05,
    'minimum_improvement': 0.10,  # 10% better to ship
}
```

---

## 7. Scaling Projections

| Personas | Stories | Combinations | Sample QC/week | Automated QC |
|----------|---------|--------------|----------------|--------------|
| 15 | 100 | 1,500 | 50 | 1,500 |
| 15 | 1,000 | 15,000 | 122 | 15,000 |
| 20 | 10,000 | 200,000 | 447 | 200,000 |
| 25 | 100,000 | 2,500,000 | 1,581 | 2,500,000 |

**Cost model**: Automated QC is cheap (compute). Human QC scales as √(N×M).

---

## 8. Implementation Phases

### Phase 1: Foundation (Complete)
- [x] 19 personas with cultural diversity
- [x] Schema supporting natural language
- [x] Add 10 personas for coverage gaps (P1 + P2 + P3 complete)
- [x] Implement compatibility scoring (`scripts/persona_compatibility.py`)

### Phase 2: Quality Ops (Planned)
- [ ] Automated QC pipeline
- [ ] Golden reference creation for all personas
- [x] Regression test framework (`scripts/persona_regression.py`)

### Phase 3: Scale (Planned)
- [ ] Persona versioning system
- [ ] A/B testing infrastructure
- [ ] Sampling QC dashboard

### Phase 4: Optimization (Planned)
- [ ] User preference learning
- [ ] Dynamic persona recommendation
- [ ] Custom persona generation (voice cloning tier)

---

## 9. Implementation Files

All foundation files exist:

| File | Purpose | Status |
|------|---------|--------|
| `personas/taxonomy.md` | Dimensional framework reference | Complete |
| `personas/library-status.md` | Coverage tracking | Complete |
| `scripts/persona_compatibility.py` | Story-persona scoring | Complete |
| `scripts/persona_regression.py` | Regression testing + golden reference comparison | Complete |

---

## 10. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Coverage | ≥80% preference space | Taxonomy gap analysis |
| Consistency | ≤5% regression failures | Automated regression tests |
| Quality | ≥95% ACX pass rate | Automated validation |

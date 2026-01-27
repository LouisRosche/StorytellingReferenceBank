# Voice Persona Taxonomy

Mathematical framework for dimensional coverage and optimization.

---

## Dimensional Space

### Primary Dimensions

| Dim | Symbol | Values | Weight |
|-----|--------|--------|--------|
| Gender | G | {M, F, N, A} | 0.15 |
| Age | A | {child, teen, young, middle, elder} | 0.15 |
| Pitch | P | {vlow, low, med, high, vhigh} | 0.10 |
| Pace | S | {vslow, slow, med, fast, vfast} | 0.10 |
| Texture | T | {smooth, warm, breathy, husky, gravelly, crisp} | 0.15 |
| Accent | R | {NA, UK, AU, AF, IN, CA, EU, AS} | 0.20 |
| Language | L | {en, es, fr, de, zh, ja, ko, pt, ru, it} | 0.15 |

### Similarity Function

```
sim(p1, p2) = Σ(wi × match(p1.di, p2.di)) / Σwi

where:
  match(v1, v2) = 1.0 if v1 == v2
                = 0.5 if adjacent(v1, v2)  # e.g., low/medium
                = 0.0 otherwise
```

### Redundancy Threshold

Personas with `sim(p1, p2) > 0.70` are redundant. Consolidate or differentiate.

---

## Coverage Matrix

### Current Library (9 personas)

```
         | G   | A      | P    | S      | T        | R   | L     |
---------|-----|--------|------|--------|----------|-----|-------|
mentor   | M   | elder  | low  | slow   | gravelly | UK  | en    |
children | F   | young  | med  | med    | warm     | NA  | en    |
literary | M   | middle | low  | slow   | warm     | NA  | en    |
indian   | N   | middle | med  | med    | warm     | IN  | en,hi |
latinx   | N   | young  | med  | med    | warm     | NA  | en,es |
elder    | N   | elder  | low  | slow   | warm     | -   | en    |
global   | N   | middle | med  | med    | warm     | AF  | en    |
nonbin   | N   | young  | med  | med    | clear    | NA  | en    |
caribb   | N   | middle | med  | slow   | warm     | CA  | en    |
```

### Coverage Gaps

| Dimension | Missing Values | Priority |
|-----------|----------------|----------|
| Gender | F (only 1/9) | HIGH |
| Age | teen, child | MEDIUM |
| Pitch | vlow, high, vhigh | MEDIUM |
| Pace | fast, vfast | LOW |
| Texture | smooth, breathy, husky | MEDIUM |
| Accent | AU, EU, AS | MEDIUM |
| Language | fr, de, zh, ja, ko, pt, ru, it | HIGH |

---

## Expansion Plan

### +6 Personas for 80% Coverage

| ID | G | A | P | T | R | L | Fills Gap |
|----|---|---|---|---|---|---|-----------|
| `narrator-literary-f` | F | middle | med | warm | NA | en | Gender |
| `narrator-warm-f` | F | young | med | smooth | NA | en | Gender, Texture |
| `narrator-thriller` | M | middle | low | crisp | NA | en | Texture |
| `narrator-british` | M | middle | med | crisp | UK | en | Accent variety |
| `narrator-french` | N | middle | med | smooth | EU | en,fr | Language |
| `character-teen` | N | teen | high | clear | NA | en | Age, Pitch |

### Post-Expansion Coverage

```
Gender:   M=4 F=3 N=8  → Balanced
Age:      teen=1 young=4 middle=7 elder=2 → Full range
Pitch:    low=4 med=9 high=1 → Improved
Texture:  warm=6 crisp=2 clear=2 smooth=2 gravelly=1 → Diversified
Accent:   NA=8 UK=2 AF=1 IN=1 CA=1 EU=1 → +European
Language: en=15 es=1 hi=1 fr=1 → +French
```

---

## Compatibility Vectors

### Genre Affinity Tags

```yaml
literary:    [contemplative, melancholic, wry, tender, grave]
thriller:    [tense, urgent, controlled, cold, sharp]
romance:     [warm, tender, passionate, playful, longing]
fantasy:     [wonder, mysterious, heroic, ancient, magical]
horror:      [dread, whispered, unsettling, cold, creeping]
comedy:      [wry, playful, timing, absurd, deadpan]
children:    [warm, excited, gentle, playful, soothing]
memoir:      [intimate, reflective, honest, vulnerable, wry]
```

### Tone-Emotion Mapping

```yaml
dark:        [grave, melancholic, cold, dread, unsettling]
light:       [warm, playful, gentle, bright, hopeful]
serious:     [contemplative, grave, measured, honest, weighty]
humorous:    [wry, playful, absurd, timing, deadpan]
intimate:    [tender, vulnerable, honest, warm, quiet]
epic:        [heroic, ancient, vast, wonder, grave]
```

---

## Validation Formulas

### Library Diversity Score

```
diversity = (unique_values_used / total_possible_values) × 100

Current: (28 / 48) × 100 = 58%
Target:  ≥75%
```

### Redundancy Index

```
redundancy = count(pairs where sim > 0.70) / total_pairs

Current: 3 / 36 = 8.3%
Target:  ≤10%
```

### User Preference Coverage

```
coverage = users_finding_acceptable_match / total_users

Measured via: Survey "Was a voice available that suited your project?"
Target: ≥80%
```

---

## Maintenance Protocol

1. **Quarterly Review**: Calculate coverage and redundancy metrics
2. **Gap Analysis**: Identify top 3 unfilled demand areas from user requests
3. **Expansion Decision**: Add persona if demand > 5% of requests AND coverage < 80%
4. **Deprecation Decision**: Remove persona if usage < 1% AND redundancy > 70% with another

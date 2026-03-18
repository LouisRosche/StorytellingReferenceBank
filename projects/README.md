# Projects

Active works at various production stages.

| Project | Genre | Speakers | Chapters | Status |
|---------|-------|----------|----------|--------|
| `luna-the-little-cloud` | Children's picture book | 5 (narrator, luna, flower, bee, storm_clouds) | Full manuscript | Production-tested |
| `the-weight-of-mangoes` | Literary fiction (ensemble) | 9 (Indo-Caribbean family saga) | 2 chapters | In development |
| `the-listener` | Psychological thriller | 9 (therapist, patient, supporting) | 34 chapters | Complete draft |
| `the-house-remains` | Literary drama | 8 (family reunion, multi-generational) | 2 chapters | In development |

## Structure

Each project follows:

```
projects/[name]/
├── drafts/              # Manuscript files (chapter-NN.txt)
├── story-bible/
│   └── characters/      # Character sheets with TTS Persona Links
├── personas/            # Voice persona JSON files
└── speaker-map.json     # Speaker → persona routing
```

## Reference Examples

**Multi-speaker children's book**: `luna-the-little-cloud` — production-tested pipeline with prose-style dialogue parsing, 5 personas, speaker map.

**Tagged multi-speaker**: `the-house-remains` and `the-weight-of-mangoes` — `[SPEAKER]` format with 7-9 voices.

**Full-length thriller**: `the-listener` — 34-chapter complete draft with dual POV and 9 speakers.

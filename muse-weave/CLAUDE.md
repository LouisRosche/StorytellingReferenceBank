# Muse Weave

Narrative deckbuilder roguelite. Five Muses, Hero's Journey mapped to Jo-ha-kyū, storytelling-driven combat.

## Architecture

TypeScript monorepo (pnpm workspaces + Turborepo). One language, one type system.

```
packages/
  shared/        # Types: MuseType, CardData, CombatState, GameConfig, constants
  engine/        # Pure TS game logic — zero framework deps, 166 tests
  client/        # Phaser 3 scenes (Boot, Map, Combat) — stub scaffolds
apps/
  web/           # Next.js shell with GameCanvas component
unity/           # Legacy Unity project (reference only, superseded by Phaser)
narrative/       # Storytelling craft references extracted from StorytellingReferenceBank
audio/           # Voice personas, ACX specs, sound design
```

## Commands

```bash
pnpm install                              # Install all deps
pnpm --filter @deckbuilder/engine test    # Run engine tests (vitest)
pnpm --filter @deckbuilder/shared build   # Build shared types
pnpm --filter @deckbuilder/web dev        # Start Next.js dev server
```

## The Five Muses

Pentagon counter system — each Muse beats 2, loses to 2:

```
Trickster → Sovereign → Oracle → Wanderer → Martyr → Trickster  (adjacent: 1.3x)
Trickster → Oracle, Sovereign → Wanderer, etc.                   (cross: 1.15x)
```

Each Muse has: keywords, narrative identity, card archetypes, rarity scaling curves.

## Journey System

Hero's Journey phases mapped to Jo-ha-kyū:
- **Jo** (floors 1–4): Ordinary World → Call → Threshold. Pacing 0.8x.
- **Ha** (floors 5–9): Trials → Ordeal. Pacing 1.0x. Mid-boss floor 9.
- **Kyū** (floors 10–13): Apotheosis → Return. Pacing 1.3x. Final boss floor 13.

Floor 2 = Muse selection. Motif rewards unlock at floor 5+.

## Engine Design

- **Combat**: Finite state machine + command pattern (full undo). States: draw → play → enemy → cleanup.
- **Cards**: Seeded PRNG deck. EffectResolver dispatches CardEffect → commands.
- **Map**: Slay-the-Spire DAG generator. Room weights, crossing-edge prevention, seed determinism.
- **Affinity**: Commitment ratio (focused vs scattered play). Rarity scaling: common (0→0.15), uncommon (0.1→0.4), rare (0.2→0.7), legendary (0.3→1.0).

## Narrative Reference Library → `narrative/`

Extracted from the StorytellingReferenceBank. Informs game writing, card flavor, event text, Muse characterization.

| Directory | Contents |
|-----------|----------|
| `narrative/craft/` | Lasting work principles, master techniques, dialogue craft, common pitfalls, voice vocabulary |
| `narrative/structures/` | Three-Act, Save the Cat, Scene-Sequel, Kishotenketsu, Rasa/Jo-ha-kyū/Griot |
| `narrative/characters/` | Character + antagonist sheet templates |
| `narrative/worlds/` | World-building framework |
| `narrative/genres/` | Genre conventions (all genres + children's picture books) |
| `narrative/series/` | Series bible template |

## Audio Reference Library → `audio/`

Voice persona system and production specs for narrated game content.

| Directory | Contents |
|-----------|----------|
| `audio/personas/` | 19 persona JSONs, schema, taxonomy, golden test passages |
| `audio/specs/` | ACX requirements, sound design cue format |
| `audio/docs/` | Sound design architecture, tool evaluation, voice cloning workflow |

## Principles

- **Direct and forthright.** No hedging.
- **No safe writing.** The game's narrative should take risks.
- **Style varies by Muse.** Each archetype has its own voice and card language.
- Engine code is pure TypeScript — no framework deps, fully testable.
- Client scenes are stubs. Build incrementally.

## Iteration Targets

Current scaffold. Next priorities:
1. Wire engine into Phaser scenes (CombatScene ↔ StateMachine)
2. Add shared types: RunState, EnemyTemplate, CardChoice
3. Card data: starter decks per Muse, enemy encounter definitions
4. Map scene: render DAG, node selection, floor progression
5. Combat scene: hand display, card play, turn resolution, enemy AI

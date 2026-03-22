/**
 * The Five Muses — narrative archetypes that shape deck identity.
 *
 * Each Muse maps to a storytelling tradition:
 *   Trickster  → Folklore/Fable (Anansi, Loki, Coyote)
 *   Sovereign  → Epic/Dynasty (Gilgamesh, Arthur, Sundiata)
 *   Oracle     → Prophecy/Mystery (Cassandra, Tiresias, the Norns)
 *   Wanderer   → Picaresque/Odyssey (Odysseus, Xuanzang, Ibn Battuta)
 *   Martyr     → Tragedy/Sacrifice (Prometheus, Antigone, Karna)
 */
export type MuseType =
  | "trickster"
  | "sovereign"
  | "oracle"
  | "wanderer"
  | "martyr";

export const MUSE_TYPES = [
  "trickster",
  "sovereign",
  "oracle",
  "wanderer",
  "martyr",
] as const;

/** Signature mechanic keyword per Muse. */
export type MuseKeyword =
  | "redirect"
  | "decree"
  | "foresight"
  | "forage"
  | "offering";

export const MUSE_KEYWORDS: Record<MuseType, MuseKeyword> = {
  trickster: "redirect",
  sovereign: "decree",
  oracle: "foresight",
  wanderer: "forage",
  martyr: "offering",
};

/**
 * Muse favor tiers earned during a run.
 * Each tier unlocks a passive ability from the Muse.
 */
export type MuseFavorTier = 0 | 1 | 2 | 3;

export interface MuseFavorState {
  muse: MuseType;
  /** Raw favor points accumulated this run. */
  favor: number;
  /** Current tier (derived from favor thresholds). */
  tier: MuseFavorTier;
}

/**
 * Hero's Journey phases mapped to roguelite run structure.
 *
 * Jo (序) — Floors 1-4: Call to Adventure, choose Muse, build foundation.
 * Ha (破) — Floors 5-9: Road of Trials, commitment tested, mid-boss Ordeal.
 * Kyū (急) — Floors 10-13: Apotheosis, deck crystallized, final boss.
 */
export type JourneyPhase =
  | "ordinary_world"
  | "call_to_adventure"
  | "crossing_threshold"
  | "road_of_trials"
  | "the_ordeal"
  | "apotheosis"
  | "the_return";

export type JourneyAct = "jo" | "ha" | "kyu";

/**
 * Motif — a persistent run modifier that sits outside the draw pile.
 * Inspired by Balatro's Joker system. Earned through meta-progression.
 *
 * A literary motif is a recurring element that carries thematic weight.
 * In-game, Motifs are recurring modifiers that shape every hand you play.
 */
export interface MotifData {
  id: string;
  name: string;
  description: string;
  muse: MuseType;
  rarity: import("./card").CardRarity;
  /** Passive effect applied every turn or on specific triggers. */
  effectType: string;
  effectValue: number;
  /** Trigger condition (e.g., "on_redirect", "on_turn_start", "on_hp_loss"). */
  trigger: string;
}

/** Maximum motif slots per run. */
export const MAX_MOTIF_SLOTS = 3;

/** Favor thresholds to reach each tier. */
export const FAVOR_TIER_THRESHOLDS: Record<MuseFavorTier, number> = {
  0: 0,
  1: 5,
  2: 12,
  3: 20,
};

/**
 * Meta-progression: lifetime stats per Muse across all runs.
 */
export interface MuseLifetimeProgress {
  muse: MuseType;
  /** Total runs started with this Muse. */
  runsStarted: number;
  /** Total runs completed (reached final boss). */
  runsCompleted: number;
  /** Highest favor tier reached in any single run. */
  highestTier: MuseFavorTier;
  /** Total affinity accumulated across all runs. */
  lifetimeAffinity: number;
  /** Unlocked motif IDs. */
  unlockedMotifs: string[];
  /** Unlocked card IDs (added to archetype draft pool). */
  unlockedCards: string[];
}

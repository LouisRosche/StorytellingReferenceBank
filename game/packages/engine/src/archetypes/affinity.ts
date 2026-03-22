import type { MuseType, CardRarity } from "@deckbuilder/shared";
import { MUSE_TYPES } from "@deckbuilder/shared";

const MAX_AFFINITY_FOR_SCALING = 30;

/**
 * Per-run archetype commitment tracker.
 * Rarity is not power — it is synergy ceiling potential.
 * Commons work everywhere. Legendaries are devastating with commitment, mediocre without.
 */
export class MuseAffinity {
  private scores: Map<MuseType, number>;

  constructor() {
    this.scores = new Map();
    for (const muse of MUSE_TYPES) {
      this.scores.set(muse, 0);
    }
  }

  /** Add affinity toward a Muse. Called when drafting cards, choosing paths, etc. */
  addAffinity(muse: MuseType, amount: number): void {
    if (amount <= 0) return;
    this.scores.set(muse, (this.scores.get(muse) ?? 0) + amount);
  }

  /** Get raw affinity score for a Muse. */
  getScore(muse: MuseType): number {
    return this.scores.get(muse) ?? 0;
  }

  /** Get total affinity across all Muses. */
  getTotal(): number {
    let total = 0;
    for (const score of this.scores.values()) {
      total += score;
    }
    return total;
  }

  /** Returns the Muse with the highest accumulated affinity. Ties broken by MUSE_TYPES order. */
  getDominant(): MuseType {
    let dominant: MuseType = "trickster";
    let highest = -1;
    for (const [muse, score] of this.scores) {
      if (score > highest) {
        highest = score;
        dominant = muse;
      }
    }
    return dominant;
  }

  /**
   * Commitment ratio [0..1] for a given Muse.
   * Uses geometric mean of depth (raw score / max) and focus (score / total).
   * Scattered builds yield low ratios. Committed builds yield high ratios.
   */
  getCommitmentRatio(muse: MuseType): number {
    const raw = this.scores.get(muse) ?? 0;
    const total = this.getTotal();
    if (total === 0) return 0;

    const depthRatio = clamp01(raw / MAX_AFFINITY_FOR_SCALING);
    const focusRatio = raw / total;

    return clamp01(Math.sqrt(depthRatio * focusRatio));
  }

  /** Get the synergy multiplier for a card based on its rarity and current commitment. */
  getSynergyMultiplier(rarity: CardRarity, muse: MuseType): number {
    const t = this.getCommitmentRatio(muse);
    return calculateRarityMultiplier(rarity, t);
  }

  /** Get all scores as a plain object (for serialization). */
  toJSON(): Record<MuseType, number> {
    const result = {} as Record<MuseType, number>;
    for (const [muse, score] of this.scores) {
      result[muse] = score;
    }
    return result;
  }

  /** Restore from serialized state. */
  static fromJSON(data: Record<MuseType, number>): MuseAffinity {
    const affinity = new MuseAffinity();
    for (const muse of MUSE_TYPES) {
      if (data[muse] !== undefined) {
        affinity.scores.set(muse, data[muse]);
      }
    }
    return affinity;
  }
}

/**
 * Rarity-as-ceiling scaling curves.
 *   Common:    1.0 – 1.15  (always reliable)
 *   Uncommon:  0.9 – 1.4   (slight penalty at zero, solid at commitment)
 *   Rare:      0.7 – 1.8   (weak without synergy, very strong with it)
 *   Legendary: 0.5 – 2.5   (actively bad uncommitted, game-warping when fully committed)
 */
export function calculateRarityMultiplier(rarity: CardRarity, commitmentRatio: number): number {
  const t = clamp01(commitmentRatio);
  switch (rarity) {
    case "common":    return 1.0 + t * 0.15;
    case "uncommon":  return 0.9 + t * 0.5;
    case "rare":      return 0.7 + t * 1.1;
    case "legendary": return 0.5 + t * 2.0;
    default:          return 1.0;
  }
}

/** Calculate effective power of a card given base value, rarity, and commitment. */
export function calculateEffectivePower(
  baseValue: number,
  rarity: CardRarity,
  commitmentRatio: number,
): number {
  const mult = calculateRarityMultiplier(rarity, commitmentRatio);
  const result = Math.round(baseValue * mult);
  return result < 0 ? 0 : result;
}

function clamp01(value: number): number {
  if (value < 0) return 0;
  if (value > 1) return 1;
  return value;
}

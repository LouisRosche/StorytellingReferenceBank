import type { MuseType, MuseFavorTier, MuseFavorState } from "@deckbuilder/shared";
import { MUSE_TYPES, FAVOR_TIER_THRESHOLDS } from "@deckbuilder/shared";

/**
 * Tracks Muse favor earned during a single run.
 * Favor is earned by playing Muse-aligned cards, choosing aligned paths, etc.
 * Higher tiers unlock passive Muse abilities.
 */
export class MuseFavorTracker {
  private favorMap: Map<MuseType, number>;

  constructor() {
    this.favorMap = new Map();
    for (const muse of MUSE_TYPES) {
      this.favorMap.set(muse, 0);
    }
  }

  /** Add favor toward a Muse. */
  addFavor(muse: MuseType, amount: number): void {
    if (amount <= 0) return;
    this.favorMap.set(muse, (this.favorMap.get(muse) ?? 0) + amount);
  }

  /** Get raw favor for a Muse. */
  getFavor(muse: MuseType): number {
    return this.favorMap.get(muse) ?? 0;
  }

  /** Get the current tier for a Muse based on accumulated favor. */
  getTier(muse: MuseType): MuseFavorTier {
    const favor = this.getFavor(muse);
    if (favor >= FAVOR_TIER_THRESHOLDS[3]) return 3;
    if (favor >= FAVOR_TIER_THRESHOLDS[2]) return 2;
    if (favor >= FAVOR_TIER_THRESHOLDS[1]) return 1;
    return 0;
  }

  /** Get the Muse with the highest favor. */
  getDominantMuse(): MuseType {
    let dominant: MuseType = "trickster";
    let highest = -1;
    for (const [muse, favor] of this.favorMap) {
      if (favor > highest) {
        highest = favor;
        dominant = muse;
      }
    }
    return dominant;
  }

  /** Get full state for a specific Muse. */
  getState(muse: MuseType): MuseFavorState {
    return {
      muse,
      favor: this.getFavor(muse),
      tier: this.getTier(muse),
    };
  }

  /** Get states for all Muses. */
  getAllStates(): MuseFavorState[] {
    return MUSE_TYPES.map((muse) => this.getState(muse));
  }

  /** Serialize. */
  toJSON(): Record<MuseType, number> {
    const result = {} as Record<MuseType, number>;
    for (const [muse, favor] of this.favorMap) {
      result[muse] = favor;
    }
    return result;
  }

  /** Deserialize. */
  static fromJSON(data: Record<MuseType, number>): MuseFavorTracker {
    const tracker = new MuseFavorTracker();
    for (const muse of MUSE_TYPES) {
      if (data[muse] !== undefined) {
        tracker.favorMap.set(muse, data[muse]);
      }
    }
    return tracker;
  }
}

/** Favor-per-action defaults. */
export const FAVOR_GRANTS = {
  /** Favor gained when playing a Muse-aligned card. */
  playAlignedCard: 1,
  /** Favor gained when choosing a Muse-aligned path on the map. */
  chooseAlignedPath: 2,
  /** Favor gained when winning a combat with dominant Muse alignment. */
  winCombatAligned: 3,
  /** Favor gained from Muse-specific events. */
  museEvent: 4,
} as const;

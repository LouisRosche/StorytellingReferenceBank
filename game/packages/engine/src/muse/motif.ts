import type { MotifData, MuseType, CardRarity } from "@deckbuilder/shared";
import { MAX_MOTIF_SLOTS } from "@deckbuilder/shared";

/**
 * Manages active Motifs for a run.
 * Motifs sit beside the deck — always active, never drawn or played.
 * They modify how the archetype plays (e.g., "Redirects also draw 1 card").
 */
export class MotifManager {
  private activeMotifs: MotifData[] = [];

  /** Try to add a motif. Returns false if slots are full. */
  addMotif(motif: MotifData): boolean {
    if (this.activeMotifs.length >= MAX_MOTIF_SLOTS) {
      return false;
    }
    this.activeMotifs.push(motif);
    return true;
  }

  /** Remove a motif by ID. Returns the removed motif or null. */
  removeMotif(motifId: string): MotifData | null {
    const idx = this.activeMotifs.findIndex((m) => m.id === motifId);
    if (idx === -1) return null;
    return this.activeMotifs.splice(idx, 1)[0];
  }

  /** Replace a motif at the given slot index. Returns the replaced motif. */
  replaceMotif(slotIndex: number, newMotif: MotifData): MotifData | null {
    if (slotIndex < 0 || slotIndex >= this.activeMotifs.length) return null;
    const old = this.activeMotifs[slotIndex];
    this.activeMotifs[slotIndex] = newMotif;
    return old;
  }

  /** Get all active motifs. */
  getActive(): readonly MotifData[] {
    return this.activeMotifs;
  }

  /** Get motifs that match a specific trigger. */
  getByTrigger(trigger: string): MotifData[] {
    return this.activeMotifs.filter((m) => m.trigger === trigger);
  }

  /** Get motifs for a specific Muse. */
  getByMuse(muse: MuseType): MotifData[] {
    return this.activeMotifs.filter((m) => m.muse === muse);
  }

  /** Current slot count. */
  get slotCount(): number {
    return this.activeMotifs.length;
  }

  /** Remaining available slots. */
  get slotsAvailable(): number {
    return MAX_MOTIF_SLOTS - this.activeMotifs.length;
  }

  /** Serialize. */
  toJSON(): MotifData[] {
    return [...this.activeMotifs];
  }

  /** Deserialize. */
  static fromJSON(data: MotifData[]): MotifManager {
    const manager = new MotifManager();
    for (const motif of data) {
      manager.addMotif(motif);
    }
    return manager;
  }
}

/**
 * Determines which rarity of Motif is earned based on run performance.
 * - Survive to Act 2 (floor 5+): Common
 * - Beat mid-boss (floor 9+): Uncommon
 * - Complete the run: Rare
 * - Complete with high commitment (ratio > 0.7): Legendary
 */
export function determineMotifReward(
  floorReached: number,
  runCompleted: boolean,
  commitmentRatio: number,
): CardRarity | null {
  if (floorReached < 5) return null; // didn't make it to Act 2
  if (runCompleted && commitmentRatio > 0.7) return "legendary";
  if (runCompleted) return "rare";
  if (floorReached >= 9) return "uncommon";
  return "common";
}

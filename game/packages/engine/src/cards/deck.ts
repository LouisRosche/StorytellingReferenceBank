/**
 * Deck management system.
 * Handles draw pile, discard pile, hand, and exhaust pile.
 * Uses a seeded PRNG for deterministic shuffles (critical for replays / PvP).
 */

import type { IDeckManager } from "../combat/commands";

// ---------------------------------------------------------------------------
// Seeded random — simple mulberry32 PRNG.
// ---------------------------------------------------------------------------

export type SeededRandom = () => number;

/**
 * Create a seeded PRNG (mulberry32). Returns values in [0, 1).
 * Deterministic: same seed always produces the same sequence.
 */
export function createSeededRandom(seed: number): SeededRandom {
  let s = seed | 0;
  return (): number => {
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ---------------------------------------------------------------------------
// Fisher-Yates shuffle using a seeded RNG.
// ---------------------------------------------------------------------------

function shuffle<T>(arr: T[], rng: SeededRandom): T[] {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

// ---------------------------------------------------------------------------
// Deck class.
// ---------------------------------------------------------------------------

export class Deck implements IDeckManager {
  readonly drawPile: string[] = [];
  readonly discardPile: string[] = [];
  readonly hand: string[] = [];
  readonly exhaustPile: string[] = [];

  private readonly rng: SeededRandom;

  constructor(cardIds: string[], seed: number) {
    this.drawPile = [...cardIds];
    this.rng = createSeededRandom(seed);
    this.shuffleDrawPile();
  }

  /** Draw `count` cards from the draw pile into the hand. */
  draw(count: number): void {
    for (let i = 0; i < count; i++) {
      if (this.drawPile.length === 0) {
        this.shuffleDiscardIntoDraw();
        if (this.drawPile.length === 0) break; // deck is totally empty
      }
      const card = this.drawPile.pop()!;
      this.hand.push(card);
    }
  }

  /** Move a card from the hand to the discard pile. */
  discard(cardId: string): void {
    const idx = this.hand.indexOf(cardId);
    if (idx === -1) return;
    this.hand.splice(idx, 1);
    this.discardPile.push(cardId);
  }

  /** Remove a card from the hand permanently (exhaust). */
  exhaust(cardId: string): void {
    const idx = this.hand.indexOf(cardId);
    if (idx === -1) return;
    this.hand.splice(idx, 1);
    this.exhaustPile.push(cardId);
  }

  /** Shuffle the draw pile in place. */
  shuffleDrawPile(): void {
    shuffle(this.drawPile, this.rng);
  }

  /** Move all cards from discard into draw, then shuffle. */
  shuffleDiscardIntoDraw(): void {
    this.drawPile.push(...this.discardPile);
    this.discardPile.length = 0;
    this.shuffleDrawPile();
  }

  /** Discard the entire hand. Typically called at end of turn. */
  discardHand(): void {
    this.discardPile.push(...this.hand);
    this.hand.length = 0;
  }
}

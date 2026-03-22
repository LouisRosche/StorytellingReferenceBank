import { describe, it, expect } from "vitest";
import { Deck, createSeededRandom } from "../src/cards/deck";
import { EffectResolver, type EffectContext } from "../src/cards/effects";
import {
  CommandInvoker,
  type ICombatEntity,
  type IDeckManager,
} from "../src/combat/commands";
import type { CardEffect } from "@deckbuilder/shared";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeCombatEntity(hp: number, maxHp: number, block = 0): ICombatEntity & {
  _statuses: Map<string, number>;
} {
  const statuses = new Map<string, number>();
  return {
    hp,
    maxHp,
    block,
    addStatusEffect(effectId: string, stacks: number) {
      statuses.set(effectId, (statuses.get(effectId) ?? 0) + stacks);
    },
    removeStatusEffect(effectId: string, stacks: number) {
      const current = statuses.get(effectId) ?? 0;
      const newVal = current - stacks;
      if (newVal <= 0) {
        statuses.delete(effectId);
      } else {
        statuses.set(effectId, newVal);
      }
    },
    _statuses: statuses,
  };
}

function makeEffectContext(overrides?: Partial<EffectContext>): EffectContext {
  return {
    invoker: new CommandInvoker(),
    source: makeCombatEntity(50, 100),
    target: makeCombatEntity(50, 100),
    deck: { draw: () => {}, discard: () => {}, exhaust: () => {} } as IDeckManager,
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Deck
// ---------------------------------------------------------------------------

describe("Deck", () => {
  const CARDS = ["a", "b", "c", "d", "e"];

  it("initializes with all cards in draw pile (shuffled)", () => {
    const deck = new Deck(CARDS, 42);
    // All 5 cards should be in the draw pile
    expect(deck.drawPile).toHaveLength(5);
    expect(deck.hand).toHaveLength(0);
    expect(deck.discardPile).toHaveLength(0);
    expect(deck.exhaustPile).toHaveLength(0);
    // All original cards should be present
    expect([...deck.drawPile].sort()).toEqual([...CARDS].sort());
  });

  it("draw moves cards from draw pile to hand", () => {
    const deck = new Deck(CARDS, 42);
    deck.draw(3);
    expect(deck.hand).toHaveLength(3);
    expect(deck.drawPile).toHaveLength(2);
  });

  it("discard moves a card from hand to discard pile", () => {
    const deck = new Deck(CARDS, 42);
    deck.draw(3);
    const cardInHand = deck.hand[0];
    deck.discard(cardInHand);
    expect(deck.hand).toHaveLength(2);
    expect(deck.discardPile).toContain(cardInHand);
  });

  it("discard does nothing for a card not in hand", () => {
    const deck = new Deck(CARDS, 42);
    deck.draw(2);
    const handBefore = [...deck.hand];
    deck.discard("nonexistent");
    expect(deck.hand).toEqual(handBefore);
  });

  it("exhaust moves a card from hand to exhaust pile", () => {
    const deck = new Deck(CARDS, 42);
    deck.draw(3);
    const cardInHand = deck.hand[0];
    deck.exhaust(cardInHand);
    expect(deck.hand).toHaveLength(2);
    expect(deck.exhaustPile).toContain(cardInHand);
  });

  it("shuffleDiscardIntoDraw moves all discard back and empties discard", () => {
    const deck = new Deck(CARDS, 42);
    deck.draw(5);
    // Discard all from hand
    const drawn = [...deck.hand];
    for (const c of drawn) {
      deck.discard(c);
    }
    expect(deck.discardPile).toHaveLength(5);
    expect(deck.drawPile).toHaveLength(0);

    deck.shuffleDiscardIntoDraw();
    expect(deck.drawPile).toHaveLength(5);
    expect(deck.discardPile).toHaveLength(0);
  });

  it("draw automatically reshuffles discard when draw pile is empty", () => {
    const deck = new Deck(["a", "b", "c"], 42);
    deck.draw(3); // draw all
    const drawn = [...deck.hand];
    for (const c of drawn) {
      deck.discard(c);
    }
    expect(deck.drawPile).toHaveLength(0);
    expect(deck.discardPile).toHaveLength(3);

    // Drawing should trigger reshuffle
    deck.draw(2);
    expect(deck.hand).toHaveLength(2);
    expect(deck.drawPile).toHaveLength(1);
    expect(deck.discardPile).toHaveLength(0);
  });

  it("discardHand moves entire hand to discard pile", () => {
    const deck = new Deck(CARDS, 42);
    deck.draw(3);
    expect(deck.hand).toHaveLength(3);
    deck.discardHand();
    expect(deck.hand).toHaveLength(0);
    expect(deck.discardPile).toHaveLength(3);
  });

  describe("seeded shuffle determinism", () => {
    it("same seed produces same draw order", () => {
      const deck1 = new Deck([...CARDS], 12345);
      const deck2 = new Deck([...CARDS], 12345);

      deck1.draw(5);
      deck2.draw(5);

      expect(deck1.hand).toEqual(deck2.hand);
    });

    it("different seeds produce different draw orders", () => {
      const deck1 = new Deck([...CARDS], 12345);
      const deck2 = new Deck([...CARDS], 99999);

      deck1.draw(5);
      deck2.draw(5);

      // With 5! = 120 permutations, two different seeds almost certainly differ
      // But we can't guarantee it, so we just check both have valid cards
      expect([...deck1.hand].sort()).toEqual([...CARDS].sort());
      expect([...deck2.hand].sort()).toEqual([...CARDS].sort());

      // Extremely unlikely to match — but not impossible. This is a pragmatic check.
      // If this flakes, pick different seeds.
      expect(deck1.hand).not.toEqual(deck2.hand);
    });
  });
});

describe("createSeededRandom", () => {
  it("is deterministic — same seed gives same sequence", () => {
    const rng1 = createSeededRandom(42);
    const rng2 = createSeededRandom(42);

    const seq1 = Array.from({ length: 10 }, () => rng1());
    const seq2 = Array.from({ length: 10 }, () => rng2());

    expect(seq1).toEqual(seq2);
  });

  it("produces values in [0, 1)", () => {
    const rng = createSeededRandom(42);
    for (let i = 0; i < 100; i++) {
      const val = rng();
      expect(val).toBeGreaterThanOrEqual(0);
      expect(val).toBeLessThan(1);
    }
  });
});

// ---------------------------------------------------------------------------
// EffectResolver
// ---------------------------------------------------------------------------

describe("EffectResolver", () => {
  it("resolves deal_damage effect", () => {
    const resolver = new EffectResolver();
    const target = makeCombatEntity(50, 100);
    const ctx = makeEffectContext({ target });

    const effect: CardEffect = { type: "deal_damage", value: 12, target: "single_enemy" };
    resolver.resolve(effect, ctx);

    expect(target.hp).toBe(38);
  });

  it("resolves gain_block effect (applied to source)", () => {
    const resolver = new EffectResolver();
    const source = makeCombatEntity(50, 100, 0);
    const ctx = makeEffectContext({ source });

    const effect: CardEffect = { type: "gain_block", value: 8, target: "self" };
    resolver.resolve(effect, ctx);

    expect(source.block).toBe(8);
  });

  it("resolves apply_status effect", () => {
    const resolver = new EffectResolver();
    const target = makeCombatEntity(50, 100);
    const ctx = makeEffectContext({ target });

    const effect: CardEffect = { type: "apply_status", value: 3, target: "single_enemy" };
    resolver.resolve(effect, ctx);

    // The status ID is the effect.type passed to ApplyStatusCommand, which is "apply_status"
    expect(target._statuses.get("apply_status")).toBe(3);
  });

  it("resolves draw_cards effect", () => {
    const drawSpy = vi.fn();
    const mockDeck: IDeckManager = {
      draw: drawSpy,
      discard: () => {},
      exhaust: () => {},
    };
    const resolver = new EffectResolver();
    const ctx = makeEffectContext({ deck: mockDeck });

    const effect: CardEffect = { type: "draw_cards", value: 2, target: "self" };
    resolver.resolve(effect, ctx);

    expect(drawSpy).toHaveBeenCalledWith(2);
  });

  it("throws on unknown effect type", () => {
    const resolver = new EffectResolver();
    const ctx = makeEffectContext();

    const effect: CardEffect = { type: "unknown_effect", value: 1, target: "self" };
    expect(() => resolver.resolve(effect, ctx)).toThrow("Unknown card effect type");
  });

  it("resolveAll processes multiple effects in order", () => {
    const resolver = new EffectResolver();
    const target = makeCombatEntity(50, 100);
    const source = makeCombatEntity(50, 100, 0);
    const ctx = makeEffectContext({ source, target });

    const effects: CardEffect[] = [
      { type: "deal_damage", value: 10, target: "single_enemy" },
      { type: "gain_block", value: 5, target: "self" },
    ];
    resolver.resolveAll(effects, ctx);

    expect(target.hp).toBe(40);
    expect(source.block).toBe(5);
  });

  it("register adds custom handler", () => {
    const resolver = new EffectResolver();
    const customHandler = vi.fn();
    resolver.register("custom_effect", customHandler);

    const ctx = makeEffectContext();
    const effect: CardEffect = { type: "custom_effect", value: 42, target: "self" };
    resolver.resolve(effect, ctx);

    expect(customHandler).toHaveBeenCalledWith(ctx, effect);
  });
});

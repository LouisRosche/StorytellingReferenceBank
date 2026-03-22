import { describe, it, expect } from "vitest";
import {
  getMuseMatchup,
  getMuseCounters,
  getMuseWeaknesses,
  MUSE_IDENTITIES,
} from "../src/archetypes/muse-pentagon";
import type { MuseType } from "@deckbuilder/shared";

const ALL_MUSES: MuseType[] = ["trickster", "sovereign", "oracle", "wanderer", "martyr"];

describe("getMuseMatchup", () => {
  describe("pentagon completeness", () => {
    for (const muse of ALL_MUSES) {
      it(`${muse} beats exactly 2 and loses to exactly 2`, () => {
        const opponents = ALL_MUSES.filter((m) => m !== muse);
        const results = opponents.map((opp) => getMuseMatchup(muse, opp));

        const wins = results.filter(
          (r) => r.advantage === "strong" || r.advantage === "moderate",
        );
        const losses = results.filter(
          (r) =>
            r.advantage === "strong_disadvantage" ||
            r.advantage === "moderate_disadvantage",
        );

        expect(wins).toHaveLength(2);
        expect(losses).toHaveLength(2);
      });
    }
  });

  describe("mirror matchups are neutral (1.0)", () => {
    for (const muse of ALL_MUSES) {
      it(`${muse} vs ${muse} = neutral`, () => {
        const result = getMuseMatchup(muse, muse);
        expect(result.advantage).toBe("neutral");
        expect(result.multiplier).toBe(1.0);
      });
    }
  });

  describe("adjacent counters are strong (1.3x)", () => {
    // Pentagon order: trickster -> sovereign -> oracle -> wanderer -> martyr -> (wraps)
    const adjacentPairs: [MuseType, MuseType][] = [
      ["trickster", "sovereign"],
      ["sovereign", "oracle"],
      ["oracle", "wanderer"],
      ["wanderer", "martyr"],
      ["martyr", "trickster"],
    ];

    for (const [attacker, defender] of adjacentPairs) {
      it(`${attacker} → ${defender} = 1.3x (strong)`, () => {
        const result = getMuseMatchup(attacker, defender);
        expect(result.advantage).toBe("strong");
        expect(result.multiplier).toBe(1.3);
      });
    }
  });

  describe("cross counters are moderate (1.15x)", () => {
    // Cross = skip one in the pentagon
    const crossPairs: [MuseType, MuseType][] = [
      ["trickster", "oracle"],
      ["sovereign", "wanderer"],
      ["oracle", "martyr"],
      ["wanderer", "trickster"],
      ["martyr", "sovereign"],
    ];

    for (const [attacker, defender] of crossPairs) {
      it(`${attacker} → ${defender} = 1.15x (moderate)`, () => {
        const result = getMuseMatchup(attacker, defender);
        expect(result.advantage).toBe("moderate");
        expect(result.multiplier).toBeCloseTo(1.15, 5);
      });
    }
  });

  describe("disadvantages are reciprocals", () => {
    it("strong disadvantage is ~0.77 (1/1.3)", () => {
      // sovereign is beaten by trickster (strong), so sovereign attacking trickster's counter...
      // Actually: trickster beats sovereign (strong), so sovereign vs trickster = strong_disadvantage
      const result = getMuseMatchup("sovereign", "trickster");
      expect(result.advantage).toBe("strong_disadvantage");
      expect(result.multiplier).toBeCloseTo(1 / 1.3, 5);
    });

    it("moderate disadvantage is ~0.87 (1/1.15)", () => {
      // oracle vs trickster: trickster cross-beats oracle, so oracle vs trickster = moderate_disadvantage
      const result = getMuseMatchup("oracle", "trickster");
      expect(result.advantage).toBe("moderate_disadvantage");
      expect(result.multiplier).toBeCloseTo(1 / 1.15, 5);
    });
  });

  describe("specific narrative matchups", () => {
    it("Trickster beats Sovereign (strong)", () => {
      const result = getMuseMatchup("trickster", "sovereign");
      expect(result.advantage).toBe("strong");
      expect(result.multiplier).toBe(1.3);
    });

    it("Martyr beats Trickster (strong — adjacent wrapping)", () => {
      const result = getMuseMatchup("martyr", "trickster");
      expect(result.advantage).toBe("strong");
      expect(result.multiplier).toBe(1.3);
    });

    it("Oracle beats Wanderer (strong)", () => {
      const result = getMuseMatchup("oracle", "wanderer");
      expect(result.advantage).toBe("strong");
      expect(result.multiplier).toBe(1.3);
    });

    it("Wanderer beats Martyr (strong)", () => {
      const result = getMuseMatchup("wanderer", "martyr");
      expect(result.advantage).toBe("strong");
      expect(result.multiplier).toBe(1.3);
    });
  });
});

describe("getMuseCounters", () => {
  it("trickster counters sovereign (adjacent) and oracle (cross)", () => {
    const [adjacent, cross] = getMuseCounters("trickster");
    expect(adjacent).toBe("sovereign");
    expect(cross).toBe("oracle");
  });

  it("martyr counters trickster (adjacent) and sovereign (cross)", () => {
    const [adjacent, cross] = getMuseCounters("martyr");
    expect(adjacent).toBe("trickster");
    expect(cross).toBe("sovereign");
  });

  it("every muse counters exactly 2 distinct muses", () => {
    for (const muse of ALL_MUSES) {
      const [a, b] = getMuseCounters(muse);
      expect(a).not.toBe(b);
      expect(a).not.toBe(muse);
      expect(b).not.toBe(muse);
    }
  });
});

describe("getMuseWeaknesses", () => {
  it("trickster is weak to martyr (adjacent) and wanderer (cross)", () => {
    const [adjacent, cross] = getMuseWeaknesses("trickster");
    expect(adjacent).toBe("martyr");
    expect(cross).toBe("wanderer");
  });

  it("sovereign is weak to trickster (adjacent) and martyr (cross)", () => {
    const [adjacent, cross] = getMuseWeaknesses("sovereign");
    expect(adjacent).toBe("trickster");
    expect(cross).toBe("martyr");
  });

  it("weaknesses are the inverse of counters", () => {
    for (const muse of ALL_MUSES) {
      const [wa, wc] = getMuseWeaknesses(muse);
      // If muse is weak to wa, then wa should counter muse
      const waCounters = getMuseCounters(wa);
      expect(waCounters).toContain(muse);
      const wcCounters = getMuseCounters(wc);
      expect(wcCounters).toContain(muse);
    }
  });
});

describe("MUSE_IDENTITIES", () => {
  it("has entries for all 5 muses", () => {
    for (const muse of ALL_MUSES) {
      expect(MUSE_IDENTITIES[muse]).toBeDefined();
      expect(MUSE_IDENTITIES[muse].type).toBe(muse);
    }
  });

  it("each identity has a non-empty displayName and tradition", () => {
    for (const muse of ALL_MUSES) {
      const identity = MUSE_IDENTITIES[muse];
      expect(identity.displayName.length).toBeGreaterThan(0);
      expect(identity.tradition.length).toBeGreaterThan(0);
    }
  });

  it("each identity has exactly 2 dominant rasas", () => {
    for (const muse of ALL_MUSES) {
      expect(MUSE_IDENTITIES[muse].dominantRasa).toHaveLength(2);
    }
  });
});

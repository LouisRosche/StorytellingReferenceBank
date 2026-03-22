import { describe, it, expect } from "vitest";
import {
  MuseAffinity,
  calculateRarityMultiplier,
  calculateEffectivePower,
} from "../src/archetypes/affinity";
import type { MuseType } from "@deckbuilder/shared";

const ALL_MUSES: MuseType[] = ["trickster", "sovereign", "oracle", "wanderer", "martyr"];

describe("MuseAffinity", () => {
  it("fresh affinity has 0 for all Muses", () => {
    const affinity = new MuseAffinity();
    for (const muse of ALL_MUSES) {
      expect(affinity.getScore(muse)).toBe(0);
    }
  });

  it("addAffinity increases score", () => {
    const affinity = new MuseAffinity();
    affinity.addAffinity("trickster", 5);
    expect(affinity.getScore("trickster")).toBe(5);

    affinity.addAffinity("trickster", 3);
    expect(affinity.getScore("trickster")).toBe(8);
  });

  it("addAffinity ignores non-positive amounts", () => {
    const affinity = new MuseAffinity();
    affinity.addAffinity("oracle", 0);
    affinity.addAffinity("oracle", -5);
    expect(affinity.getScore("oracle")).toBe(0);
  });

  it("getDominant returns highest", () => {
    const affinity = new MuseAffinity();
    affinity.addAffinity("oracle", 10);
    affinity.addAffinity("trickster", 3);
    expect(affinity.getDominant()).toBe("oracle");
  });

  it("getDominant breaks ties by MUSE_TYPES order (first highest wins)", () => {
    const affinity = new MuseAffinity();
    // All at 0, trickster is first in iteration order
    expect(affinity.getDominant()).toBe("trickster");
  });

  it("getTotal sums all scores", () => {
    const affinity = new MuseAffinity();
    affinity.addAffinity("trickster", 5);
    affinity.addAffinity("oracle", 10);
    expect(affinity.getTotal()).toBe(15);
  });

  describe("commitment ratio", () => {
    it("is 0 at start (total is 0)", () => {
      const affinity = new MuseAffinity();
      expect(affinity.getCommitmentRatio("trickster")).toBe(0);
    });

    it("increases with focused investment", () => {
      const affinity = new MuseAffinity();
      affinity.addAffinity("trickster", 15);
      const ratio = affinity.getCommitmentRatio("trickster");
      expect(ratio).toBeGreaterThan(0);
      // With 15 points all in trickster: depth = 15/30 = 0.5, focus = 1.0
      // geometric mean = sqrt(0.5 * 1.0) = sqrt(0.5) ≈ 0.707
      expect(ratio).toBeCloseTo(Math.sqrt(0.5), 5);
    });

    it("scattered investment yields lower commitment than focused", () => {
      const focused = new MuseAffinity();
      focused.addAffinity("trickster", 15);

      const scattered = new MuseAffinity();
      scattered.addAffinity("trickster", 5);
      scattered.addAffinity("oracle", 5);
      scattered.addAffinity("wanderer", 5);

      expect(scattered.getCommitmentRatio("trickster")).toBeLessThan(
        focused.getCommitmentRatio("trickster"),
      );
    });

    it("maxes out at 1.0 with full commitment", () => {
      const affinity = new MuseAffinity();
      affinity.addAffinity("trickster", 30); // MAX_AFFINITY_FOR_SCALING
      // depth = 30/30 = 1.0, focus = 1.0, sqrt(1.0) = 1.0
      expect(affinity.getCommitmentRatio("trickster")).toBeCloseTo(1.0, 5);
    });
  });

  describe("rarity scaling", () => {
    it("commons at 0 commitment = 1.0", () => {
      expect(calculateRarityMultiplier("common", 0)).toBe(1.0);
    });

    it("commons at max commitment = 1.15", () => {
      expect(calculateRarityMultiplier("common", 1)).toBeCloseTo(1.15, 5);
    });

    it("legendaries at 0 commitment = 0.5", () => {
      expect(calculateRarityMultiplier("legendary", 0)).toBe(0.5);
    });

    it("legendaries at max commitment = 2.5", () => {
      expect(calculateRarityMultiplier("legendary", 1)).toBeCloseTo(2.5, 5);
    });

    it("uncommons at 0 = 0.9, at max = 1.4", () => {
      expect(calculateRarityMultiplier("uncommon", 0)).toBeCloseTo(0.9, 5);
      expect(calculateRarityMultiplier("uncommon", 1)).toBeCloseTo(1.4, 5);
    });

    it("rares at 0 = 0.7, at max = 1.8", () => {
      expect(calculateRarityMultiplier("rare", 0)).toBeCloseTo(0.7, 5);
      expect(calculateRarityMultiplier("rare", 1)).toBeCloseTo(1.8, 5);
    });

    it("clamps commitment ratio to [0, 1]", () => {
      // Negative ratio should clamp to 0
      expect(calculateRarityMultiplier("common", -1)).toBe(1.0);
      // Over-1 ratio should clamp to 1
      expect(calculateRarityMultiplier("common", 5)).toBeCloseTo(1.15, 5);
    });
  });

  describe("calculateEffectivePower", () => {
    it("rounds correctly", () => {
      // base 10, common at 0 commitment: 10 * 1.0 = 10
      expect(calculateEffectivePower(10, "common", 0)).toBe(10);
    });

    it("applies rarity multiplier and rounds", () => {
      // base 10, legendary at 0 commitment: 10 * 0.5 = 5
      expect(calculateEffectivePower(10, "legendary", 0)).toBe(5);
      // base 10, legendary at full commitment: 10 * 2.5 = 25
      expect(calculateEffectivePower(10, "legendary", 1)).toBe(25);
    });

    it("never returns negative", () => {
      expect(calculateEffectivePower(0, "legendary", 0)).toBe(0);
    });
  });

  describe("serialization roundtrip", () => {
    it("toJSON → fromJSON preserves all scores", () => {
      const original = new MuseAffinity();
      original.addAffinity("trickster", 7);
      original.addAffinity("oracle", 12);
      original.addAffinity("martyr", 3);

      const json = original.toJSON();
      const restored = MuseAffinity.fromJSON(json);

      for (const muse of ALL_MUSES) {
        expect(restored.getScore(muse)).toBe(original.getScore(muse));
      }
    });

    it("getDominant matches after roundtrip", () => {
      const original = new MuseAffinity();
      original.addAffinity("wanderer", 20);

      const restored = MuseAffinity.fromJSON(original.toJSON());
      expect(restored.getDominant()).toBe(original.getDominant());
    });
  });
});

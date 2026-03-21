import { describe, it, expect } from "vitest";
import { MuseFavorTracker } from "../src/muse/favor";
import { MotifManager, determineMotifReward } from "../src/muse/motif";
import {
  getJourneyPhase,
  getJourneyAct,
  getJourneyPacingMultiplier,
  isMuseSelectionFloor,
  isOrdealFloor,
  isFinalBossFloor,
  getJourneyContext,
} from "../src/muse/journey";
import type { MotifData, MuseType } from "@deckbuilder/shared";

// ---------------------------------------------------------------------------
// MuseFavorTracker
// ---------------------------------------------------------------------------

function makeMotif(overrides: Partial<MotifData> & { id: string }): MotifData {
  return {
    name: "Test Motif",
    description: "A test motif",
    muse: "trickster",
    rarity: "common",
    effectType: "bonus_damage",
    effectValue: 1,
    trigger: "on_turn_start",
    ...overrides,
  };
}

describe("MuseFavorTracker", () => {
  it("starts at 0 favor for all muses", () => {
    const tracker = new MuseFavorTracker();
    const muses: MuseType[] = ["trickster", "sovereign", "oracle", "wanderer", "martyr"];
    for (const muse of muses) {
      expect(tracker.getFavor(muse)).toBe(0);
    }
  });

  it("addFavor increases favor", () => {
    const tracker = new MuseFavorTracker();
    tracker.addFavor("trickster", 3);
    expect(tracker.getFavor("trickster")).toBe(3);

    tracker.addFavor("trickster", 7);
    expect(tracker.getFavor("trickster")).toBe(10);
  });

  it("addFavor ignores non-positive amounts", () => {
    const tracker = new MuseFavorTracker();
    tracker.addFavor("oracle", 0);
    tracker.addFavor("oracle", -2);
    expect(tracker.getFavor("oracle")).toBe(0);
  });

  describe("tier thresholds", () => {
    it("0 favor = tier 0", () => {
      const tracker = new MuseFavorTracker();
      expect(tracker.getTier("trickster")).toBe(0);
    });

    it("5 favor = tier 1", () => {
      const tracker = new MuseFavorTracker();
      tracker.addFavor("trickster", 5);
      expect(tracker.getTier("trickster")).toBe(1);
    });

    it("12 favor = tier 2", () => {
      const tracker = new MuseFavorTracker();
      tracker.addFavor("trickster", 12);
      expect(tracker.getTier("trickster")).toBe(2);
    });

    it("20 favor = tier 3", () => {
      const tracker = new MuseFavorTracker();
      tracker.addFavor("trickster", 20);
      expect(tracker.getTier("trickster")).toBe(3);
    });

    it("4 favor = still tier 0 (below threshold)", () => {
      const tracker = new MuseFavorTracker();
      tracker.addFavor("trickster", 4);
      expect(tracker.getTier("trickster")).toBe(0);
    });

    it("11 favor = still tier 1 (below tier 2 threshold)", () => {
      const tracker = new MuseFavorTracker();
      tracker.addFavor("trickster", 11);
      expect(tracker.getTier("trickster")).toBe(1);
    });
  });

  it("getDominantMuse returns muse with highest favor", () => {
    const tracker = new MuseFavorTracker();
    tracker.addFavor("oracle", 15);
    tracker.addFavor("martyr", 3);
    expect(tracker.getDominantMuse()).toBe("oracle");
  });

  describe("serialization roundtrip", () => {
    it("toJSON → fromJSON preserves all favor values", () => {
      const original = new MuseFavorTracker();
      original.addFavor("trickster", 5);
      original.addFavor("oracle", 12);
      original.addFavor("martyr", 20);

      const json = original.toJSON();
      const restored = MuseFavorTracker.fromJSON(json);

      const muses: MuseType[] = ["trickster", "sovereign", "oracle", "wanderer", "martyr"];
      for (const muse of muses) {
        expect(restored.getFavor(muse)).toBe(original.getFavor(muse));
      }
    });

    it("tiers match after roundtrip", () => {
      const original = new MuseFavorTracker();
      original.addFavor("trickster", 13);

      const restored = MuseFavorTracker.fromJSON(original.toJSON());
      expect(restored.getTier("trickster")).toBe(original.getTier("trickster"));
    });
  });
});

// ---------------------------------------------------------------------------
// MotifManager
// ---------------------------------------------------------------------------

describe("MotifManager", () => {
  it("can add up to MAX_MOTIF_SLOTS (3) motifs", () => {
    const manager = new MotifManager();
    expect(manager.addMotif(makeMotif({ id: "m1" }))).toBe(true);
    expect(manager.addMotif(makeMotif({ id: "m2" }))).toBe(true);
    expect(manager.addMotif(makeMotif({ id: "m3" }))).toBe(true);
    expect(manager.slotCount).toBe(3);
  });

  it("fourth add returns false", () => {
    const manager = new MotifManager();
    manager.addMotif(makeMotif({ id: "m1" }));
    manager.addMotif(makeMotif({ id: "m2" }));
    manager.addMotif(makeMotif({ id: "m3" }));
    expect(manager.addMotif(makeMotif({ id: "m4" }))).toBe(false);
    expect(manager.slotCount).toBe(3);
  });

  it("slotsAvailable decreases correctly", () => {
    const manager = new MotifManager();
    expect(manager.slotsAvailable).toBe(3);
    manager.addMotif(makeMotif({ id: "m1" }));
    expect(manager.slotsAvailable).toBe(2);
  });

  it("removeMotif removes by ID and returns the motif", () => {
    const manager = new MotifManager();
    const motif = makeMotif({ id: "m1" });
    manager.addMotif(motif);
    const removed = manager.removeMotif("m1");
    expect(removed).toEqual(motif);
    expect(manager.slotCount).toBe(0);
  });

  it("removeMotif returns null for missing ID", () => {
    const manager = new MotifManager();
    expect(manager.removeMotif("nonexistent")).toBeNull();
  });

  it("replaceMotif swaps at slot index", () => {
    const manager = new MotifManager();
    const m1 = makeMotif({ id: "m1" });
    const m2 = makeMotif({ id: "m2" });
    const replacement = makeMotif({ id: "m3" });

    manager.addMotif(m1);
    manager.addMotif(m2);

    const old = manager.replaceMotif(0, replacement);
    expect(old).toEqual(m1);
    expect(manager.getActive()[0].id).toBe("m3");
    expect(manager.slotCount).toBe(2); // count unchanged
  });

  it("replaceMotif returns null for invalid index", () => {
    const manager = new MotifManager();
    expect(manager.replaceMotif(0, makeMotif({ id: "m1" }))).toBeNull();
    expect(manager.replaceMotif(-1, makeMotif({ id: "m1" }))).toBeNull();
  });

  it("getByTrigger filters by trigger", () => {
    const manager = new MotifManager();
    manager.addMotif(makeMotif({ id: "m1", trigger: "on_turn_start" }));
    manager.addMotif(makeMotif({ id: "m2", trigger: "on_redirect" }));
    manager.addMotif(makeMotif({ id: "m3", trigger: "on_turn_start" }));

    const turnStart = manager.getByTrigger("on_turn_start");
    expect(turnStart).toHaveLength(2);
    expect(turnStart.map((m) => m.id)).toEqual(["m1", "m3"]);
  });

  it("getByMuse filters by muse", () => {
    const manager = new MotifManager();
    manager.addMotif(makeMotif({ id: "m1", muse: "trickster" }));
    manager.addMotif(makeMotif({ id: "m2", muse: "oracle" }));
    manager.addMotif(makeMotif({ id: "m3", muse: "trickster" }));

    const tricksterMotifs = manager.getByMuse("trickster");
    expect(tricksterMotifs).toHaveLength(2);
    expect(tricksterMotifs.map((m) => m.id)).toEqual(["m1", "m3"]);
  });

  it("serialization roundtrip via fromJSON", () => {
    const manager = new MotifManager();
    manager.addMotif(makeMotif({ id: "m1", muse: "oracle" }));
    manager.addMotif(makeMotif({ id: "m2", muse: "martyr" }));

    const json = manager.toJSON();
    const restored = MotifManager.fromJSON(json);

    expect(restored.slotCount).toBe(2);
    expect(restored.getActive().map((m) => m.id)).toEqual(["m1", "m2"]);
  });
});

// ---------------------------------------------------------------------------
// determineMotifReward
// ---------------------------------------------------------------------------

describe("determineMotifReward", () => {
  it("returns null if floor < 5", () => {
    expect(determineMotifReward(4, false, 0)).toBeNull();
    expect(determineMotifReward(1, false, 0)).toBeNull();
  });

  it('returns "common" at floor 5 (not completed)', () => {
    expect(determineMotifReward(5, false, 0)).toBe("common");
  });

  it('returns "common" at floor 8 (below ordeal, not completed)', () => {
    expect(determineMotifReward(8, false, 0)).toBe("common");
  });

  it('returns "uncommon" at floor 9+ (not completed)', () => {
    expect(determineMotifReward(9, false, 0)).toBe("uncommon");
    expect(determineMotifReward(12, false, 0)).toBe("uncommon");
  });

  it('returns "rare" on run completion with low commitment', () => {
    expect(determineMotifReward(13, true, 0.5)).toBe("rare");
  });

  it('returns "legendary" on run completion with high commitment (>0.7)', () => {
    expect(determineMotifReward(13, true, 0.8)).toBe("legendary");
    expect(determineMotifReward(13, true, 1.0)).toBe("legendary");
  });

  it('returns "rare" on run completion with exactly 0.7 commitment (not >0.7)', () => {
    expect(determineMotifReward(13, true, 0.7)).toBe("rare");
  });
});

// ---------------------------------------------------------------------------
// Journey
// ---------------------------------------------------------------------------

describe("Journey phases", () => {
  it("floor 1 = ordinary_world", () => {
    expect(getJourneyPhase(1)).toBe("ordinary_world");
  });

  it("floor 2 = call_to_adventure", () => {
    expect(getJourneyPhase(2)).toBe("call_to_adventure");
  });

  it("floors 3-4 = crossing_threshold", () => {
    expect(getJourneyPhase(3)).toBe("crossing_threshold");
    expect(getJourneyPhase(4)).toBe("crossing_threshold");
  });

  it("floor 5 = road_of_trials", () => {
    expect(getJourneyPhase(5)).toBe("road_of_trials");
  });

  it("floors 5-7 = road_of_trials", () => {
    expect(getJourneyPhase(6)).toBe("road_of_trials");
    expect(getJourneyPhase(7)).toBe("road_of_trials");
  });

  it("floor 9 = the_ordeal", () => {
    expect(getJourneyPhase(9)).toBe("the_ordeal");
  });

  it("floors 8-9 = the_ordeal", () => {
    expect(getJourneyPhase(8)).toBe("the_ordeal");
  });

  it("floors 10-12 = apotheosis", () => {
    expect(getJourneyPhase(10)).toBe("apotheosis");
    expect(getJourneyPhase(11)).toBe("apotheosis");
    expect(getJourneyPhase(12)).toBe("apotheosis");
  });

  it("floor 13 = the_return", () => {
    expect(getJourneyPhase(13)).toBe("the_return");
  });
});

describe("Journey acts (Jo-ha-kyu)", () => {
  it("floors 1-4 = jo", () => {
    for (let f = 1; f <= 4; f++) {
      expect(getJourneyAct(f)).toBe("jo");
    }
  });

  it("floors 5-9 = ha", () => {
    for (let f = 5; f <= 9; f++) {
      expect(getJourneyAct(f)).toBe("ha");
    }
  });

  it("floors 10-13 = kyu", () => {
    for (let f = 10; f <= 13; f++) {
      expect(getJourneyAct(f)).toBe("kyu");
    }
  });
});

describe("Pacing multipliers", () => {
  it("jo = 0.8", () => {
    expect(getJourneyPacingMultiplier(1)).toBe(0.8);
    expect(getJourneyPacingMultiplier(4)).toBe(0.8);
  });

  it("ha = 1.0", () => {
    expect(getJourneyPacingMultiplier(5)).toBe(1.0);
    expect(getJourneyPacingMultiplier(9)).toBe(1.0);
  });

  it("kyu = 1.3", () => {
    expect(getJourneyPacingMultiplier(10)).toBe(1.3);
    expect(getJourneyPacingMultiplier(13)).toBe(1.3);
  });
});

describe("Special floor checks", () => {
  it("isMuseSelectionFloor(2) = true", () => {
    expect(isMuseSelectionFloor(2)).toBe(true);
  });

  it("isMuseSelectionFloor for other floors = false", () => {
    expect(isMuseSelectionFloor(1)).toBe(false);
    expect(isMuseSelectionFloor(3)).toBe(false);
  });

  it("isOrdealFloor(9) = true", () => {
    expect(isOrdealFloor(9)).toBe(true);
  });

  it("isOrdealFloor for other floors = false", () => {
    expect(isOrdealFloor(8)).toBe(false);
    expect(isOrdealFloor(10)).toBe(false);
  });

  it("isFinalBossFloor(13) = true", () => {
    expect(isFinalBossFloor(13)).toBe(true);
  });

  it("isFinalBossFloor for other floors = false", () => {
    expect(isFinalBossFloor(12)).toBe(false);
    expect(isFinalBossFloor(14)).toBe(false);
  });
});

describe("getJourneyContext", () => {
  it("returns correct composite context for floor 2", () => {
    const ctx = getJourneyContext(2);
    expect(ctx.phase).toBe("call_to_adventure");
    expect(ctx.act).toBe("jo");
    expect(ctx.floor).toBe(2);
    expect(ctx.pacingMultiplier).toBe(0.8);
    expect(ctx.isMuseSelection).toBe(true);
    expect(ctx.isOrdeal).toBe(false);
    expect(ctx.isFinalBoss).toBe(false);
  });

  it("returns correct composite context for floor 13", () => {
    const ctx = getJourneyContext(13);
    expect(ctx.phase).toBe("the_return");
    expect(ctx.act).toBe("kyu");
    expect(ctx.pacingMultiplier).toBe(1.3);
    expect(ctx.isFinalBoss).toBe(true);
  });
});

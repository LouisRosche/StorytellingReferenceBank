import { describe, it, expect } from "vitest";
import { generateMap, type MapNode } from "../src/map/generator";
import type { MapConfig, RoomType } from "@deckbuilder/shared";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function defaultConfig(overrides?: Partial<MapConfig>): MapConfig {
  return {
    floorsPerAct: 13,
    columnsPerFloor: 4,
    pathCount: 3,
    roomWeights: {
      monster: 0.45,
      event: 0.12,
      rest: 0.12,
      elite: 0.08,
      shop: 0.08,
      boss: 0,
    },
    eliteMinFloor: 3,
    restMinFloor: 3,
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("generateMap", () => {
  it("produces nodes on the correct number of floors", () => {
    const config = defaultConfig({ floorsPerAct: 13 });
    const map = generateMap(config, 42);

    const floors = new Set(map.map((n) => n.floor));
    // Floor 0 and floor 12 (0-indexed, 13 floors total) should exist
    expect(floors.has(0)).toBe(true);
    expect(floors.has(12)).toBe(true);

    // No floor beyond the configured range
    for (const f of floors) {
      expect(f).toBeGreaterThanOrEqual(0);
      expect(f).toBeLessThan(13);
    }
  });

  it("all connections point forward (to the next floor)", () => {
    const config = defaultConfig();
    const map = generateMap(config, 42);

    const nodeMap = new Map<string, MapNode>();
    for (const node of map) {
      nodeMap.set(node.id, node);
    }

    for (const node of map) {
      for (const connId of node.connections) {
        const target = nodeMap.get(connId);
        expect(target).toBeDefined();
        expect(target!.floor).toBe(node.floor + 1);
      }
    }
  });

  it("first floor nodes are always monsters", () => {
    const config = defaultConfig();
    const map = generateMap(config, 42);
    const firstFloor = map.filter((n) => n.floor === 0);

    expect(firstFloor.length).toBeGreaterThan(0);
    for (const node of firstFloor) {
      expect(node.type).toBe("monster");
    }
  });

  it("last floor nodes are always rest", () => {
    const config = defaultConfig({ floorsPerAct: 13 });
    const map = generateMap(config, 42);
    const lastFloor = map.filter((n) => n.floor === 12);

    expect(lastFloor.length).toBeGreaterThan(0);
    for (const node of lastFloor) {
      expect(node.type).toBe("rest");
    }
  });

  it("has at least one node on the first and last floors", () => {
    const config = defaultConfig();
    const map = generateMap(config, 42);

    const firstFloor = map.filter((n) => n.floor === 0);
    const lastFloor = map.filter((n) => n.floor === config.floorsPerAct - 1);

    expect(firstFloor.length).toBeGreaterThan(0);
    expect(lastFloor.length).toBeGreaterThan(0);
  });

  it("every non-last-floor node has at least one connection", () => {
    const config = defaultConfig();
    const map = generateMap(config, 42);

    const nonLastFloor = map.filter((n) => n.floor < config.floorsPerAct - 1);
    for (const node of nonLastFloor) {
      expect(node.connections.length).toBeGreaterThan(0);
    }
  });

  it("all node IDs are unique", () => {
    const config = defaultConfig();
    const map = generateMap(config, 42);
    const ids = map.map((n) => n.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  describe("seed determinism", () => {
    it("same seed produces the same map", () => {
      const config = defaultConfig();
      const map1 = generateMap(config, 12345);
      const map2 = generateMap(config, 12345);

      expect(map1).toEqual(map2);
    });

    it("different seeds produce different maps", () => {
      const config = defaultConfig();
      const map1 = generateMap(config, 12345);
      const map2 = generateMap(config, 99999);

      // Compare node IDs or types — they should differ
      const ids1 = map1.map((n) => n.id).join(",");
      const ids2 = map2.map((n) => n.id).join(",");

      // With different seeds and random paths, the used nodes should differ
      expect(ids1).not.toBe(ids2);
    });
  });

  it("columns are within valid range", () => {
    const config = defaultConfig({ columnsPerFloor: 4 });
    const map = generateMap(config, 42);

    for (const node of map) {
      expect(node.column).toBeGreaterThanOrEqual(0);
      expect(node.column).toBeLessThan(4);
    }
  });

  it("room types are all valid RoomType values", () => {
    const validTypes: RoomType[] = ["monster", "elite", "rest", "shop", "event", "boss"];
    const config = defaultConfig();
    const map = generateMap(config, 42);

    for (const node of map) {
      expect(validTypes).toContain(node.type);
    }
  });
});

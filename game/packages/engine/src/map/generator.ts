/**
 * Procedural DAG map generator following the Slay-the-Spire algorithm.
 * Ported from MapGenerator.cs — pure TypeScript, no framework dependencies.
 */

import type { MapConfig, RoomType } from "@deckbuilder/shared";
import { createSeededRandom, type SeededRandom } from "../cards/deck";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface MapNode {
  id: string;
  floor: number;
  column: number;
  type: RoomType;
  /** IDs of nodes this node connects to on the next floor. */
  connections: string[];
}

export type MapGraph = MapNode[];

// ---------------------------------------------------------------------------
// Generator
// ---------------------------------------------------------------------------

/**
 * Generate a Slay-the-Spire-style DAG map.
 *
 * @param config  Map configuration (floor count, columns, weights, etc.)
 * @param seed    Deterministic seed for the PRNG.
 * @returns       Flat array of all reachable MapNodes.
 */
export function generateMap(config: MapConfig, seed: number): MapGraph {
  const rng = createSeededRandom(seed);
  const floors = config.floorsPerAct;
  const columns = config.columnsPerFloor;
  const pathCount = config.pathCount;

  // -----------------------------------------------------------------------
  // 1. Initialise an empty grid.
  // -----------------------------------------------------------------------
  type InternalNode = {
    floor: number;
    column: number;
    type: RoomType;
    children: Set<string>; // child node ids
    parents: Set<string>; // parent node ids
  };

  const grid: InternalNode[][] = [];
  for (let f = 0; f < floors; f++) {
    grid[f] = [];
    for (let c = 0; c < columns; c++) {
      grid[f][c] = {
        floor: f,
        column: c,
        type: "monster",
        children: new Set(),
        parents: new Set(),
      };
    }
  }

  const nodeId = (f: number, c: number): string => `${f}_${c}`;

  // -----------------------------------------------------------------------
  // 2. Draw paths from floor 0 to floor N-1.
  // -----------------------------------------------------------------------
  const usedNodes = new Set<string>();
  const edges = new Set<string>();

  const pickNextColumn = (col: number): number => {
    const offset = Math.floor(rng() * 3) - 1; // -1, 0, or 1
    return clamp(col + offset, 0, columns - 1);
  };

  const hasCrossingEdge = (floor: number, fromCol: number, toCol: number): boolean => {
    for (const edge of edges) {
      if (!edge.startsWith(`${floor}_`)) continue;

      const parts = edge.split("->");
      if (parts.length !== 2) continue;
      const [fromPart, toPart] = parts;
      const existingFrom = parseInt(fromPart.split("_")[1], 10);
      const existingTo = parseInt(toPart.split("_")[1], 10);
      if (isNaN(existingFrom) || isNaN(existingTo)) continue;

      if (
        (fromCol < existingFrom && toCol > existingTo) ||
        (fromCol > existingFrom && toCol < existingTo)
      ) {
        return true;
      }
    }
    return false;
  };

  for (let p = 0; p < pathCount; p++) {
    let col = Math.floor(rng() * columns);
    usedNodes.add(nodeId(0, col));

    for (let floor = 0; floor < floors - 1; floor++) {
      let nextCol = pickNextColumn(col);
      let edgeKey = `${nodeId(floor, col)}->${nodeId(floor + 1, nextCol)}`;

      if (hasCrossingEdge(floor, col, nextCol)) {
        // Fall back to straight-up connection.
        nextCol = col;
        edgeKey = `${nodeId(floor, col)}->${nodeId(floor + 1, nextCol)}`;
      }

      if (!edges.has(edgeKey)) {
        edges.add(edgeKey);
        grid[floor][col].children.add(nodeId(floor + 1, nextCol));
        grid[floor + 1][nextCol].parents.add(nodeId(floor, col));
      }

      usedNodes.add(nodeId(floor + 1, nextCol));
      col = nextCol;
    }
  }

  // -----------------------------------------------------------------------
  // 3. Assign room types to used nodes.
  // -----------------------------------------------------------------------
  const weights = config.roomWeights;

  const isValidPlacement = (node: InternalNode, proposed: RoomType, floor: number): boolean => {
    // No consecutive same-type major rooms (check parents).
    for (const pid of node.parents) {
      const [pf, pc] = pid.split("_").map(Number);
      if (grid[pf][pc].type === proposed) return false;
    }

    // No sibling nodes sharing the same type.
    for (const pid of node.parents) {
      const [pf, pc] = pid.split("_").map(Number);
      for (const siblingId of grid[pf][pc].children) {
        if (siblingId === nodeId(floor, node.column)) continue;
        const [sf, sc] = siblingId.split("_").map(Number);
        if (grid[sf][sc].type === proposed) return false;
      }
    }

    // Pre-boss floor: no rest site on floor N-2 (floor N-1 is always rest).
    if (proposed === "rest" && floor === floors - 2) return false;

    return true;
  };

  const pickRoomType = (node: InternalNode, floor: number): RoomType => {
    const roll = rng();
    let cumulative = 0;

    // Event
    cumulative += weights.event ?? 0;
    if (roll < cumulative && isValidPlacement(node, "event", floor)) return "event";

    // Rest
    cumulative += weights.rest ?? 0;
    if (roll < cumulative && floor >= config.restMinFloor && isValidPlacement(node, "rest", floor))
      return "rest";

    // Elite
    cumulative += weights.elite ?? 0;
    if (
      roll < cumulative &&
      floor >= config.eliteMinFloor &&
      isValidPlacement(node, "elite", floor)
    )
      return "elite";

    // Shop
    cumulative += weights.shop ?? 0;
    if (roll < cumulative && isValidPlacement(node, "shop", floor)) return "shop";

    return "monster";
  };

  for (let f = 0; f < floors; f++) {
    for (let c = 0; c < columns; c++) {
      if (!usedNodes.has(nodeId(f, c))) continue;

      const node = grid[f][c];

      if (f === 0) {
        node.type = "monster";
      } else if (f === floors - 1) {
        node.type = "rest";
      } else {
        node.type = pickRoomType(node, f);
      }
    }
  }

  // -----------------------------------------------------------------------
  // 4. Build the flat MapGraph output (only reachable nodes).
  // -----------------------------------------------------------------------
  const result: MapGraph = [];

  for (let f = 0; f < floors; f++) {
    for (let c = 0; c < columns; c++) {
      const id = nodeId(f, c);
      if (!usedNodes.has(id)) continue;

      const node = grid[f][c];
      result.push({
        id,
        floor: f,
        column: c,
        type: node.type,
        connections: Array.from(node.children),
      });
    }
  }

  return result;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

import type { JourneyPhase, JourneyAct } from "@deckbuilder/shared";
import { FLOORS_JO, FLOORS_HA } from "@deckbuilder/shared";

/**
 * Maps floor number to Hero's Journey phase and Jo-ha-kyū act.
 *
 * Jo (序) — Floors 1-4: Slow, deliberate. Foundation.
 *   Floor 1: Ordinary World
 *   Floor 2: Call to Adventure (choose Muse)
 *   Floors 3-4: Crossing the Threshold
 *
 * Ha (破) — Floors 5-9: Accelerating. Commitment tested.
 *   Floors 5-7: Road of Trials
 *   Floors 8-9: The Ordeal (mid-boss on floor 9)
 *
 * Kyū (急) — Floors 10-13: Swift, decisive. Culmination.
 *   Floors 10-12: Apotheosis
 *   Floor 13: The Return (final boss)
 */
export function getJourneyPhase(floor: number): JourneyPhase {
  if (floor <= 0) return "ordinary_world";
  if (floor === 1) return "ordinary_world";
  if (floor === 2) return "call_to_adventure";
  if (floor <= 4) return "crossing_threshold";
  if (floor <= 7) return "road_of_trials";
  if (floor <= 9) return "the_ordeal";
  if (floor <= 12) return "apotheosis";
  return "the_return";
}

/** Get the Jo-ha-kyū act for a given floor. */
export function getJourneyAct(floor: number): JourneyAct {
  if (floor <= FLOORS_JO) return "jo";
  if (floor <= FLOORS_JO + FLOORS_HA) return "ha";
  return "kyu";
}

/** Pacing multiplier for encounter difficulty based on Jo-ha-kyū rhythm. */
export function getJourneyPacingMultiplier(floor: number): number {
  const act = getJourneyAct(floor);
  switch (act) {
    case "jo":  return 0.8;  // Slow, deliberate — easier encounters
    case "ha":  return 1.0;  // Breaking, acceleration — standard difficulty
    case "kyu": return 1.3;  // Rapid, decisive — intensified
  }
}

/**
 * Whether the current floor is a Muse selection point.
 * Floor 2 = Call to Adventure = choose your Muse.
 */
export function isMuseSelectionFloor(floor: number): boolean {
  return floor === 2;
}

/** Whether the current floor is the mid-boss (Ordeal). */
export function isOrdealFloor(floor: number): boolean {
  return floor === 9;
}

/** Whether the current floor is the final boss (Return). */
export function isFinalBossFloor(floor: number): boolean {
  return floor === 13;
}

/**
 * Narrative context for the current journey phase.
 * Used by the event/flavor text system to select appropriate narrative beats.
 */
export interface JourneyContext {
  phase: JourneyPhase;
  act: JourneyAct;
  floor: number;
  pacingMultiplier: number;
  isMuseSelection: boolean;
  isOrdeal: boolean;
  isFinalBoss: boolean;
}

export function getJourneyContext(floor: number): JourneyContext {
  return {
    phase: getJourneyPhase(floor),
    act: getJourneyAct(floor),
    floor,
    pacingMultiplier: getJourneyPacingMultiplier(floor),
    isMuseSelection: isMuseSelectionFloor(floor),
    isOrdeal: isOrdealFloor(floor),
    isFinalBoss: isFinalBossFloor(floor),
  };
}

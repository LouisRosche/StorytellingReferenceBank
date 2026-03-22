import type { MuseType } from "@deckbuilder/shared";

/** Result of a matchup between two Muses. */
export interface MuseMatchup {
  advantage: "strong" | "moderate" | "neutral" | "moderate_disadvantage" | "strong_disadvantage";
  multiplier: number;
}

const STRONG_ADVANTAGE = 1.3;
const MODERATE_ADVANTAGE = 1.15;
const NEUTRAL = 1.0;
const MODERATE_DISADVANTAGE = 1 / MODERATE_ADVANTAGE; // ~0.87
const STRONG_DISADVANTAGE = 1 / STRONG_ADVANTAGE;     // ~0.77

// Pentagon adjacency: each entry beats the next (wrapping)
const PENTAGON_ORDER: MuseType[] = ["trickster", "sovereign", "oracle", "wanderer", "martyr"];

/**
 * Get the matchup multiplier when attacker's muse faces defender's muse.
 * Same muse = neutral (1.0).
 * Adjacent in pentagon = strong advantage (1.3) or strong disadvantage (0.77).
 * Cross in pentagon = moderate advantage (1.15) or moderate disadvantage (0.87).
 */
export function getMuseMatchup(attacker: MuseType, defender: MuseType): MuseMatchup {
  if (attacker === defender) {
    return { advantage: "neutral", multiplier: NEUTRAL };
  }

  const atkIdx = PENTAGON_ORDER.indexOf(attacker);
  const defIdx = PENTAGON_ORDER.indexOf(defender);
  const diff = ((defIdx - atkIdx) % 5 + 5) % 5; // positive modulo

  // diff=1: attacker beats next adjacent (strong advantage)
  // diff=2: attacker beats cross (moderate advantage)
  // diff=3: attacker loses to cross (moderate disadvantage)
  // diff=4: attacker loses to adjacent (strong disadvantage)
  switch (diff) {
    case 1: return { advantage: "strong", multiplier: STRONG_ADVANTAGE };
    case 2: return { advantage: "moderate", multiplier: MODERATE_ADVANTAGE };
    case 3: return { advantage: "moderate_disadvantage", multiplier: MODERATE_DISADVANTAGE };
    case 4: return { advantage: "strong_disadvantage", multiplier: STRONG_DISADVANTAGE };
    default: return { advantage: "neutral", multiplier: NEUTRAL };
  }
}

/** Returns the two Muses that the given Muse beats (adjacent, then cross). */
export function getMuseCounters(muse: MuseType): [MuseType, MuseType] {
  const idx = PENTAGON_ORDER.indexOf(muse);
  const adjacent = PENTAGON_ORDER[(idx + 1) % 5];
  const cross = PENTAGON_ORDER[(idx + 2) % 5];
  return [adjacent, cross];
}

/** Returns the two Muses that beat the given Muse (adjacent, then cross). */
export function getMuseWeaknesses(muse: MuseType): [MuseType, MuseType] {
  const idx = PENTAGON_ORDER.indexOf(muse);
  const adjacent = PENTAGON_ORDER[((idx - 1) % 5 + 5) % 5];
  const cross = PENTAGON_ORDER[((idx - 2) % 5 + 5) % 5];
  return [adjacent, cross];
}

/** Full narrative metadata per Muse. */
export interface MuseIdentity {
  type: MuseType;
  displayName: string;
  tradition: string;
  dominantRasa: [string, string];
  signatureMechanic: string;
  runFeeling: string;
}

export const MUSE_IDENTITIES: Record<MuseType, MuseIdentity> = {
  trickster: {
    type: "trickster",
    displayName: "The Trickster",
    tradition: "Folklore & Fable — Anansi, Loki, Coyote, Reynard",
    dominantRasa: ["hasya", "adbhuta"],
    signatureMechanic: "Redirect — reroute enemy intents, copy effects, turn strength into weakness",
    runFeeling: "A heist. Plans within plans.",
  },
  sovereign: {
    type: "sovereign",
    displayName: "The Sovereign",
    tradition: "Epic & Dynasty — Gilgamesh, Arthur, Sundiata, Caesar",
    dominantRasa: ["veera", "raudra"],
    signatureMechanic: "Decree — play scaling persistent effects that grow stronger each turn",
    runFeeling: "Empire-building. Slow start, unstoppable endgame.",
  },
  oracle: {
    type: "oracle",
    displayName: "The Oracle",
    tradition: "Prophecy & Mystery — Cassandra, Tiresias, the Norns, I Ching",
    dominantRasa: ["bhayanaka", "adbhuta"],
    signatureMechanic: "Foresight — see upcoming draws and enemy intents, rearrange draw pile",
    runFeeling: "A puzzle unfolding. You arranged this three turns ago.",
  },
  wanderer: {
    type: "wanderer",
    displayName: "The Wanderer",
    tradition: "Picaresque & Odyssey — Odysseus, Xuanzang, Ibn Battuta, Huck Finn",
    dominantRasa: ["adbhuta", "shringara"],
    signatureMechanic: "Forage — gain temporary cards from encounters and the environment",
    runFeeling: "An adventure. Every fight gives you something new.",
  },
  martyr: {
    type: "martyr",
    displayName: "The Martyr",
    tradition: "Tragedy & Sacrifice — Prometheus, Antigone, Roland, Karna",
    dominantRasa: ["karuna", "veera"],
    signatureMechanic: "Offering — spend HP or sacrifice cards to fuel devastating effects",
    runFeeling: "A tragedy building toward transcendence.",
  },
};

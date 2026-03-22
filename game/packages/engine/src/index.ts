// Archetypes — Muse pentagon, affinity tracking, rarity scaling
export {
  getMuseMatchup,
  getMuseCounters,
  getMuseWeaknesses,
  MUSE_IDENTITIES,
  type MuseMatchup,
  type MuseIdentity,
} from "./archetypes/index.js";

export {
  MuseAffinity,
  calculateRarityMultiplier,
  calculateEffectivePower,
} from "./archetypes/index.js";

// Muse systems — favor, motifs, hero's journey
export { MuseFavorTracker, FAVOR_GRANTS } from "./muse/index.js";
export { MotifManager, determineMotifReward } from "./muse/index.js";
export {
  getJourneyPhase,
  getJourneyAct,
  getJourneyPacingMultiplier,
  isMuseSelectionFloor,
  isOrdealFloor,
  isFinalBossFloor,
  getJourneyContext,
  type JourneyContext,
} from "./muse/index.js";

// Combat — state machine, commands
export { StateMachine, type IState } from "./combat/index.js";
export {
  CommandInvoker,
  DealDamageCommand,
  GainBlockCommand,
  ApplyStatusCommand,
  HealCommand,
  type ICommand,
  type ICombatEntity,
} from "./combat/index.js";

// Cards — effects, deck management
export { EffectResolver } from "./cards/index.js";
export { Deck } from "./cards/index.js";

// Map — procedural generation
export { generateMap, type MapNode } from "./map/index.js";

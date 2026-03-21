export const CARD_RARITIES = [
  "common",
  "uncommon",
  "rare",
  "legendary",
] as const;

export const ROOM_TYPES = [
  "monster",
  "elite",
  "rest",
  "shop",
  "event",
  "boss",
] as const;

export const TURN_PHASES = [
  "draw",
  "player_action",
  "enemy_intent",
  "resolution",
  "end_turn",
] as const;

export const MAX_HAND_SIZE = 10;
export const MAX_ENERGY = 3;

import type { MuseType } from "./muse";

export type TurnPhase =
  | "draw"
  | "player_action"
  | "enemy_intent"
  | "resolution"
  | "end_turn";

export interface PlayerState {
  hp: number;
  maxHp: number;
  energy: number;
  maxEnergy: number;
  block: number;
  statusEffects: Record<string, number>;
}

export interface EnemyState {
  id: string;
  name: string;
  hp: number;
  maxHp: number;
  block: number;
  intentType: "attack" | "defend" | "buff" | "debuff" | "unknown";
  intentValue: number;
  statusEffects: Record<string, number>;
  /** Enemy's Muse affiliation — affects archetype counter multipliers. */
  muse: MuseType | null;
}

export interface CombatState {
  turnPhase: TurnPhase;
  turnNumber: number;
  player: PlayerState;
  enemies: EnemyState[];
  hand: string[];
  drawPile: string[];
  discardPile: string[];
  exhaustPile: string[];
}

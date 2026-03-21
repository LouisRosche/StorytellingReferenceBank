export type RoomType =
  | "monster"
  | "elite"
  | "rest"
  | "shop"
  | "event"
  | "boss";

export interface MapConfig {
  floorsPerAct: number;
  columnsPerFloor: number;
  pathCount: number;
  roomWeights: Record<RoomType, number>;
  /** Minimum floor before elites/rest sites can spawn */
  eliteMinFloor: number;
  restMinFloor: number;
}

export interface EncounterConfig {
  /** Base HP scaling per act */
  hpMultiplierPerAct: number;
  /** Elite difficulty multiplier at higher ascensions */
  eliteAscensionMultiplier: number;
}

export interface GameConfig {
  startingHp: number;
  maxHp: number;
  startingEnergy: number;
  startingDeckSize: number;
  drawPerTurn: number;
  map: MapConfig;
  encounters: EncounterConfig;
}

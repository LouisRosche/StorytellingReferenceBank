import type { MuseType, MuseKeyword } from "./muse";

export type CardRarity = "common" | "uncommon" | "rare" | "legendary";

export type CardTarget = "single_enemy" | "all_enemies" | "self" | "none";

export interface CardEffect {
  type: string;
  value: number;
  target: CardTarget;
  /** Optional secondary value (e.g., duration for status effects) */
  duration?: number;
}

export interface CardData {
  id: string;
  name: string;
  description: string;
  manaCost: number;
  rarity: CardRarity;
  effects: CardEffect[];
  artAssetKey: string;
  /** If true, card is removed from deck after play (exhaust) */
  exhaust: boolean;
  /** If true, card is removed from hand at end of turn (ethereal) */
  ethereal: boolean;
  /** Muse affiliation. Null for neutral cards. */
  muse: MuseType | null;
  /** Muse keyword tag (redirect, decree, foresight, forage, offering). */
  keyword?: MuseKeyword;
}

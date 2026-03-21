import Phaser from "phaser";
import { BootScene } from "./scenes/BootScene.js";
import { CombatScene } from "./scenes/CombatScene.js";
import { MapScene } from "./scenes/MapScene.js";

export interface GameLaunchOptions {
  parent: string | HTMLElement;
  width?: number;
  height?: number;
}

export function createGameConfig(options: GameLaunchOptions): Phaser.Types.Core.GameConfig {
  return {
    type: Phaser.AUTO,
    parent: options.parent,
    width: options.width ?? 1280,
    height: options.height ?? 720,
    backgroundColor: "#0a0a0f",
    scale: {
      mode: Phaser.Scale.FIT,
      autoCenter: Phaser.Scale.CENTER_BOTH,
    },
    scene: [BootScene, CombatScene, MapScene],
  };
}

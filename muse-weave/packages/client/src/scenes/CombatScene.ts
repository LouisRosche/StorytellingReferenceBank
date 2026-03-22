import Phaser from "phaser";

export class CombatScene extends Phaser.Scene {
  constructor() {
    super({ key: "CombatScene" });
  }

  create(): void {
    const { width, height } = this.cameras.main;
    this.add
      .text(width / 2, height / 2 - 40, "Combat", {
        fontSize: "32px",
        color: "#ffffff",
        fontFamily: "serif",
      })
      .setOrigin(0.5);

    this.add
      .text(width / 2, height / 2 + 20, "Engine connected — scenes ready", {
        fontSize: "18px",
        color: "#888888",
        fontFamily: "serif",
      })
      .setOrigin(0.5);

    // Temporary: click to go back to map
    this.input.once("pointerdown", () => {
      this.scene.start("MapScene");
    });
  }
}

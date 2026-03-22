import Phaser from "phaser";

export class MapScene extends Phaser.Scene {
  constructor() {
    super({ key: "MapScene" });
  }

  create(): void {
    const { width, height } = this.cameras.main;
    this.add
      .text(width / 2, height / 2 - 40, "The Journey Begins", {
        fontSize: "32px",
        color: "#ffffff",
        fontFamily: "serif",
      })
      .setOrigin(0.5);

    this.add
      .text(width / 2, height / 2 + 20, "Choose your path", {
        fontSize: "18px",
        color: "#888888",
        fontFamily: "serif",
      })
      .setOrigin(0.5);

    // Temporary: click to enter combat
    this.input.once("pointerdown", () => {
      this.scene.start("CombatScene");
    });
  }
}

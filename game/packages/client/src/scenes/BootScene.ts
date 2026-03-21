import Phaser from "phaser";

export class BootScene extends Phaser.Scene {
  constructor() {
    super({ key: "BootScene" });
  }

  preload(): void {
    // Placeholder — load assets here when we have them
    const { width, height } = this.cameras.main;
    const bar = this.add.rectangle(width / 2, height / 2, 300, 30, 0x333333);
    const fill = this.add.rectangle(width / 2 - 148, height / 2, 4, 26, 0x8866ff);
    fill.setOrigin(0, 0.5);

    this.load.on("progress", (value: number) => {
      fill.width = 296 * value;
    });

    this.load.on("complete", () => {
      bar.destroy();
      fill.destroy();
    });
  }

  create(): void {
    this.scene.start("MapScene");
  }
}

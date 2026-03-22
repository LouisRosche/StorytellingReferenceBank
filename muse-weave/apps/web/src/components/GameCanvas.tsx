"use client";

import { useEffect, useRef } from "react";

export function GameCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);
  const gameRef = useRef<Phaser.Game | null>(null);

  useEffect(() => {
    if (!containerRef.current || gameRef.current) return;

    let destroyed = false;

    async function init() {
      const Phaser = await import("phaser");
      const { createGameConfig } = await import("@deckbuilder/client");

      if (destroyed || !containerRef.current) return;

      const config = createGameConfig({ parent: containerRef.current });
      gameRef.current = new Phaser.Game(config);
    }

    init();

    return () => {
      destroyed = true;
      if (gameRef.current) {
        gameRef.current.destroy(true);
        gameRef.current = null;
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      style={{ width: "100%", height: "100%", background: "#0a0a0f" }}
    />
  );
}

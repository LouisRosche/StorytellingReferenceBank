"use client";

import { useCallback, useState } from "react";
import { Unity, useUnityContext } from "react-unity-webgl";
import type { CombatState } from "@deckbuilder/shared";

/**
 * Wraps the Unity WebGL player. Build artifacts are expected in public/Build/.
 *
 * Two-way communication:
 *   Unity → React: registerReactCallback("OnCombatStateChanged", handler)
 *   React → Unity: sendMessage("GameBridge", "MethodName", payload)
 */
export function UnityGame() {
  const {
    unityProvider,
    isLoaded,
    loadingProgression,
    sendMessage,
    addEventListener,
    removeEventListener,
  } = useUnityContext({
    loaderUrl: "/Build/Build.loader.js",
    dataUrl: "/Build/Build.data.gz",
    frameworkUrl: "/Build/Build.framework.js.gz",
    codeUrl: "/Build/Build.wasm.gz",
  });

  const [combatState, setCombatState] = useState<CombatState | null>(null);

  const handleCombatUpdate = useCallback((jsonPayload: string) => {
    try {
      const state: CombatState = JSON.parse(jsonPayload);
      setCombatState(state);
    } catch {
      console.error("Failed to parse combat state from Unity");
    }
  }, []);

  // Register the callback once Unity is loaded
  if (isLoaded) {
    addEventListener("OnCombatStateChanged", handleCombatUpdate);
  }

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      {!isLoaded && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "#111",
            color: "#fff",
            fontSize: "1.5rem",
          }}
        >
          Loading {Math.round(loadingProgression * 100)}%
        </div>
      )}
      <Unity
        unityProvider={unityProvider}
        style={{ width: "100%", height: "100%", visibility: isLoaded ? "visible" : "hidden" }}
      />
    </div>
  );
}

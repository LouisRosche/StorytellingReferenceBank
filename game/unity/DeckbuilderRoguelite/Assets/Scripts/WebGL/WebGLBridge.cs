using System.Runtime.InteropServices;
using UnityEngine;

namespace Deckbuilder.WebGL
{
    /// <summary>
    /// Two-way communication bridge between Unity WebGL and the React host.
    /// Attach to a persistent GameObject named "GameBridge" in the scene.
    /// </summary>
    public class WebGLBridge : MonoBehaviour
    {
        // --- Unity → JavaScript (calling into the browser) ---

#if UNITY_WEBGL && !UNITY_EDITOR
        [DllImport("__Internal")]
        private static extern void SendCombatStateToReact(string jsonPayload);

        [DllImport("__Internal")]
        private static extern void SendGameEventToReact(string eventName, string jsonPayload);
#else
        private static void SendCombatStateToReact(string jsonPayload)
            => Debug.Log($"[WebGLBridge] CombatState: {jsonPayload}");

        private static void SendGameEventToReact(string eventName, string jsonPayload)
            => Debug.Log($"[WebGLBridge] Event {eventName}: {jsonPayload}");
#endif

        public static void EmitCombatState(string json) => SendCombatStateToReact(json);
        public static void EmitEvent(string eventName, string json) => SendGameEventToReact(eventName, json);

        // --- JavaScript → Unity (called from React via sendMessage) ---

        public void OnCardPlayed(string cardDataJson)
        {
            Debug.Log($"[WebGLBridge] Card played: {cardDataJson}");
            // Deserialize and route to CommandInvoker
        }

        public void OnEndTurnRequested()
        {
            Debug.Log("[WebGLBridge] End turn requested");
            // Signal FSM to advance
        }

        public void OnTargetSelected(string targetId)
        {
            Debug.Log($"[WebGLBridge] Target selected: {targetId}");
            // Pop TargetSelectionState with result
        }
    }
}

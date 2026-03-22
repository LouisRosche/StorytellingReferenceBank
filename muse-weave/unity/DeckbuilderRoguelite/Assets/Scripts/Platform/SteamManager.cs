using UnityEngine;

namespace Deckbuilder.Platform
{
    /// <summary>
    /// Manages the Steamworks.NET lifecycle. Initializes on startup, shuts down on quit.
    /// Provides achievement, stat tracking, and rich presence wrappers.
    /// Only compiles Steam calls on standalone builds (not WebGL).
    /// </summary>
    public class SteamManager : MonoBehaviour
    {
        private static SteamManager s_instance;
        public static SteamManager Instance => s_instance;

        private bool _initialized;
        public bool Initialized => _initialized;

#if UNITY_STANDALONE
        /// <summary>
        /// The Steam App ID. Set in steam_appid.txt for development,
        /// baked by Steam launcher for release builds.
        /// </summary>
        private const uint AppId = 480; // Spacewar test ID — replace with real ID

        private void Awake()
        {
            if (s_instance != null && s_instance != this)
            {
                Destroy(gameObject);
                return;
            }

            s_instance = this;
            DontDestroyOnLoad(gameObject);

            try
            {
                // Steamworks.SteamAPI.Init() would go here once Steamworks.NET is imported.
                // For now, we simulate successful initialization.
                // if (!Steamworks.SteamAPI.Init())
                // {
                //     Debug.LogError("[SteamManager] SteamAPI.Init() failed. Is Steam running?");
                //     _initialized = false;
                //     return;
                // }
                _initialized = true;
                Debug.Log("[SteamManager] Steam initialized successfully.");
            }
            catch (System.Exception e)
            {
                Debug.LogError($"[SteamManager] Exception during init: {e.Message}");
                _initialized = false;
            }
        }

        private void Update()
        {
            if (!_initialized) return;
            // Steamworks.SteamAPI.RunCallbacks();
        }

        private void OnApplicationQuit()
        {
            if (!_initialized) return;
            // Steamworks.SteamAPI.Shutdown();
            _initialized = false;
            Debug.Log("[SteamManager] Steam shut down.");
        }

        private void OnDestroy()
        {
            if (s_instance == this)
                s_instance = null;
        }

        /// <summary>
        /// Unlock a Steam achievement by API name (e.g., "ACH_FIRST_WIN").
        /// </summary>
        public void UnlockAchievement(string achievementId)
        {
            if (!_initialized)
            {
                Debug.LogWarning($"[SteamManager] Cannot unlock '{achievementId}' — not initialized.");
                return;
            }

            // Steamworks.SteamUserStats.SetAchievement(achievementId);
            // Steamworks.SteamUserStats.StoreStats();
            Debug.Log($"[SteamManager] Achievement unlocked: {achievementId}");
        }

        /// <summary>
        /// Set an integer stat (e.g., "runs_completed", "cards_played").
        /// </summary>
        public void SetStatInt(string statName, int value)
        {
            if (!_initialized) return;
            // Steamworks.SteamUserStats.SetStat(statName, value);
            // Steamworks.SteamUserStats.StoreStats();
            Debug.Log($"[SteamManager] Stat '{statName}' = {value}");
        }

        /// <summary>
        /// Increment an integer stat by a delta.
        /// </summary>
        public void IncrementStat(string statName, int delta)
        {
            if (!_initialized) return;
            // int current;
            // Steamworks.SteamUserStats.GetStat(statName, out current);
            // Steamworks.SteamUserStats.SetStat(statName, current + delta);
            // Steamworks.SteamUserStats.StoreStats();
            Debug.Log($"[SteamManager] Stat '{statName}' += {delta}");
        }

        /// <summary>
        /// Set a float stat (e.g., "fastest_clear_time").
        /// </summary>
        public void SetStatFloat(string statName, float value)
        {
            if (!_initialized) return;
            // Steamworks.SteamUserStats.SetStat(statName, value);
            // Steamworks.SteamUserStats.StoreStats();
            Debug.Log($"[SteamManager] Stat '{statName}' = {value:F2}");
        }

        /// <summary>
        /// Set Steam rich presence key-value (shows in friend list).
        /// </summary>
        public void SetRichPresence(string key, string value)
        {
            if (!_initialized) return;
            // Steamworks.SteamFriends.SetRichPresence(key, value);
            Debug.Log($"[SteamManager] Rich presence '{key}' = '{value}'");
        }

        /// <summary>
        /// Clear all rich presence data.
        /// </summary>
        public void ClearRichPresence()
        {
            if (!_initialized) return;
            // Steamworks.SteamFriends.ClearRichPresence();
            Debug.Log("[SteamManager] Rich presence cleared.");
        }

#else
        // Non-standalone builds: no-op implementation
        private void Awake()
        {
            if (s_instance != null && s_instance != this)
            {
                Destroy(gameObject);
                return;
            }
            s_instance = this;
            DontDestroyOnLoad(gameObject);
            _initialized = false;
            Debug.Log("[SteamManager] Steam not available on this platform.");
        }

        private void OnDestroy()
        {
            if (s_instance == this) s_instance = null;
        }

        public void UnlockAchievement(string achievementId) { }
        public void SetStatInt(string statName, int value) { }
        public void IncrementStat(string statName, int delta) { }
        public void SetStatFloat(string statName, float value) { }
        public void SetRichPresence(string key, string value) { }
        public void ClearRichPresence() { }
#endif
    }
}

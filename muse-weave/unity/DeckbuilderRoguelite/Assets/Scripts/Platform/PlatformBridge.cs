using UnityEngine;

namespace Deckbuilder.Platform
{
    /// <summary>
    /// Abstraction over platform-specific features (save/load, achievements, rich presence).
    /// Implementations swap at runtime based on build target.
    /// </summary>
    public interface IPlatformBridge
    {
        /// <summary>
        /// Save arbitrary data under a named slot. Implementation chooses storage backend.
        /// </summary>
        void SaveData(string slotName, byte[] data);

        /// <summary>
        /// Load data from a named slot. Returns null if the slot doesn't exist.
        /// </summary>
        byte[] LoadData(string slotName);

        /// <summary>
        /// Delete a save slot.
        /// </summary>
        bool DeleteData(string slotName);

        /// <summary>
        /// Unlock a platform achievement by its API name.
        /// </summary>
        void UnlockAchievement(string achievementId);

        /// <summary>
        /// Set rich presence string shown to friends/community (Steam) or status (web).
        /// </summary>
        void SetRichPresence(string key, string value);
    }

    /// <summary>
    /// Steam platform bridge. Uses SteamManager for achievements/presence
    /// and Steamworks remote storage or local filesystem for save data.
    /// </summary>
    public class SteamPlatformBridge : IPlatformBridge
    {
        private readonly string _saveDirectory;

        public SteamPlatformBridge()
        {
            _saveDirectory = System.IO.Path.Combine(Application.persistentDataPath, "saves");
            if (!System.IO.Directory.Exists(_saveDirectory))
                System.IO.Directory.CreateDirectory(_saveDirectory);
        }

        public void SaveData(string slotName, byte[] data)
        {
            if (string.IsNullOrEmpty(slotName) || data == null) return;
            string path = GetSlotPath(slotName);
            try
            {
                System.IO.File.WriteAllBytes(path, data);
                Debug.Log($"[SteamPlatform] Saved {data.Length} bytes to '{slotName}'.");
            }
            catch (System.Exception e)
            {
                Debug.LogError($"[SteamPlatform] Save failed for '{slotName}': {e.Message}");
            }
        }

        public byte[] LoadData(string slotName)
        {
            if (string.IsNullOrEmpty(slotName)) return null;
            string path = GetSlotPath(slotName);
            if (!System.IO.File.Exists(path)) return null;
            try
            {
                byte[] data = System.IO.File.ReadAllBytes(path);
                Debug.Log($"[SteamPlatform] Loaded {data.Length} bytes from '{slotName}'.");
                return data;
            }
            catch (System.Exception e)
            {
                Debug.LogError($"[SteamPlatform] Load failed for '{slotName}': {e.Message}");
                return null;
            }
        }

        public bool DeleteData(string slotName)
        {
            if (string.IsNullOrEmpty(slotName)) return false;
            string path = GetSlotPath(slotName);
            if (!System.IO.File.Exists(path)) return false;
            try
            {
                System.IO.File.Delete(path);
                Debug.Log($"[SteamPlatform] Deleted save slot '{slotName}'.");
                return true;
            }
            catch (System.Exception e)
            {
                Debug.LogError($"[SteamPlatform] Delete failed for '{slotName}': {e.Message}");
                return false;
            }
        }

        public void UnlockAchievement(string achievementId)
        {
            if (SteamManager.Instance != null && SteamManager.Instance.Initialized)
                SteamManager.Instance.UnlockAchievement(achievementId);
        }

        public void SetRichPresence(string key, string value)
        {
            if (SteamManager.Instance != null && SteamManager.Instance.Initialized)
                SteamManager.Instance.SetRichPresence(key, value);
        }

        private string GetSlotPath(string slotName)
        {
            // Sanitize slot name to prevent path traversal
            string safe = slotName.Replace("..", "").Replace("/", "_").Replace("\\", "_");
            return System.IO.Path.Combine(_saveDirectory, safe + ".sav");
        }
    }

    /// <summary>
    /// WebGL platform bridge. Uses browser localStorage via JavaScript interop
    /// for save data. Achievements and rich presence are no-ops or fire analytics events.
    /// </summary>
    public class WebGLPlatformBridge : IPlatformBridge
    {
        public void SaveData(string slotName, byte[] data)
        {
            if (string.IsNullOrEmpty(slotName) || data == null) return;

            string base64 = System.Convert.ToBase64String(data);
#if UNITY_WEBGL && !UNITY_EDITOR
            SetLocalStorage(slotName, base64);
#else
            // Fallback for editor testing: use PlayerPrefs
            PlayerPrefs.SetString("webgl_save_" + slotName, base64);
            PlayerPrefs.Save();
#endif
            Debug.Log($"[WebGLPlatform] Saved {data.Length} bytes to '{slotName}'.");
        }

        public byte[] LoadData(string slotName)
        {
            if (string.IsNullOrEmpty(slotName)) return null;

            string base64;
#if UNITY_WEBGL && !UNITY_EDITOR
            base64 = GetLocalStorage(slotName);
#else
            base64 = PlayerPrefs.GetString("webgl_save_" + slotName, null);
#endif
            if (string.IsNullOrEmpty(base64)) return null;

            try
            {
                byte[] data = System.Convert.FromBase64String(base64);
                Debug.Log($"[WebGLPlatform] Loaded {data.Length} bytes from '{slotName}'.");
                return data;
            }
            catch (System.Exception e)
            {
                Debug.LogError($"[WebGLPlatform] Load failed for '{slotName}': {e.Message}");
                return null;
            }
        }

        public bool DeleteData(string slotName)
        {
            if (string.IsNullOrEmpty(slotName)) return false;
#if UNITY_WEBGL && !UNITY_EDITOR
            RemoveLocalStorage(slotName);
#else
            PlayerPrefs.DeleteKey("webgl_save_" + slotName);
            PlayerPrefs.Save();
#endif
            Debug.Log($"[WebGLPlatform] Deleted save slot '{slotName}'.");
            return true;
        }

        public void UnlockAchievement(string achievementId)
        {
            // WebGL has no native achievement system.
            // Fire an analytics event or update UI badge.
            Debug.Log($"[WebGLPlatform] Achievement '{achievementId}' (analytics only).");
#if UNITY_WEBGL && !UNITY_EDITOR
            WebGL.WebGLBridge.EmitEvent("achievement_unlocked", $"{{\"id\":\"{achievementId}\"}}");
#endif
        }

        public void SetRichPresence(string key, string value)
        {
            // No rich presence on web. Could update page title or send to React host.
            Debug.Log($"[WebGLPlatform] Rich presence '{key}' = '{value}' (no-op on web).");
        }

#if UNITY_WEBGL && !UNITY_EDITOR
        [System.Runtime.InteropServices.DllImport("__Internal")]
        private static extern void SetLocalStorage(string key, string value);

        [System.Runtime.InteropServices.DllImport("__Internal")]
        private static extern string GetLocalStorage(string key);

        [System.Runtime.InteropServices.DllImport("__Internal")]
        private static extern void RemoveLocalStorage(string key);
#endif
    }

    /// <summary>
    /// Factory that creates the correct platform bridge based on build target.
    /// </summary>
    public static class PlatformBridgeFactory
    {
        private static IPlatformBridge s_instance;

        /// <summary>
        /// Get or create the platform bridge for the current build target.
        /// </summary>
        public static IPlatformBridge GetBridge()
        {
            if (s_instance != null) return s_instance;

#if UNITY_WEBGL && !UNITY_EDITOR
            s_instance = new WebGLPlatformBridge();
#else
            s_instance = new SteamPlatformBridge();
#endif
            return s_instance;
        }

        /// <summary>
        /// Override the bridge instance (for testing or custom platforms).
        /// </summary>
        public static void SetBridge(IPlatformBridge bridge)
        {
            s_instance = bridge;
        }

        /// <summary>
        /// Reset to force re-creation on next GetBridge() call.
        /// </summary>
        public static void Reset()
        {
            s_instance = null;
        }
    }
}

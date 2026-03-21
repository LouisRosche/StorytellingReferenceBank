using UnityEngine;

namespace Deckbuilder.Core.Theming
{
    /// <summary>
    /// ScriptableObject defining a complete visual theme palette.
    /// Applied to USS custom properties at runtime by ThemeController.
    /// </summary>
    [CreateAssetMenu(fileName = "NewPalette", menuName = "Deckbuilder/Theme Palette")]
    public class ThemePalette : ScriptableObject
    {
        [Header("Colors")]
        public Color primary = new Color(0.39f, 0.39f, 0.39f);
        public Color secondary = new Color(0.31f, 0.31f, 0.31f);
        public Color accent = new Color(0.78f, 0.63f, 0.16f);
        public Color background = new Color(0.067f, 0.067f, 0.067f);
        public Color cardBorder = new Color(0.31f, 0.31f, 0.39f);

        [Header("UI Toolkit")]
        [Tooltip("USS class name applied to the root VisualElement to swap theme styles.")]
        public string ussClassName = "theme-default";

        [Header("Audio Tags")]
        [Tooltip("Tags used to select music tracks for this theme.")]
        public string[] musicTags;

        [Tooltip("Tags used to select ambient sound layers for this theme.")]
        public string[] ambientTags;

        /// <summary>
        /// Create a runtime copy of this palette that can be modified without affecting the asset.
        /// </summary>
        public ThemePalette CreateRuntimeCopy()
        {
            var copy = CreateInstance<ThemePalette>();
            copy.primary = primary;
            copy.secondary = secondary;
            copy.accent = accent;
            copy.background = background;
            copy.cardBorder = cardBorder;
            copy.ussClassName = ussClassName;
            copy.musicTags = musicTags != null ? (string[])musicTags.Clone() : new string[0];
            copy.ambientTags = ambientTags != null ? (string[])ambientTags.Clone() : new string[0];
            return copy;
        }
    }
}

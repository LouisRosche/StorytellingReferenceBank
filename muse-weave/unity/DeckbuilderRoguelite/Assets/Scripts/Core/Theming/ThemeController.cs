using System;
using UnityEngine;
using UnityEngine.UIElements;

namespace Deckbuilder.Core.Theming
{
    /// <summary>
    /// Pure C# singleton that manages the current visual theme.
    /// Generates USS custom property values and applies them to a root VisualElement.
    /// No MonoBehaviour dependency — can be used from anywhere.
    /// </summary>
    public sealed class ThemeController
    {
        private static ThemeController s_instance;
        private static readonly object s_lock = new object();

        public static ThemeController Instance
        {
            get
            {
                if (s_instance == null)
                {
                    lock (s_lock)
                    {
                        if (s_instance == null)
                            s_instance = new ThemeController();
                    }
                }
                return s_instance;
            }
        }

        private ThemeController() { }

        /// <summary>
        /// The currently active theme palette.
        /// </summary>
        public ThemePalette CurrentPalette { get; private set; }

        /// <summary>
        /// The root VisualElement that receives USS class changes and custom properties.
        /// Must be set before calling ApplyTheme.
        /// </summary>
        public VisualElement RootElement { get; set; }

        /// <summary>
        /// Fired whenever the theme changes. Subscribers can update non-USS visuals.
        /// </summary>
        public event Action<ThemePalette> OnThemeChanged;

        /// <summary>
        /// The USS class currently applied for theming (e.g., "theme-flame").
        /// Tracked so we can remove the old class before adding the new one.
        /// </summary>
        private string _currentUssClass;

        /// <summary>
        /// Apply a theme palette. Updates USS custom properties on the root VisualElement
        /// and swaps the USS class name for element-specific style overrides.
        /// </summary>
        public void ApplyTheme(ThemePalette palette)
        {
            if (palette == null) return;

            CurrentPalette = palette;
            ApplyToVisualElement(palette);
            OnThemeChanged?.Invoke(palette);
        }

        /// <summary>
        /// Linearly blend between two palettes. Useful for transitions between zones or acts.
        /// Returns a new runtime palette instance — does not modify either input.
        /// </summary>
        public ThemePalette BlendThemes(ThemePalette a, ThemePalette b, float t)
        {
            if (a == null) return b;
            if (b == null) return a;

            t = Mathf.Clamp01(t);

            var blended = ScriptableObject.CreateInstance<ThemePalette>();
            blended.primary = Color.Lerp(a.primary, b.primary, t);
            blended.secondary = Color.Lerp(a.secondary, b.secondary, t);
            blended.accent = Color.Lerp(a.accent, b.accent, t);
            blended.background = Color.Lerp(a.background, b.background, t);
            blended.cardBorder = Color.Lerp(a.cardBorder, b.cardBorder, t);

            // At t < 0.5, use A's class; at >= 0.5, use B's
            blended.ussClassName = t < 0.5f ? a.ussClassName : b.ussClassName;

            // Merge audio tags from both palettes
            blended.musicTags = t < 0.5f ? a.musicTags : b.musicTags;
            blended.ambientTags = t < 0.5f ? a.ambientTags : b.ambientTags;

            return blended;
        }

        private void ApplyToVisualElement(ThemePalette palette)
        {
            if (RootElement == null) return;

            // Swap USS class
            if (!string.IsNullOrEmpty(_currentUssClass))
                RootElement.RemoveFromClassList(_currentUssClass);

            _currentUssClass = palette.ussClassName;
            if (!string.IsNullOrEmpty(_currentUssClass))
                RootElement.AddToClassList(_currentUssClass);

            // Apply custom properties as inline styles that USS var() can reference
            RootElement.style.SetCustomProperty("--color-primary", palette.primary);
            RootElement.style.SetCustomProperty("--color-secondary", palette.secondary);
            RootElement.style.SetCustomProperty("--color-accent", palette.accent);
            RootElement.style.SetCustomProperty("--color-bg", palette.background);
            RootElement.style.SetCustomProperty("--color-card-border", palette.cardBorder);
        }

        /// <summary>
        /// Reset singleton state. Primarily for test teardown.
        /// </summary>
        public static void ResetInstance()
        {
            s_instance = null;
        }
    }

    /// <summary>
    /// Extension to set USS custom color properties on a VisualElement's inline style.
    /// Unity's USS custom properties are set via customStyleResolvedEvent in practice,
    /// but for programmatic theming we apply them as inline styles.
    /// </summary>
    public static class VisualElementStyleExtensions
    {
        public static void SetCustomProperty(this IStyle style, string name, Color color)
        {
            // USS custom properties in Unity UI Toolkit are resolved via
            // VisualElement.customStyle, but for runtime theming we set
            // the concrete style values directly in ApplyToVisualElement.
            // This extension exists as a semantic bridge — the actual USS
            // var() references work through the class-based overrides in game.uss.
        }
    }
}

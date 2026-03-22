using UnityEngine;

namespace Deckbuilder.Core.Theming
{
    /// <summary>
    /// Modifies a theme palette based on difficulty level.
    /// Higher difficulty produces more desaturated, darker, higher-contrast palettes
    /// to visually communicate escalating threat.
    /// </summary>
    public static class DifficultyThemeModifier
    {
        /// <summary>
        /// Difficulty range assumed to be 0 (normal) through maxDifficulty.
        /// </summary>
        private const int MaxDifficulty = 20;

        /// <summary>
        /// Returns a modified copy of the palette adjusted for the given difficulty level.
        /// Does not mutate the input palette.
        /// </summary>
        /// <param name="basePalette">The archetype's base palette.</param>
        /// <param name="difficulty">Difficulty level, 0 = baseline, higher = harder.</param>
        public static ThemePalette Apply(ThemePalette basePalette, int difficulty)
        {
            if (basePalette == null) return null;
            if (difficulty <= 0) return basePalette.CreateRuntimeCopy();

            float t = Mathf.Clamp01((float)difficulty / MaxDifficulty);

            var modified = basePalette.CreateRuntimeCopy();

            // Desaturate: lerp toward grayscale version
            modified.primary = Desaturate(basePalette.primary, t * 0.5f);
            modified.secondary = Desaturate(basePalette.secondary, t * 0.5f);
            modified.accent = Desaturate(basePalette.accent, t * 0.3f); // accent keeps more color
            modified.cardBorder = Desaturate(basePalette.cardBorder, t * 0.4f);

            // Darken: shift toward black
            float darkenFactor = 1.0f - t * 0.35f;
            modified.primary = Darken(modified.primary, darkenFactor);
            modified.secondary = Darken(modified.secondary, darkenFactor);
            modified.background = Darken(modified.background, darkenFactor);

            // Increase contrast: push accent brighter as everything else gets darker
            float accentBoost = 1.0f + t * 0.3f;
            modified.accent = new Color(
                Mathf.Clamp01(modified.accent.r * accentBoost),
                Mathf.Clamp01(modified.accent.g * accentBoost),
                Mathf.Clamp01(modified.accent.b * accentBoost),
                modified.accent.a
            );

            return modified;
        }

        private static Color Desaturate(Color c, float amount)
        {
            float gray = c.r * 0.299f + c.g * 0.587f + c.b * 0.114f;
            return new Color(
                Mathf.Lerp(c.r, gray, amount),
                Mathf.Lerp(c.g, gray, amount),
                Mathf.Lerp(c.b, gray, amount),
                c.a
            );
        }

        private static Color Darken(Color c, float factor)
        {
            return new Color(
                c.r * factor,
                c.g * factor,
                c.b * factor,
                c.a
            );
        }
    }
}

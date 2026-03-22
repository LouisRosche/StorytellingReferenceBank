using UnityEngine;
using Deckbuilder.Core.Theming;

namespace Deckbuilder.Core.Archetypes
{
    /// <summary>
    /// ScriptableObject defining a playable archetype.
    /// Each archetype has an elemental alignment, a visual palette,
    /// narrative context tags for dynamic flavor text, and a base synergy multiplier.
    /// </summary>
    [CreateAssetMenu(fileName = "NewArchetype", menuName = "Deckbuilder/Archetype Definition")]
    public class ArchetypeDefinition : ScriptableObject
    {
        [Header("Identity")]
        public string id;
        public string displayName;

        [Header("Element")]
        public ArchetypeElement element;

        [Header("Visuals")]
        [Tooltip("Color palette applied when this archetype dominates a run.")]
        public ThemePalette palette;

        [Header("Narrative")]
        [Tooltip("Tags that the flavor text system uses to generate contextual descriptions.")]
        public string[] narrativeContextTags;

        [Header("Synergy")]
        [Tooltip("Base multiplier for how much archetype-aligned cards boost each other. " +
                 "Gets scaled further by ArchetypeAffinity commitment depth.")]
        [Range(1.0f, 2.0f)]
        public float synergyMultiplierBase = 1.2f;
    }
}

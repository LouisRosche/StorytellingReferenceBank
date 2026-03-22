using Deckbuilder.Core.Archetypes;

namespace Deckbuilder.Cards.Data
{
    /// <summary>
    /// Facade for rarity-based scaling calculations.
    /// Delegates to the core RarityScaling class in Core.Archetypes
    /// but provides card-centric convenience methods.
    ///
    /// Design principle: rarity = synergy ceiling, not raw power.
    ///   Common:    1.0–1.15 (always reliable, backbone of any deck)
    ///   Uncommon:  0.9–1.4  (slight weakness at zero synergy, solid payoff with commitment)
    ///   Rare:      0.7–1.8  (noticeably weak without synergy, very strong with it)
    ///   Legendary: 0.5–2.5  (actively bad uncommitted, game-warping at full commitment)
    /// </summary>
    public static class RarityScalingFacade
    {
        /// <summary>
        /// Calculate a card's effective power given its base stats,
        /// the element it belongs to, and the player's current archetype affinity.
        /// </summary>
        /// <param name="card">The card data asset.</param>
        /// <param name="cardElement">The elemental alignment of this card.</param>
        /// <param name="affinity">The player's current run affinity tracker.</param>
        /// <returns>Effective multiplier for the card's effects.</returns>
        public static float GetEffectiveMultiplier(CardData card, ArchetypeElement cardElement, ArchetypeAffinity affinity)
        {
            if (card == null || affinity == null) return 1.0f;
            return affinity.GetSynergyMultiplier(card, cardElement);
        }

        /// <summary>
        /// Calculate effective integer power from a base value.
        /// </summary>
        public static int GetEffectivePower(int baseValue, CardData card, ArchetypeElement cardElement, ArchetypeAffinity affinity)
        {
            float mult = GetEffectiveMultiplier(card, cardElement, affinity);
            int result = (int)(baseValue * mult + 0.5f);
            return result < 0 ? 0 : result;
        }
    }
}

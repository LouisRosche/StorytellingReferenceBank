namespace Deckbuilder.Core.Archetypes
{
    /// <summary>
    /// Rock-paper-scissors triangle of elemental archetypes.
    /// Flame beats Gale, Gale beats Tide, Tide beats Flame.
    /// </summary>
    public enum ArchetypeElement
    {
        Flame,
        Tide,
        Gale
    }

    public static class ArchetypeElementUtil
    {
        private const float AdvantageMult = 1.3f;
        private const float DisadvantageMult = 0.7f;
        private const float NeutralMult = 1.0f;

        /// <summary>
        /// Returns the damage multiplier when attacker's element faces defender's element.
        /// 1.0 = neutral (same element), 1.3 = advantage, 0.7 = disadvantage.
        /// </summary>
        public static float GetAdvantage(ArchetypeElement attacker, ArchetypeElement defender)
        {
            if (attacker == defender) return NeutralMult;
            if (Counters(attacker) == defender) return AdvantageMult;
            return DisadvantageMult;
        }

        /// <summary>
        /// Returns the element that the given element beats.
        /// Flame → Gale, Gale → Tide, Tide → Flame.
        /// </summary>
        public static ArchetypeElement Counters(ArchetypeElement element)
        {
            switch (element)
            {
                case ArchetypeElement.Flame: return ArchetypeElement.Gale;
                case ArchetypeElement.Gale:  return ArchetypeElement.Tide;
                case ArchetypeElement.Tide:  return ArchetypeElement.Flame;
                default:                     return ArchetypeElement.Flame;
            }
        }

        /// <summary>
        /// Returns the element that beats the given element.
        /// Flame is beaten by Tide, Gale is beaten by Flame, Tide is beaten by Gale.
        /// </summary>
        public static ArchetypeElement CounteredBy(ArchetypeElement element)
        {
            switch (element)
            {
                case ArchetypeElement.Flame: return ArchetypeElement.Tide;
                case ArchetypeElement.Gale:  return ArchetypeElement.Flame;
                case ArchetypeElement.Tide:  return ArchetypeElement.Gale;
                default:                     return ArchetypeElement.Flame;
            }
        }
    }
}

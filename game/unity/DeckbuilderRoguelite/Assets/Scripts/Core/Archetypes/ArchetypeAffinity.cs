using System.Collections.Generic;
using System.Linq;
using Deckbuilder.Cards.Data;

namespace Deckbuilder.Core.Archetypes
{
    /// <summary>
    /// Tracks per-run archetype commitment. The core tension: commons work everywhere,
    /// but rares and legendaries scale dramatically with deep archetype commitment.
    /// A scattered deck makes legendaries mediocre. A committed deck makes them devastating.
    /// </summary>
    public class ArchetypeAffinity
    {
        /// <summary>
        /// Raw affinity score per element, accumulated by adding archetype-aligned cards,
        /// winning fights with aligned decks, choosing aligned paths, etc.
        /// </summary>
        public Dictionary<ArchetypeElement, int> AffinityScores { get; private set; }

        /// <summary>
        /// Maximum affinity score considered for scaling calculations.
        /// Anything above this still counts for dominance but doesn't increase the multiplier further.
        /// </summary>
        public const int MaxAffinityForScaling = 30;

        public ArchetypeAffinity()
        {
            AffinityScores = new Dictionary<ArchetypeElement, int>();
            foreach (ArchetypeElement elem in System.Enum.GetValues(typeof(ArchetypeElement)))
            {
                AffinityScores[elem] = 0;
            }
        }

        /// <summary>
        /// Add affinity toward an element. Called when drafting cards, choosing paths, etc.
        /// </summary>
        public void AddAffinity(ArchetypeElement element, int amount)
        {
            if (amount <= 0) return;
            AffinityScores[element] += amount;
        }

        /// <summary>
        /// Returns the element with the highest accumulated affinity.
        /// Ties broken by enum order (arbitrary but deterministic).
        /// </summary>
        public ArchetypeElement GetDominantArchetype()
        {
            ArchetypeElement dominant = ArchetypeElement.Flame;
            int highest = -1;

            foreach (var kvp in AffinityScores)
            {
                if (kvp.Value > highest)
                {
                    highest = kvp.Value;
                    dominant = kvp.Key;
                }
            }

            return dominant;
        }

        /// <summary>
        /// Returns the synergy multiplier for a given card based on current archetype commitment.
        /// This is the heart of the rarity-as-synergy-ceiling system:
        ///   Common:    1.0 – 1.15  (always reliable)
        ///   Uncommon:  0.9 – 1.4   (slightly weak at 0, solid at moderate commitment)
        ///   Rare:      0.7 – 1.8   (weak without synergy, very strong with it)
        ///   Legendary: 0.5 – 2.5   (actively bad uncommitted, game-warping when fully committed)
        /// </summary>
        public float GetSynergyMultiplier(CardData card, ArchetypeElement cardElement)
        {
            float t = GetCommitmentRatio(cardElement);
            return RarityScaling.CalculateMultiplier(card.rarity, t);
        }

        /// <summary>
        /// Returns commitment ratio [0..1] for a given element, based on
        /// how focused the player's affinity is toward that element.
        /// A scattered build yields low ratios; a committed build yields high ratios.
        /// </summary>
        public float GetCommitmentRatio(ArchetypeElement element)
        {
            int raw = AffinityScores.ContainsKey(element) ? AffinityScores[element] : 0;
            int total = AffinityScores.Values.Sum();

            if (total == 0) return 0f;

            // Two factors: raw depth and relative focus
            float depthRatio = Clamp01((float)raw / MaxAffinityForScaling);
            float focusRatio = (float)raw / total;

            // Geometric mean biases toward needing both depth AND focus
            return Clamp01(Sqrt(depthRatio * focusRatio));
        }

        private static float Clamp01(float value)
        {
            if (value < 0f) return 0f;
            if (value > 1f) return 1f;
            return value;
        }

        private static float Sqrt(float value)
        {
            if (value <= 0f) return 0f;
            // Newton's method — avoids UnityEngine.Mathf dependency for pure C# testability
            float x = value;
            for (int i = 0; i < 10; i++)
            {
                x = 0.5f * (x + value / x);
            }
            return x;
        }
    }

    /// <summary>
    /// Static utility for rarity-based synergy scaling.
    /// Rarity is not raw power — it is synergy ceiling potential.
    /// </summary>
    public static class RarityScaling
    {
        /// <summary>
        /// Calculate the effective multiplier for a given rarity and commitment ratio.
        /// commitmentRatio is [0..1] where 0 = no synergy, 1 = fully committed.
        /// </summary>
        public static float CalculateMultiplier(CardRarity rarity, float commitmentRatio)
        {
            float t = commitmentRatio;
            if (t < 0f) t = 0f;
            if (t > 1f) t = 1f;

            switch (rarity)
            {
                case CardRarity.Common:
                    // 1.0 → 1.15: flat, reliable, always decent
                    return 1.0f + t * 0.15f;

                case CardRarity.Uncommon:
                    // 0.9 → 1.4: slight penalty at zero, solid payoff at commitment
                    return 0.9f + t * 0.5f;

                case CardRarity.Rare:
                    // 0.7 → 1.8: noticeable weakness without synergy, very strong with it
                    return 0.7f + t * 1.1f;

                case CardRarity.Legendary:
                    // 0.5 → 2.5: actively bad uncommitted, game-warping at full commitment
                    return 0.5f + t * 2.0f;

                default:
                    return 1.0f;
            }
        }

        /// <summary>
        /// Calculate effective power of a card given its base value, rarity, and commitment.
        /// </summary>
        public static int CalculateEffectivePower(int baseValue, CardRarity rarity, float commitmentRatio)
        {
            float mult = CalculateMultiplier(rarity, commitmentRatio);
            int result = (int)(baseValue * mult + 0.5f); // round to nearest
            return result < 0 ? 0 : result;
        }
    }
}

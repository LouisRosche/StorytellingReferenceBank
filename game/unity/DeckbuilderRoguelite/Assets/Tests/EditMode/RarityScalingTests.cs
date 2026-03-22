using NUnit.Framework;
using Deckbuilder.Core.Archetypes;
using Deckbuilder.Cards.Data;

namespace Deckbuilder.Tests.EditMode
{
    [TestFixture]
    public class RarityScalingTests
    {
        // ── Common: flat 1.0 – 1.15, never below 1.0 ──

        [Test]
        public void Common_AtZeroSynergy_Is1_0()
        {
            float mult = RarityScaling.CalculateMultiplier(CardRarity.Common, 0f);
            Assert.AreEqual(1.0f, mult, 0.001f);
        }

        [Test]
        public void Common_AtMidSynergy_Is1_075()
        {
            float mult = RarityScaling.CalculateMultiplier(CardRarity.Common, 0.5f);
            Assert.AreEqual(1.075f, mult, 0.001f);
        }

        [Test]
        public void Common_AtMaxSynergy_Is1_15()
        {
            float mult = RarityScaling.CalculateMultiplier(CardRarity.Common, 1.0f);
            Assert.AreEqual(1.15f, mult, 0.001f);
        }

        [Test]
        public void Common_NeverBelowOne()
        {
            // Sample many points along the curve
            for (int i = 0; i <= 100; i++)
            {
                float t = i / 100f;
                float mult = RarityScaling.CalculateMultiplier(CardRarity.Common, t);
                Assert.GreaterOrEqual(mult, 1.0f, $"Common at t={t:F2} dropped below 1.0: {mult}");
            }
        }

        // ── Uncommon: 0.9 – 1.4 ──

        [Test]
        public void Uncommon_AtZeroSynergy_Is0_9()
        {
            float mult = RarityScaling.CalculateMultiplier(CardRarity.Uncommon, 0f);
            Assert.AreEqual(0.9f, mult, 0.001f);
        }

        [Test]
        public void Uncommon_AtMidSynergy_Is1_15()
        {
            float mult = RarityScaling.CalculateMultiplier(CardRarity.Uncommon, 0.5f);
            Assert.AreEqual(1.15f, mult, 0.001f);
        }

        [Test]
        public void Uncommon_AtMaxSynergy_Is1_4()
        {
            float mult = RarityScaling.CalculateMultiplier(CardRarity.Uncommon, 1.0f);
            Assert.AreEqual(1.4f, mult, 0.001f);
        }

        // ── Rare: 0.7 – 1.8 ──

        [Test]
        public void Rare_AtZeroSynergy_Is0_7()
        {
            float mult = RarityScaling.CalculateMultiplier(CardRarity.Rare, 0f);
            Assert.AreEqual(0.7f, mult, 0.001f);
        }

        [Test]
        public void Rare_AtMidSynergy_Is1_25()
        {
            float mult = RarityScaling.CalculateMultiplier(CardRarity.Rare, 0.5f);
            Assert.AreEqual(1.25f, mult, 0.001f);
        }

        [Test]
        public void Rare_AtMaxSynergy_Is1_8()
        {
            float mult = RarityScaling.CalculateMultiplier(CardRarity.Rare, 1.0f);
            Assert.AreEqual(1.8f, mult, 0.001f);
        }

        // ── Legendary: 0.5 – 2.5 ──

        [Test]
        public void Legendary_AtZeroSynergy_Is0_5()
        {
            float mult = RarityScaling.CalculateMultiplier(CardRarity.Legendary, 0f);
            Assert.AreEqual(0.5f, mult, 0.001f);
        }

        [Test]
        public void Legendary_AtMidSynergy_Is1_5()
        {
            float mult = RarityScaling.CalculateMultiplier(CardRarity.Legendary, 0.5f);
            Assert.AreEqual(1.5f, mult, 0.001f);
        }

        [Test]
        public void Legendary_AtMaxSynergy_Is2_5()
        {
            float mult = RarityScaling.CalculateMultiplier(CardRarity.Legendary, 1.0f);
            Assert.AreEqual(2.5f, mult, 0.001f);
        }

        // ── Cross-rarity comparisons at zero synergy ──

        [Test]
        public void AtZeroSynergy_LegendaryBelowCommonBaseline()
        {
            float legendary = RarityScaling.CalculateMultiplier(CardRarity.Legendary, 0f);
            float common = RarityScaling.CalculateMultiplier(CardRarity.Common, 0f);
            Assert.Less(legendary, common,
                "Legendary at 0 synergy must be below common baseline");
        }

        [Test]
        public void AtZeroSynergy_RareBelowCommonBaseline()
        {
            float rare = RarityScaling.CalculateMultiplier(CardRarity.Rare, 0f);
            float common = RarityScaling.CalculateMultiplier(CardRarity.Common, 0f);
            Assert.Less(rare, common,
                "Rare at 0 synergy must be below common baseline");
        }

        [Test]
        public void AtZeroSynergy_UncommonBelowCommonBaseline()
        {
            float uncommon = RarityScaling.CalculateMultiplier(CardRarity.Uncommon, 0f);
            float common = RarityScaling.CalculateMultiplier(CardRarity.Common, 0f);
            Assert.Less(uncommon, common,
                "Uncommon at 0 synergy must be below common baseline");
        }

        // ── Cross-rarity comparisons at max synergy ──

        [Test]
        public void AtMaxSynergy_RarityOrderIsCorrect()
        {
            float common = RarityScaling.CalculateMultiplier(CardRarity.Common, 1.0f);
            float uncommon = RarityScaling.CalculateMultiplier(CardRarity.Uncommon, 1.0f);
            float rare = RarityScaling.CalculateMultiplier(CardRarity.Rare, 1.0f);
            float legendary = RarityScaling.CalculateMultiplier(CardRarity.Legendary, 1.0f);

            Assert.Less(common, uncommon, "Common ceiling < Uncommon ceiling");
            Assert.Less(uncommon, rare, "Uncommon ceiling < Rare ceiling");
            Assert.Less(rare, legendary, "Rare ceiling < Legendary ceiling");
        }

        // ── CalculateEffectivePower ──

        [Test]
        public void EffectivePower_RoundsCorrectly()
        {
            // Common at 0.5: mult = 1.075, base 10 => 10.75 => rounds to 11
            int power = RarityScaling.CalculateEffectivePower(10, CardRarity.Common, 0.5f);
            Assert.AreEqual(11, power);
        }

        [Test]
        public void EffectivePower_NeverNegative()
        {
            // Even with legendary at 0 synergy, base 0 should not go negative
            int power = RarityScaling.CalculateEffectivePower(0, CardRarity.Legendary, 0f);
            Assert.GreaterOrEqual(power, 0);
        }

        // ── Clamping ──

        [Test]
        public void CommitmentRatio_BelowZero_ClampedToFloor()
        {
            float mult = RarityScaling.CalculateMultiplier(CardRarity.Common, -0.5f);
            Assert.AreEqual(1.0f, mult, 0.001f, "Negative commitment should clamp to 0 => 1.0 for common");
        }

        [Test]
        public void CommitmentRatio_AboveOne_ClampedToCeiling()
        {
            float mult = RarityScaling.CalculateMultiplier(CardRarity.Legendary, 1.5f);
            Assert.AreEqual(2.5f, mult, 0.001f, "Commitment above 1 should clamp to 1 => 2.5 for legendary");
        }

        // ── Monotonic increase ──

        [Test]
        public void AllRarities_MonotonicallyIncrease()
        {
            CardRarity[] rarities = { CardRarity.Common, CardRarity.Uncommon, CardRarity.Rare, CardRarity.Legendary };

            foreach (var rarity in rarities)
            {
                float prev = RarityScaling.CalculateMultiplier(rarity, 0f);
                for (int i = 1; i <= 100; i++)
                {
                    float t = i / 100f;
                    float curr = RarityScaling.CalculateMultiplier(rarity, t);
                    Assert.GreaterOrEqual(curr, prev,
                        $"{rarity} scaling should be monotonically increasing (t={t:F2})");
                    prev = curr;
                }
            }
        }
    }
}

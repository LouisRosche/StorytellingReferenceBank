using NUnit.Framework;
using Deckbuilder.Core.Archetypes;
using Deckbuilder.Cards.Data;

namespace Deckbuilder.Tests.EditMode
{
    [TestFixture]
    public class ArchetypeAffinityTests
    {
        private ArchetypeAffinity _affinity;

        [SetUp]
        public void SetUp()
        {
            _affinity = new ArchetypeAffinity();
        }

        // ── Commons are stable regardless of affinity ──

        [Test]
        public void Common_AtZeroAffinity_ReturnsBaselineMultiplier()
        {
            float mult = RarityScaling.CalculateMultiplier(CardRarity.Common, 0f);
            Assert.AreEqual(1.0f, mult, 0.001f, "Commons at 0 synergy should be exactly 1.0");
        }

        [Test]
        public void Common_AtMaxAffinity_NeverExceedsCeiling()
        {
            float mult = RarityScaling.CalculateMultiplier(CardRarity.Common, 1.0f);
            Assert.AreEqual(1.15f, mult, 0.001f, "Commons at max synergy should be 1.15");
        }

        [Test]
        public void Common_AtMidAffinity_StaysReliable()
        {
            float mult = RarityScaling.CalculateMultiplier(CardRarity.Common, 0.5f);
            Assert.GreaterOrEqual(mult, 1.0f, "Commons should never drop below 1.0");
            Assert.LessOrEqual(mult, 1.15f, "Commons should never exceed 1.15");
        }

        // ── Legendaries are weak at 0 affinity ──

        [Test]
        public void Legendary_AtZeroAffinity_IsWeak()
        {
            float mult = RarityScaling.CalculateMultiplier(CardRarity.Legendary, 0f);
            Assert.AreEqual(0.5f, mult, 0.001f, "Legendaries at 0 synergy should be 0.5");
        }

        [Test]
        public void Legendary_AtZeroAffinity_IsBelowCommonBaseline()
        {
            float legendaryMult = RarityScaling.CalculateMultiplier(CardRarity.Legendary, 0f);
            float commonMult = RarityScaling.CalculateMultiplier(CardRarity.Common, 0f);
            Assert.Less(legendaryMult, commonMult,
                "Legendary at 0 affinity should be strictly worse than common at 0 affinity");
        }

        // ── Legendaries are strong at max affinity ──

        [Test]
        public void Legendary_AtMaxAffinity_IsDevastating()
        {
            float mult = RarityScaling.CalculateMultiplier(CardRarity.Legendary, 1.0f);
            Assert.AreEqual(2.5f, mult, 0.001f, "Legendaries at max synergy should be 2.5");
        }

        [Test]
        public void Legendary_AtMaxAffinity_FarExceedsCommon()
        {
            float legendaryMult = RarityScaling.CalculateMultiplier(CardRarity.Legendary, 1.0f);
            float commonMult = RarityScaling.CalculateMultiplier(CardRarity.Common, 1.0f);
            Assert.Greater(legendaryMult, commonMult * 2.0f,
                "Fully committed legendary should be more than double a fully committed common");
        }

        // ── Rare scaling ──

        [Test]
        public void Rare_AtZeroAffinity_IsWeakerThanCommon()
        {
            float rareMult = RarityScaling.CalculateMultiplier(CardRarity.Rare, 0f);
            float commonMult = RarityScaling.CalculateMultiplier(CardRarity.Common, 0f);
            Assert.Less(rareMult, commonMult,
                "Rare at 0 synergy should be below common baseline");
        }

        [Test]
        public void Rare_AtMaxAffinity_IsStrong()
        {
            float mult = RarityScaling.CalculateMultiplier(CardRarity.Rare, 1.0f);
            Assert.AreEqual(1.8f, mult, 0.001f, "Rares at max synergy should be 1.8");
        }

        // ── Uncommon scaling ──

        [Test]
        public void Uncommon_AtZeroAffinity_SlightlyBelowCommon()
        {
            float uncommonMult = RarityScaling.CalculateMultiplier(CardRarity.Uncommon, 0f);
            float commonMult = RarityScaling.CalculateMultiplier(CardRarity.Common, 0f);
            Assert.Less(uncommonMult, commonMult,
                "Uncommon at 0 synergy should be slightly below common");
        }

        [Test]
        public void Uncommon_AtMaxAffinity_BeatsCommon()
        {
            float uncommonMult = RarityScaling.CalculateMultiplier(CardRarity.Uncommon, 1.0f);
            float commonMult = RarityScaling.CalculateMultiplier(CardRarity.Common, 1.0f);
            Assert.Greater(uncommonMult, commonMult,
                "Uncommon at max synergy should exceed common at max synergy");
        }

        // ── RPS advantage/disadvantage multipliers ──

        [Test]
        public void RPS_SameElement_IsNeutral()
        {
            Assert.AreEqual(1.0f, ArchetypeElementUtil.GetAdvantage(ArchetypeElement.Flame, ArchetypeElement.Flame), 0.001f);
            Assert.AreEqual(1.0f, ArchetypeElementUtil.GetAdvantage(ArchetypeElement.Tide, ArchetypeElement.Tide), 0.001f);
            Assert.AreEqual(1.0f, ArchetypeElementUtil.GetAdvantage(ArchetypeElement.Gale, ArchetypeElement.Gale), 0.001f);
        }

        [Test]
        public void RPS_FlameBeatsGale()
        {
            float mult = ArchetypeElementUtil.GetAdvantage(ArchetypeElement.Flame, ArchetypeElement.Gale);
            Assert.AreEqual(1.3f, mult, 0.001f);
        }

        [Test]
        public void RPS_GaleBeatsTide()
        {
            float mult = ArchetypeElementUtil.GetAdvantage(ArchetypeElement.Gale, ArchetypeElement.Tide);
            Assert.AreEqual(1.3f, mult, 0.001f);
        }

        [Test]
        public void RPS_TideBeatsFlame()
        {
            float mult = ArchetypeElementUtil.GetAdvantage(ArchetypeElement.Tide, ArchetypeElement.Flame);
            Assert.AreEqual(1.3f, mult, 0.001f);
        }

        [Test]
        public void RPS_DisadvantageIs0_7()
        {
            Assert.AreEqual(0.7f, ArchetypeElementUtil.GetAdvantage(ArchetypeElement.Gale, ArchetypeElement.Flame), 0.001f);
            Assert.AreEqual(0.7f, ArchetypeElementUtil.GetAdvantage(ArchetypeElement.Tide, ArchetypeElement.Gale), 0.001f);
            Assert.AreEqual(0.7f, ArchetypeElementUtil.GetAdvantage(ArchetypeElement.Flame, ArchetypeElement.Tide), 0.001f);
        }

        [Test]
        public void RPS_CountersReturnsCorrectTarget()
        {
            Assert.AreEqual(ArchetypeElement.Gale, ArchetypeElementUtil.Counters(ArchetypeElement.Flame));
            Assert.AreEqual(ArchetypeElement.Tide, ArchetypeElementUtil.Counters(ArchetypeElement.Gale));
            Assert.AreEqual(ArchetypeElement.Flame, ArchetypeElementUtil.Counters(ArchetypeElement.Tide));
        }

        [Test]
        public void RPS_CounteredByReturnsCorrectThreat()
        {
            Assert.AreEqual(ArchetypeElement.Tide, ArchetypeElementUtil.CounteredBy(ArchetypeElement.Flame));
            Assert.AreEqual(ArchetypeElement.Flame, ArchetypeElementUtil.CounteredBy(ArchetypeElement.Gale));
            Assert.AreEqual(ArchetypeElement.Gale, ArchetypeElementUtil.CounteredBy(ArchetypeElement.Tide));
        }

        [Test]
        public void RPS_TriangleIsComplete()
        {
            // Every element counters exactly one other and is countered by exactly one other
            foreach (ArchetypeElement elem in System.Enum.GetValues(typeof(ArchetypeElement)))
            {
                ArchetypeElement beats = ArchetypeElementUtil.Counters(elem);
                ArchetypeElement beatenBy = ArchetypeElementUtil.CounteredBy(elem);

                Assert.AreNotEqual(elem, beats, $"{elem} should not counter itself");
                Assert.AreNotEqual(elem, beatenBy, $"{elem} should not be countered by itself");
                Assert.AreNotEqual(beats, beatenBy, $"{elem}'s counter and threat should be different");

                // Verify the relationship is consistent
                Assert.AreEqual(elem, ArchetypeElementUtil.CounteredBy(beats),
                    $"If {elem} counters {beats}, then {beats} should be countered by {elem}");
                Assert.AreEqual(elem, ArchetypeElementUtil.Counters(beatenBy),
                    $"If {elem} is countered by {beatenBy}, then {beatenBy} should counter {elem}");
            }
        }

        // ── Affinity tracking ──

        [Test]
        public void AddAffinity_IncreasesScore()
        {
            _affinity.AddAffinity(ArchetypeElement.Flame, 5);
            Assert.AreEqual(5, _affinity.AffinityScores[ArchetypeElement.Flame]);
        }

        [Test]
        public void AddAffinity_ZeroOrNegative_IsIgnored()
        {
            _affinity.AddAffinity(ArchetypeElement.Flame, 0);
            _affinity.AddAffinity(ArchetypeElement.Flame, -3);
            Assert.AreEqual(0, _affinity.AffinityScores[ArchetypeElement.Flame]);
        }

        [Test]
        public void GetDominantArchetype_ReturnsHighestScorer()
        {
            _affinity.AddAffinity(ArchetypeElement.Flame, 2);
            _affinity.AddAffinity(ArchetypeElement.Tide, 8);
            _affinity.AddAffinity(ArchetypeElement.Gale, 5);

            Assert.AreEqual(ArchetypeElement.Tide, _affinity.GetDominantArchetype());
        }

        [Test]
        public void CommitmentRatio_ZeroAffinity_ReturnsZero()
        {
            float ratio = _affinity.GetCommitmentRatio(ArchetypeElement.Flame);
            Assert.AreEqual(0f, ratio, 0.001f);
        }

        [Test]
        public void CommitmentRatio_FullyCommitted_ReturnsHigh()
        {
            // Max out a single element with no distractions
            _affinity.AddAffinity(ArchetypeElement.Flame, ArchetypeAffinity.MaxAffinityForScaling);
            float ratio = _affinity.GetCommitmentRatio(ArchetypeElement.Flame);
            Assert.AreEqual(1.0f, ratio, 0.001f, "Single-element max commitment should be 1.0");
        }

        [Test]
        public void CommitmentRatio_ScatteredBuild_ReturnsLow()
        {
            // Spread equally across all three elements
            _affinity.AddAffinity(ArchetypeElement.Flame, 10);
            _affinity.AddAffinity(ArchetypeElement.Tide, 10);
            _affinity.AddAffinity(ArchetypeElement.Gale, 10);

            float ratio = _affinity.GetCommitmentRatio(ArchetypeElement.Flame);
            Assert.Less(ratio, 0.65f, "Scattered build should have low commitment ratio");
        }

        // ── CalculateEffectivePower ──

        [Test]
        public void EffectivePower_CommonAtZero_EqualsBase()
        {
            int power = RarityScaling.CalculateEffectivePower(10, CardRarity.Common, 0f);
            Assert.AreEqual(10, power, "Common at 0 commitment should equal base value");
        }

        [Test]
        public void EffectivePower_LegendaryAtZero_IsBelowBase()
        {
            int power = RarityScaling.CalculateEffectivePower(10, CardRarity.Legendary, 0f);
            Assert.AreEqual(5, power, "Legendary at 0 commitment: 10 * 0.5 = 5");
        }

        [Test]
        public void EffectivePower_LegendaryAtMax_IsDevastating()
        {
            int power = RarityScaling.CalculateEffectivePower(10, CardRarity.Legendary, 1.0f);
            Assert.AreEqual(25, power, "Legendary at max commitment: 10 * 2.5 = 25");
        }
    }
}

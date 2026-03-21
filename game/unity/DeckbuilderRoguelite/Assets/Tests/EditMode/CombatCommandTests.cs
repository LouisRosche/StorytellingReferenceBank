using System.Collections.Generic;
using NUnit.Framework;
using Deckbuilder.Core.Commands;

namespace Deckbuilder.Tests.EditMode
{
    [TestFixture]
    public class CombatCommandTests
    {
        private class TestEntity : ICombatEntity
        {
            public int Hp { get; set; } = 100;
            public int MaxHp => 100;
            public int Block { get; set; } = 0;
            public Dictionary<string, int> Statuses { get; } = new();

            public void AddStatusEffect(string effectId, int stacks)
            {
                if (!Statuses.ContainsKey(effectId)) Statuses[effectId] = 0;
                Statuses[effectId] += stacks;
            }

            public void RemoveStatusEffect(string effectId, int stacks)
            {
                if (!Statuses.ContainsKey(effectId)) return;
                Statuses[effectId] -= stacks;
                if (Statuses[effectId] <= 0) Statuses.Remove(effectId);
            }
        }

        [Test]
        public void DealDamage_ReducesHp()
        {
            var entity = new TestEntity { Hp = 80 };
            var cmd = new DealDamageCommand(entity, 15);

            cmd.Execute();

            Assert.AreEqual(65, entity.Hp);
        }

        [Test]
        public void DealDamage_BlockAbsorbsDamage()
        {
            var entity = new TestEntity { Hp = 80, Block = 10 };
            var cmd = new DealDamageCommand(entity, 15);

            cmd.Execute();

            Assert.AreEqual(75, entity.Hp);
            Assert.AreEqual(0, entity.Block);
        }

        [Test]
        public void DealDamage_BlockFullyAbsorbs()
        {
            var entity = new TestEntity { Hp = 80, Block = 20 };
            var cmd = new DealDamageCommand(entity, 15);

            cmd.Execute();

            Assert.AreEqual(80, entity.Hp);
            Assert.AreEqual(5, entity.Block);
        }

        [Test]
        public void DealDamage_UndoRestoresState()
        {
            var entity = new TestEntity { Hp = 80, Block = 5 };
            var cmd = new DealDamageCommand(entity, 15);

            cmd.Execute();
            cmd.Undo();

            Assert.AreEqual(80, entity.Hp);
            Assert.AreEqual(5, entity.Block);
        }

        [Test]
        public void GainBlock_IncreasesBlock()
        {
            var entity = new TestEntity();
            var cmd = new GainBlockCommand(entity, 12);

            cmd.Execute();

            Assert.AreEqual(12, entity.Block);
        }

        [Test]
        public void ApplyStatus_AddsStacks()
        {
            var entity = new TestEntity();
            var cmd = new ApplyStatusEffectCommand(entity, "poison", 3);

            cmd.Execute();

            Assert.AreEqual(3, entity.Statuses["poison"]);
        }

        [Test]
        public void ApplyStatus_UndoRemovesStacks()
        {
            var entity = new TestEntity();
            var cmd = new ApplyStatusEffectCommand(entity, "poison", 3);

            cmd.Execute();
            cmd.Undo();

            Assert.IsFalse(entity.Statuses.ContainsKey("poison"));
        }
    }
}

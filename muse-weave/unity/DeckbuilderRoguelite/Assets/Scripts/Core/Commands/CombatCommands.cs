using Deckbuilder.Cards.Data;

namespace Deckbuilder.Core.Commands
{
    public class DealDamageCommand : ICommand
    {
        private readonly ICombatEntity _target;
        private readonly int _amount;
        private int _actualDamage;

        public DealDamageCommand(ICombatEntity target, int amount)
        {
            _target = target;
            _amount = amount;
        }

        public void Execute()
        {
            int blocked = System.Math.Min(_target.Block, _amount);
            _actualDamage = _amount - blocked;
            _target.Block -= blocked;
            _target.Hp -= _actualDamage;
        }

        public void Undo()
        {
            _target.Hp += _actualDamage;
            _target.Block += (_amount - _actualDamage);
        }
    }

    public class GainBlockCommand : ICommand
    {
        private readonly ICombatEntity _target;
        private readonly int _amount;

        public GainBlockCommand(ICombatEntity target, int amount)
        {
            _target = target;
            _amount = amount;
        }

        public void Execute() => _target.Block += _amount;
        public void Undo() => _target.Block -= _amount;
    }

    public class DrawCardCommand : ICommand
    {
        private readonly IDeckManager _deck;
        private readonly int _count;

        public DrawCardCommand(IDeckManager deck, int count)
        {
            _deck = deck;
            _count = count;
        }

        public void Execute() => _deck.Draw(_count);
        public void Undo() { /* Draw is not trivially reversible */ }
    }

    public class ApplyStatusEffectCommand : ICommand
    {
        private readonly ICombatEntity _target;
        private readonly string _effectId;
        private readonly int _stacks;

        public ApplyStatusEffectCommand(ICombatEntity target, string effectId, int stacks)
        {
            _target = target;
            _effectId = effectId;
            _stacks = stacks;
        }

        public void Execute() => _target.AddStatusEffect(_effectId, _stacks);
        public void Undo() => _target.RemoveStatusEffect(_effectId, _stacks);
    }
}

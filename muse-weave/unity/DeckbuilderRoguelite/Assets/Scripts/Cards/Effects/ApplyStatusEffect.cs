using UnityEngine;
using Deckbuilder.Cards.Data;
using Deckbuilder.Core.Commands;

namespace Deckbuilder.Cards.Effects
{
    [CreateAssetMenu(fileName = "ApplyStatus", menuName = "Deckbuilder/Effects/Apply Status")]
    public class ApplyStatusEffect : CardEffect
    {
        public string statusEffectId;
        public int stacks;

        public override void Execute(EffectContext context)
        {
            var command = new ApplyStatusEffectCommand(context.Target, statusEffectId, stacks);
            context.Invoker.ExecuteCommand(command);
        }
    }
}

using UnityEngine;
using Deckbuilder.Cards.Data;
using Deckbuilder.Core.Commands;

namespace Deckbuilder.Cards.Effects
{
    [CreateAssetMenu(fileName = "DealDamage", menuName = "Deckbuilder/Effects/Deal Damage")]
    public class DealDamageEffect : CardEffect
    {
        public int baseDamage;

        public override void Execute(EffectContext context)
        {
            var command = new DealDamageCommand(context.Target, baseDamage + context.Value);
            context.Invoker.ExecuteCommand(command);
        }
    }
}

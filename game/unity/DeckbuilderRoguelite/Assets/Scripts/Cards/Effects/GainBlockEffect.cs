using UnityEngine;
using Deckbuilder.Cards.Data;
using Deckbuilder.Core.Commands;

namespace Deckbuilder.Cards.Effects
{
    [CreateAssetMenu(fileName = "GainBlock", menuName = "Deckbuilder/Effects/Gain Block")]
    public class GainBlockEffect : CardEffect
    {
        public int baseBlock;

        public override void Execute(EffectContext context)
        {
            var command = new GainBlockCommand(context.Source, baseBlock + context.Value);
            context.Invoker.ExecuteCommand(command);
        }
    }
}

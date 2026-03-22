using UnityEngine;
using Deckbuilder.Cards.Data;
using Deckbuilder.Core.Commands;

namespace Deckbuilder.Cards.Effects
{
    [CreateAssetMenu(fileName = "DrawCards", menuName = "Deckbuilder/Effects/Draw Cards")]
    public class DrawCardsEffect : CardEffect
    {
        public int cardsToDraw;

        public override void Execute(EffectContext context)
        {
            var command = new DrawCardCommand(context.Deck, cardsToDraw);
            context.Invoker.ExecuteCommand(command);
        }
    }
}

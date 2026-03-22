using UnityEngine;

namespace Deckbuilder.Cards.Data
{
    /// <summary>
    /// Abstract base for card effects (Strategy pattern via ScriptableObjects).
    /// Each concrete effect is a separate asset that can be composed into cards
    /// by designers without touching code.
    /// </summary>
    public abstract class CardEffect : ScriptableObject
    {
        public abstract void Execute(EffectContext context);
    }

    /// <summary>
    /// Runtime context passed to effects during resolution.
    /// Decouples effects from concrete game systems.
    /// </summary>
    public class EffectContext
    {
        public Core.Commands.ICombatEntity Source { get; set; }
        public Core.Commands.ICombatEntity Target { get; set; }
        public Core.Commands.IDeckManager Deck { get; set; }
        public Core.Commands.CommandInvoker Invoker { get; set; }
        public int Value { get; set; }
    }
}

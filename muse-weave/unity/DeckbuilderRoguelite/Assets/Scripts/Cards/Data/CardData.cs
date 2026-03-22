using UnityEngine;

namespace Deckbuilder.Cards.Data
{
    public enum CardRarity { Common, Uncommon, Rare, Legendary }
    public enum CardTarget { SingleEnemy, AllEnemies, Self, None }

    /// <summary>
    /// Immutable data container for a card definition.
    /// Create instances via Assets → Create → Deckbuilder → Card Data.
    /// Multiple runtime card instances reference the same ScriptableObject (Flyweight pattern).
    /// </summary>
    [CreateAssetMenu(fileName = "NewCard", menuName = "Deckbuilder/Card Data")]
    public class CardData : ScriptableObject
    {
        [Header("Identity")]
        public string cardId;
        public string cardName;
        [TextArea(2, 4)]
        public string description;

        [Header("Cost")]
        public int manaCost;
        public CardRarity rarity;

        [Header("Targeting")]
        public CardTarget target;

        [Header("Effects (Strategy Pattern)")]
        [Tooltip("Drag CardEffect ScriptableObjects here. They execute in order when the card is played.")]
        public CardEffect[] effects;

        [Header("Keywords")]
        public bool exhaust;
        public bool ethereal;

        [Header("Visuals")]
        [Tooltip("Addressable asset key for card artwork")]
        public string artAssetKey;
    }
}

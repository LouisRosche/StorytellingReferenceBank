using UnityEngine;
using UnityEngine.UIElements;
using Deckbuilder.Cards.Data;

namespace Deckbuilder.UI
{
    /// <summary>
    /// Manages the card hand using UI Toolkit.
    /// Cards are instantiated as VisualElements from a UXML template and styled via USS.
    /// No GameObjects are created for UI — everything lives in the visual tree.
    /// </summary>
    public class CardUIController : MonoBehaviour
    {
        [SerializeField] private UIDocument uiDocument;
        [SerializeField] private VisualTreeAsset cardTemplate;

        private VisualElement _handContainer;

        private void OnEnable()
        {
            var root = uiDocument.rootVisualElement;
            _handContainer = root.Q<VisualElement>("hand-container");
        }

        public void RenderHand(CardData[] cardsInHand)
        {
            _handContainer.Clear();

            foreach (var card in cardsInHand)
            {
                var cardElement = cardTemplate.Instantiate();

                cardElement.Q<Label>("card-name").text = card.cardName;
                cardElement.Q<Label>("card-cost").text = card.manaCost.ToString();
                cardElement.Q<Label>("card-description").text = card.description;
                cardElement.AddToClassList($"rarity-{card.rarity.ToString().ToLower()}");

                // Hover feedback via USS pseudo-classes (:hover scales up)
                cardElement.RegisterCallback<ClickEvent>(_ => OnCardClicked(card));

                _handContainer.Add(cardElement);
            }
        }

        private void OnCardClicked(CardData card)
        {
            Debug.Log($"Card clicked: {card.cardName}");
            // Route to FSM / CommandInvoker
        }
    }
}

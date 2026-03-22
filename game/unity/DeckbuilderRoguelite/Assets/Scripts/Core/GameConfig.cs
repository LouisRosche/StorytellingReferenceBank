using UnityEngine;

namespace Deckbuilder.Core
{
    /// <summary>
    /// Runtime game configuration loaded from the shared JSON schema.
    /// Deserialized via JsonUtility or Newtonsoft.Json from game-config.schema.json.
    /// </summary>
    [CreateAssetMenu(fileName = "GameConfig", menuName = "Deckbuilder/Game Config")]
    public class GameConfig : ScriptableObject
    {
        [Header("Player")]
        public int startingHp = 80;
        public int maxHp = 80;
        public int startingEnergy = 3;
        public int startingDeckSize = 10;
        public int drawPerTurn = 5;

        [Header("Map")]
        public int floorsPerAct = 15;
        public int columnsPerFloor = 7;
        public int pathCount = 6;
        public int eliteMinFloor = 6;
        public int restMinFloor = 6;

        [Header("Encounters")]
        public float hpMultiplierPerAct = 1.5f;
        public float eliteAscensionMultiplier = 1.6f;
    }
}

namespace Deckbuilder.Core.Commands
{
    /// <summary>
    /// Minimal interface for anything that participates in combat.
    /// Keeps commands decoupled from concrete player/enemy implementations.
    /// </summary>
    public interface ICombatEntity
    {
        int Hp { get; set; }
        int MaxHp { get; }
        int Block { get; set; }
        void AddStatusEffect(string effectId, int stacks);
        void RemoveStatusEffect(string effectId, int stacks);
    }

    /// <summary>
    /// Abstraction over deck operations so commands don't depend on MonoBehaviour.
    /// </summary>
    public interface IDeckManager
    {
        void Draw(int count);
        void Discard(string cardId);
        void Exhaust(string cardId);
    }
}

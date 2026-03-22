namespace Deckbuilder.Core.FSM
{
    /// <summary>
    /// Contract for all game states. States are pure C# — no MonoBehaviour dependency.
    /// </summary>
    public interface IState
    {
        void Enter();
        void Execute();
        void Exit();
    }
}

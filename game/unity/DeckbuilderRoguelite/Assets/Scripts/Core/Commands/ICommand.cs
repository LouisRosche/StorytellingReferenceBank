namespace Deckbuilder.Core.Commands
{
    /// <summary>
    /// Encapsulates a game action as an object.
    /// Commands are the sole mechanism for mutating game state.
    /// </summary>
    public interface ICommand
    {
        void Execute();
        void Undo();
    }
}

using System;
using System.Collections.Generic;

namespace Deckbuilder.Core.Commands
{
    /// <summary>
    /// Central dispatcher for game commands. Maintains a history stack for undo
    /// and a resolution queue for cascading effects (e.g. triggered abilities).
    /// </summary>
    public class CommandInvoker
    {
        private readonly Stack<ICommand> _history = new();
        private readonly Queue<ICommand> _resolutionQueue = new();

        public event Action<ICommand> OnCommandExecuted;

        public void ExecuteCommand(ICommand command)
        {
            command.Execute();
            _history.Push(command);
            OnCommandExecuted?.Invoke(command);

            // Process any cascading commands that were enqueued during execution
            while (_resolutionQueue.Count > 0)
            {
                var triggered = _resolutionQueue.Dequeue();
                triggered.Execute();
                _history.Push(triggered);
                OnCommandExecuted?.Invoke(triggered);
            }
        }

        /// <summary>
        /// Enqueue a triggered command to resolve after the current command completes.
        /// Used for "whenever X happens, do Y" effects.
        /// </summary>
        public void EnqueueTriggered(ICommand command)
        {
            _resolutionQueue.Enqueue(command);
        }

        public void UndoLast()
        {
            if (_history.Count == 0) return;
            var command = _history.Pop();
            command.Undo();
        }

        public void ClearHistory() => _history.Clear();
    }
}

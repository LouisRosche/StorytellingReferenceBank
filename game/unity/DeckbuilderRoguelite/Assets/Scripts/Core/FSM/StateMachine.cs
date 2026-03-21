using System.Collections.Generic;

namespace Deckbuilder.Core.FSM
{
    /// <summary>
    /// Pushdown automaton FSM. States are stacked so sub-states (e.g. target selection)
    /// can be pushed on top of the current state and popped when complete.
    /// </summary>
    public class StateMachine
    {
        private readonly Stack<IState> _stateStack = new();

        public IState CurrentState => _stateStack.Count > 0 ? _stateStack.Peek() : null;

        public void PushState(IState state)
        {
            CurrentState?.Exit();
            _stateStack.Push(state);
            state.Enter();
        }

        public void PopState()
        {
            if (_stateStack.Count == 0) return;

            var exiting = _stateStack.Pop();
            exiting.Exit();
            CurrentState?.Enter();
        }

        public void ChangeState(IState state)
        {
            while (_stateStack.Count > 0)
            {
                _stateStack.Pop().Exit();
            }
            _stateStack.Push(state);
            state.Enter();
        }

        public void Update()
        {
            CurrentState?.Execute();
        }
    }
}

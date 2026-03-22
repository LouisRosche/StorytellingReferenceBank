using System;

namespace Deckbuilder.Core.FSM
{
    public class DrawPhaseState : IState
    {
        private readonly Action<int> _drawCards;
        private readonly int _drawCount;
        private readonly Action _onComplete;

        public DrawPhaseState(Action<int> drawCards, int drawCount, Action onComplete)
        {
            _drawCards = drawCards;
            _drawCount = drawCount;
            _onComplete = onComplete;
        }

        public void Enter() => _drawCards(_drawCount);
        public void Execute() => _onComplete();
        public void Exit() { }
    }

    public class PlayerActionState : IState
    {
        private readonly Action _enableInput;
        private readonly Action _disableInput;

        public PlayerActionState(Action enableInput, Action disableInput)
        {
            _enableInput = enableInput;
            _disableInput = disableInput;
        }

        public void Enter() => _enableInput();
        public void Execute() { /* Waits for player commands */ }
        public void Exit() => _disableInput();
    }

    public class EnemyIntentState : IState
    {
        private readonly Action _resolveEnemyIntents;
        private readonly Action _onComplete;

        public EnemyIntentState(Action resolveEnemyIntents, Action onComplete)
        {
            _resolveEnemyIntents = resolveEnemyIntents;
            _onComplete = onComplete;
        }

        public void Enter() => _resolveEnemyIntents();
        public void Execute() => _onComplete();
        public void Exit() { }
    }

    public class ResolutionState : IState
    {
        private readonly Action _resolveEndOfTurn;
        private readonly Action _onComplete;

        public ResolutionState(Action resolveEndOfTurn, Action onComplete)
        {
            _resolveEndOfTurn = resolveEndOfTurn;
            _onComplete = onComplete;
        }

        public void Enter() => _resolveEndOfTurn();
        public void Execute() => _onComplete();
        public void Exit() { }
    }

    public class TargetSelectionState : IState
    {
        private readonly Action _showTargetUI;
        private readonly Action _hideTargetUI;

        public TargetSelectionState(Action showTargetUI, Action hideTargetUI)
        {
            _showTargetUI = showTargetUI;
            _hideTargetUI = hideTargetUI;
        }

        public void Enter() => _showTargetUI();
        public void Execute() { /* Waits for target selection */ }
        public void Exit() => _hideTargetUI();
    }
}

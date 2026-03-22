using NUnit.Framework;
using Deckbuilder.Core.FSM;

namespace Deckbuilder.Tests.EditMode
{
    [TestFixture]
    public class StateMachineTests
    {
        private class MockState : IState
        {
            public bool Entered { get; private set; }
            public bool Executed { get; private set; }
            public bool Exited { get; private set; }

            public void Enter() => Entered = true;
            public void Execute() => Executed = true;
            public void Exit() => Exited = true;
        }

        [Test]
        public void ChangeState_EntersNewState()
        {
            var fsm = new StateMachine();
            var state = new MockState();

            fsm.ChangeState(state);

            Assert.IsTrue(state.Entered);
            Assert.AreEqual(state, fsm.CurrentState);
        }

        [Test]
        public void ChangeState_ExitsPreviousState()
        {
            var fsm = new StateMachine();
            var first = new MockState();
            var second = new MockState();

            fsm.ChangeState(first);
            fsm.ChangeState(second);

            Assert.IsTrue(first.Exited);
            Assert.IsTrue(second.Entered);
        }

        [Test]
        public void PushState_StacksStates()
        {
            var fsm = new StateMachine();
            var bottom = new MockState();
            var top = new MockState();

            fsm.PushState(bottom);
            fsm.PushState(top);

            Assert.AreEqual(top, fsm.CurrentState);
            Assert.IsTrue(bottom.Exited); // Exited when pushed over
        }

        [Test]
        public void PopState_RestoresPreviousState()
        {
            var fsm = new StateMachine();
            var bottom = new MockState();
            var top = new MockState();

            fsm.PushState(bottom);
            fsm.PushState(top);
            fsm.PopState();

            Assert.AreEqual(bottom, fsm.CurrentState);
            Assert.IsTrue(top.Exited);
        }

        [Test]
        public void Update_ExecutesCurrentState()
        {
            var fsm = new StateMachine();
            var state = new MockState();

            fsm.ChangeState(state);
            fsm.Update();

            Assert.IsTrue(state.Executed);
        }
    }
}

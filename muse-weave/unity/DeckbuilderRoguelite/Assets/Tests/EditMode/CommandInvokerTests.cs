using NUnit.Framework;
using Deckbuilder.Core.Commands;

namespace Deckbuilder.Tests.EditMode
{
    [TestFixture]
    public class CommandInvokerTests
    {
        private class MockCommand : ICommand
        {
            public int ExecuteCount { get; private set; }
            public int UndoCount { get; private set; }

            public void Execute() => ExecuteCount++;
            public void Undo() => UndoCount++;
        }

        [Test]
        public void ExecuteCommand_RunsCommand()
        {
            var invoker = new CommandInvoker();
            var cmd = new MockCommand();

            invoker.ExecuteCommand(cmd);

            Assert.AreEqual(1, cmd.ExecuteCount);
        }

        [Test]
        public void ExecuteCommand_FiresEvent()
        {
            var invoker = new CommandInvoker();
            ICommand received = null;
            invoker.OnCommandExecuted += c => received = c;

            var cmd = new MockCommand();
            invoker.ExecuteCommand(cmd);

            Assert.AreEqual(cmd, received);
        }

        [Test]
        public void UndoLast_ReversesMostRecentCommand()
        {
            var invoker = new CommandInvoker();
            var cmd = new MockCommand();

            invoker.ExecuteCommand(cmd);
            invoker.UndoLast();

            Assert.AreEqual(1, cmd.UndoCount);
        }

        [Test]
        public void TriggeredCommands_ResolveAfterPrimary()
        {
            var invoker = new CommandInvoker();
            var triggered = new MockCommand();
            var primary = new MockCommand();

            // When primary executes, enqueue a triggered command
            invoker.OnCommandExecuted += c =>
            {
                if (c == primary)
                    invoker.EnqueueTriggered(triggered);
            };

            invoker.ExecuteCommand(primary);

            Assert.AreEqual(1, primary.ExecuteCount);
            Assert.AreEqual(1, triggered.ExecuteCount);
        }
    }
}

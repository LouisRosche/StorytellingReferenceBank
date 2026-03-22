using NUnit.Framework;
using Deckbuilder.Map;

namespace Deckbuilder.Tests.EditMode
{
    [TestFixture]
    public class MapGeneratorTests
    {
        [Test]
        public void Generate_ReturnsCorrectGridDimensions()
        {
            var gen = new MapGenerator(floors: 15, columns: 7, seed: 42);
            var grid = gen.Generate();

            Assert.AreEqual(15, grid.GetLength(0));
            Assert.AreEqual(7, grid.GetLength(1));
        }

        [Test]
        public void Generate_FirstFloorIsAlwaysMonster()
        {
            var gen = new MapGenerator(seed: 42);
            var grid = gen.Generate();

            for (int c = 0; c < grid.GetLength(1); c++)
            {
                var node = grid[0, c];
                if (node.Children.Count > 0 || node.Parents.Count > 0)
                    Assert.AreEqual(RoomType.Monster, node.Room);
            }
        }

        [Test]
        public void Generate_LastFloorIsAlwaysRest()
        {
            var gen = new MapGenerator(floors: 15, seed: 42);
            var grid = gen.Generate();

            int lastFloor = grid.GetLength(0) - 1;
            for (int c = 0; c < grid.GetLength(1); c++)
            {
                var node = grid[lastFloor, c];
                if (node.Parents.Count > 0)
                    Assert.AreEqual(RoomType.Rest, node.Room);
            }
        }

        [Test]
        public void Generate_IsDeterministicWithSeed()
        {
            var gen1 = new MapGenerator(seed: 123);
            var gen2 = new MapGenerator(seed: 123);

            var grid1 = gen1.Generate();
            var grid2 = gen2.Generate();

            for (int f = 0; f < grid1.GetLength(0); f++)
            {
                for (int c = 0; c < grid1.GetLength(1); c++)
                {
                    Assert.AreEqual(grid1[f, c].Room, grid2[f, c].Room,
                        $"Mismatch at floor {f}, column {c}");
                    Assert.AreEqual(grid1[f, c].Children.Count, grid2[f, c].Children.Count);
                }
            }
        }

        [Test]
        public void Generate_NoElitesBeforeMinFloor()
        {
            var gen = new MapGenerator(eliteMinFloor: 6, seed: 42);
            var grid = gen.Generate();

            for (int f = 0; f < 6; f++)
            {
                for (int c = 0; c < grid.GetLength(1); c++)
                {
                    Assert.AreNotEqual(RoomType.Elite, grid[f, c].Room,
                        $"Elite found at floor {f}, column {c}");
                }
            }
        }

        [Test]
        public void Generate_HasAtLeastOneConnectedPath()
        {
            var gen = new MapGenerator(seed: 42);
            var grid = gen.Generate();

            // At least one node on floor 0 should have children
            bool hasStart = false;
            for (int c = 0; c < grid.GetLength(1); c++)
            {
                if (grid[0, c].Children.Count > 0) hasStart = true;
            }
            Assert.IsTrue(hasStart, "No starting nodes found on floor 0");
        }
    }
}

using System;
using System.Collections.Generic;

namespace Deckbuilder.Map
{
    public enum RoomType { Monster, Elite, Rest, Shop, Event, Boss }

    public class MapNode
    {
        public int Floor { get; set; }
        public int Column { get; set; }
        public RoomType Room { get; set; }
        public List<MapNode> Children { get; } = new();
        public List<MapNode> Parents { get; } = new();

        public string Id => $"{Floor}_{Column}";
    }

    /// <summary>
    /// Procedural DAG map generator following the Slay the Spire algorithm.
    /// Pure C# — no Unity dependencies — fully testable headlessly.
    /// </summary>
    public class MapGenerator
    {
        private readonly int _floors;
        private readonly int _columns;
        private readonly int _pathCount;
        private readonly int _eliteMinFloor;
        private readonly int _restMinFloor;
        private readonly Random _rng;

        // Room type weights (probabilities)
        private const float EventWeight = 0.22f;
        private const float RestWeight = 0.12f;
        private const float EliteWeight = 0.08f;
        private const float ShopWeight = 0.05f;

        public MapGenerator(int floors = 15, int columns = 7, int pathCount = 6,
            int eliteMinFloor = 6, int restMinFloor = 6, int? seed = null)
        {
            _floors = floors;
            _columns = columns;
            _pathCount = pathCount;
            _eliteMinFloor = eliteMinFloor;
            _restMinFloor = restMinFloor;
            _rng = seed.HasValue ? new Random(seed.Value) : new Random();
        }

        public MapNode[,] Generate()
        {
            var grid = new MapNode[_floors, _columns];

            // Initialize grid
            for (int f = 0; f < _floors; f++)
                for (int c = 0; c < _columns; c++)
                    grid[f, c] = new MapNode { Floor = f, Column = c, Room = RoomType.Monster };

            // Draw paths
            var usedNodes = new HashSet<string>();
            var edges = new HashSet<string>();

            for (int p = 0; p < _pathCount; p++)
            {
                int col = _rng.Next(_columns);
                usedNodes.Add($"0_{col}");

                for (int floor = 0; floor < _floors - 1; floor++)
                {
                    int nextCol = PickNextColumn(col, floor, edges);
                    string edgeKey = $"{floor}_{col}->{floor + 1}_{nextCol}";

                    // Prevent crossing edges
                    if (!HasCrossingEdge(edges, floor, col, nextCol))
                    {
                        edges.Add(edgeKey);
                        grid[floor, col].Children.Add(grid[floor + 1, nextCol]);
                        grid[floor + 1, nextCol].Parents.Add(grid[floor, col]);
                    }
                    else
                    {
                        // Fall back to straight-up
                        nextCol = col;
                        edgeKey = $"{floor}_{col}->{floor + 1}_{nextCol}";
                        if (!edges.Contains(edgeKey))
                        {
                            edges.Add(edgeKey);
                            grid[floor, col].Children.Add(grid[floor + 1, nextCol]);
                            grid[floor + 1, nextCol].Parents.Add(grid[floor, col]);
                        }
                    }

                    usedNodes.Add($"{floor + 1}_{nextCol}");
                    col = nextCol;
                }
            }

            // Assign room types to used nodes
            AssignRoomTypes(grid, usedNodes);

            return grid;
        }

        private int PickNextColumn(int currentCol, int floor, HashSet<string> edges)
        {
            int offset = _rng.Next(3) - 1; // -1, 0, or 1
            int next = Math.Clamp(currentCol + offset, 0, _columns - 1);
            return next;
        }

        private bool HasCrossingEdge(HashSet<string> edges, int floor, int fromCol, int toCol)
        {
            // An edge from (floor, A) to (floor+1, B) crosses (floor, C) to (floor+1, D)
            // when A < C and B > D, or A > C and B < D.
            foreach (var edge in edges)
            {
                if (!edge.StartsWith($"{floor}_")) continue;

                var parts = edge.Split("->");
                var fromParts = parts[0].Split('_');
                var toParts = parts[1].Split('_');

                int existingFrom = int.Parse(fromParts[1]);
                int existingTo = int.Parse(toParts[1]);

                if ((fromCol < existingFrom && toCol > existingTo) ||
                    (fromCol > existingFrom && toCol < existingTo))
                    return true;
            }
            return false;
        }

        private void AssignRoomTypes(MapNode[,] grid, HashSet<string> usedNodes)
        {
            for (int f = 0; f < _floors; f++)
            {
                for (int c = 0; c < _columns; c++)
                {
                    if (!usedNodes.Contains($"{f}_{c}")) continue;

                    var node = grid[f, c];

                    // Fixed assignments
                    if (f == 0) { node.Room = RoomType.Monster; continue; }
                    if (f == _floors - 1) { node.Room = RoomType.Rest; continue; }

                    // Weighted random with constraints
                    node.Room = PickRoomType(node, f);
                }
            }
        }

        private RoomType PickRoomType(MapNode node, int floor)
        {
            float roll = (float)_rng.NextDouble();
            float cumulative = 0f;

            // Try event
            cumulative += EventWeight;
            if (roll < cumulative && IsValidPlacement(node, RoomType.Event, floor))
                return RoomType.Event;

            // Try rest
            cumulative += RestWeight;
            if (roll < cumulative && floor >= _restMinFloor && IsValidPlacement(node, RoomType.Rest, floor))
                return RoomType.Rest;

            // Try elite
            cumulative += EliteWeight;
            if (roll < cumulative && floor >= _eliteMinFloor && IsValidPlacement(node, RoomType.Elite, floor))
                return RoomType.Elite;

            // Try shop
            cumulative += ShopWeight;
            if (roll < cumulative && IsValidPlacement(node, RoomType.Shop, floor))
                return RoomType.Shop;

            return RoomType.Monster;
        }

        /// <summary>
        /// Validates placement constraints:
        /// - No consecutive same-type major rooms
        /// - No sibling nodes sharing the same type
        /// </summary>
        private bool IsValidPlacement(MapNode node, RoomType proposed, int floor)
        {
            // Check parents: no consecutive same type
            foreach (var parent in node.Parents)
            {
                if (parent.Room == proposed) return false;
            }

            // Check siblings (nodes sharing a parent): no identical types
            foreach (var parent in node.Parents)
            {
                foreach (var sibling in parent.Children)
                {
                    if (sibling != node && sibling.Room == proposed) return false;
                }
            }

            // Pre-boss floor constraint: floor N-2 can't be rest if N-1 is always rest
            if (proposed == RoomType.Rest && floor == _floors - 2)
                return false;

            return true;
        }
    }
}

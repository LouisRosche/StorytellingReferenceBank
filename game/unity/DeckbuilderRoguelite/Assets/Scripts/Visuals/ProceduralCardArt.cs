using UnityEngine;

namespace Deckbuilder.Visuals
{
    /// <summary>
    /// Generates card art procedurally from code using geometric patterns and noise.
    /// No external art assets — everything is Texture2D operations.
    /// Element type determines color palette and pattern style.
    /// Rarity determines visual complexity (more layers, more detail).
    /// </summary>
    public class ProceduralCardArt : MonoBehaviour
    {
        [Header("Output")]
        [SerializeField] private int textureWidth = 128;
        [SerializeField] private int textureHeight = 128;

        [Header("Generation Parameters")]
        [SerializeField] private Core.Archetypes.ArchetypeElement element;
        [SerializeField] private Cards.Data.CardRarity rarity;
        [SerializeField] private int seed;

        private Texture2D _generatedTexture;

        public Texture2D GeneratedTexture => _generatedTexture;

        /// <summary>
        /// Generate card art with the current parameters. Call manually or from inspector.
        /// </summary>
        public Texture2D Generate()
        {
            return Generate(element, rarity, seed);
        }

        /// <summary>
        /// Generate card art with explicit parameters.
        /// </summary>
        public Texture2D Generate(Core.Archetypes.ArchetypeElement elem, Cards.Data.CardRarity cardRarity, int artSeed)
        {
            element = elem;
            rarity = cardRarity;
            seed = artSeed;

            _generatedTexture = new Texture2D(textureWidth, textureHeight, TextureFormat.RGBA32, false);
            _generatedTexture.filterMode = FilterMode.Bilinear;
            _generatedTexture.wrapMode = TextureWrapMode.Clamp;

            var rng = new System.Random(artSeed);
            var colors = new Color[textureWidth * textureHeight];

            // Base fill from element palette
            Color baseColor = GetBaseColor(elem);
            Color highlightColor = GetHighlightColor(elem);
            Color shadowColor = GetShadowColor(elem);

            // Layer 0: Perlin noise background (all rarities)
            float noiseScale = 4.0f + rng.Next(0, 300) * 0.01f;
            float offsetX = (float)rng.NextDouble() * 1000f;
            float offsetY = (float)rng.NextDouble() * 1000f;

            for (int y = 0; y < textureHeight; y++)
            {
                for (int x = 0; x < textureWidth; x++)
                {
                    float nx = (float)x / textureWidth * noiseScale + offsetX;
                    float ny = (float)y / textureHeight * noiseScale + offsetY;
                    float noise = Mathf.PerlinNoise(nx, ny);
                    colors[y * textureWidth + x] = Color.Lerp(shadowColor, baseColor, noise);
                }
            }

            // Layer 1: Central geometric shape (all rarities)
            DrawElementShape(colors, elem, highlightColor, rng);

            // Layer 2: Radial lines (Uncommon+)
            if (cardRarity >= Cards.Data.CardRarity.Uncommon)
            {
                int lineCount = 6 + rng.Next(0, 6);
                DrawRadialLines(colors, lineCount, highlightColor * 0.6f, rng);
            }

            // Layer 3: Particle scatter (Rare+)
            if (cardRarity >= Cards.Data.CardRarity.Rare)
            {
                int particleCount = 20 + rng.Next(0, 30);
                DrawParticles(colors, particleCount, highlightColor, rng);
            }

            // Layer 4: Outer glow ring + inner sigil (Legendary)
            if (cardRarity >= Cards.Data.CardRarity.Legendary)
            {
                DrawGlowRing(colors, highlightColor);
                DrawSigil(colors, elem, Color.white, rng);
            }

            // Vignette overlay (all rarities, stronger at higher rarity)
            float vignetteStrength = 0.3f + (int)cardRarity * 0.1f;
            ApplyVignette(colors, vignetteStrength);

            _generatedTexture.SetPixels(colors);
            _generatedTexture.Apply();
            return _generatedTexture;
        }

        private Color GetBaseColor(Core.Archetypes.ArchetypeElement elem)
        {
            switch (elem)
            {
                case Core.Archetypes.ArchetypeElement.Flame:
                    return new Color(0.6f, 0.15f, 0.05f);
                case Core.Archetypes.ArchetypeElement.Tide:
                    return new Color(0.05f, 0.2f, 0.5f);
                case Core.Archetypes.ArchetypeElement.Gale:
                    return new Color(0.15f, 0.45f, 0.2f);
                default:
                    return new Color(0.3f, 0.3f, 0.3f);
            }
        }

        private Color GetHighlightColor(Core.Archetypes.ArchetypeElement elem)
        {
            switch (elem)
            {
                case Core.Archetypes.ArchetypeElement.Flame:
                    return new Color(1.0f, 0.6f, 0.1f);
                case Core.Archetypes.ArchetypeElement.Tide:
                    return new Color(0.3f, 0.7f, 1.0f);
                case Core.Archetypes.ArchetypeElement.Gale:
                    return new Color(0.5f, 1.0f, 0.6f);
                default:
                    return new Color(0.8f, 0.8f, 0.8f);
            }
        }

        private Color GetShadowColor(Core.Archetypes.ArchetypeElement elem)
        {
            switch (elem)
            {
                case Core.Archetypes.ArchetypeElement.Flame:
                    return new Color(0.15f, 0.02f, 0.0f);
                case Core.Archetypes.ArchetypeElement.Tide:
                    return new Color(0.01f, 0.03f, 0.12f);
                case Core.Archetypes.ArchetypeElement.Gale:
                    return new Color(0.02f, 0.08f, 0.03f);
                default:
                    return new Color(0.05f, 0.05f, 0.05f);
            }
        }

        private void DrawElementShape(Color[] colors, Core.Archetypes.ArchetypeElement elem, Color color, System.Random rng)
        {
            float cx = textureWidth * 0.5f;
            float cy = textureHeight * 0.5f;
            float radius = Mathf.Min(textureWidth, textureHeight) * 0.25f;

            switch (elem)
            {
                case Core.Archetypes.ArchetypeElement.Flame:
                    // Diamond / upward triangle for fire
                    DrawTriangle(colors, cx, cy - radius * 0.2f, radius, color);
                    break;
                case Core.Archetypes.ArchetypeElement.Tide:
                    // Concentric circles for water
                    DrawConcentricCircles(colors, cx, cy, radius, 3, color);
                    break;
                case Core.Archetypes.ArchetypeElement.Gale:
                    // Spiral lines for wind
                    DrawSpiral(colors, cx, cy, radius, color, rng);
                    break;
            }
        }

        private void DrawTriangle(Color[] colors, float cx, float cy, float radius, Color color)
        {
            // Upward-pointing triangle
            float ax = cx, ay = cy - radius;
            float bx = cx - radius * 0.866f, by = cy + radius * 0.5f;
            float ccx = cx + radius * 0.866f, ccy = cy + radius * 0.5f;

            for (int y = 0; y < textureHeight; y++)
            {
                for (int x = 0; x < textureWidth; x++)
                {
                    if (PointInTriangle(x, y, ax, ay, bx, by, ccx, ccy))
                    {
                        float dist = Mathf.Sqrt((x - cx) * (x - cx) + (y - cy) * (y - cy));
                        float fade = 1.0f - Mathf.Clamp01(dist / radius);
                        int idx = y * textureWidth + x;
                        colors[idx] = Color.Lerp(colors[idx], color, fade * 0.7f);
                    }
                }
            }
        }

        private bool PointInTriangle(float px, float py, float ax, float ay, float bx, float by, float cx, float cy)
        {
            float d1 = Sign(px, py, ax, ay, bx, by);
            float d2 = Sign(px, py, bx, by, cx, cy);
            float d3 = Sign(px, py, cx, cy, ax, ay);
            bool hasNeg = (d1 < 0) || (d2 < 0) || (d3 < 0);
            bool hasPos = (d1 > 0) || (d2 > 0) || (d3 > 0);
            return !(hasNeg && hasPos);
        }

        private float Sign(float x1, float y1, float x2, float y2, float x3, float y3)
        {
            return (x1 - x3) * (y2 - y3) - (x2 - x3) * (y1 - y3);
        }

        private void DrawConcentricCircles(Color[] colors, float cx, float cy, float maxRadius, int rings, Color color)
        {
            float ringWidth = 3.0f;
            for (int r = 0; r < rings; r++)
            {
                float ringRadius = maxRadius * (r + 1) / rings;
                for (int y = 0; y < textureHeight; y++)
                {
                    for (int x = 0; x < textureWidth; x++)
                    {
                        float dist = Mathf.Sqrt((x - cx) * (x - cx) + (y - cy) * (y - cy));
                        float diff = Mathf.Abs(dist - ringRadius);
                        if (diff < ringWidth)
                        {
                            float intensity = 1.0f - diff / ringWidth;
                            int idx = y * textureWidth + x;
                            colors[idx] = Color.Lerp(colors[idx], color, intensity * 0.6f);
                        }
                    }
                }
            }
        }

        private void DrawSpiral(Color[] colors, float cx, float cy, float maxRadius, Color color, System.Random rng)
        {
            float angleOffset = (float)rng.NextDouble() * Mathf.PI * 2f;
            int steps = 300;
            float lineWidth = 2.5f;

            for (int i = 0; i < steps; i++)
            {
                float t = (float)i / steps;
                float angle = angleOffset + t * Mathf.PI * 4f; // 2 full rotations
                float r = t * maxRadius;
                float px = cx + Mathf.Cos(angle) * r;
                float py = cy + Mathf.Sin(angle) * r;

                // Draw a dot at this position
                int ix = Mathf.RoundToInt(px);
                int iy = Mathf.RoundToInt(py);
                int w = Mathf.CeilToInt(lineWidth);

                for (int dy = -w; dy <= w; dy++)
                {
                    for (int dx = -w; dx <= w; dx++)
                    {
                        int sx = ix + dx;
                        int sy = iy + dy;
                        if (sx < 0 || sx >= textureWidth || sy < 0 || sy >= textureHeight) continue;
                        float dist = Mathf.Sqrt(dx * dx + dy * dy);
                        if (dist > lineWidth) continue;
                        float fade = 1.0f - dist / lineWidth;
                        int idx = sy * textureWidth + sx;
                        colors[idx] = Color.Lerp(colors[idx], color, fade * 0.5f);
                    }
                }
            }
        }

        private void DrawRadialLines(Color[] colors, int lineCount, Color color, System.Random rng)
        {
            float cx = textureWidth * 0.5f;
            float cy = textureHeight * 0.5f;
            float maxLen = Mathf.Min(textureWidth, textureHeight) * 0.45f;
            float angleOffset = (float)rng.NextDouble() * Mathf.PI * 2f;

            for (int i = 0; i < lineCount; i++)
            {
                float angle = angleOffset + (float)i / lineCount * Mathf.PI * 2f;
                float len = maxLen * (0.5f + (float)rng.NextDouble() * 0.5f);
                float ex = cx + Mathf.Cos(angle) * len;
                float ey = cy + Mathf.Sin(angle) * len;
                DrawLine(colors, cx, cy, ex, ey, color, 1.5f);
            }
        }

        private void DrawLine(Color[] colors, float x0, float y0, float x1, float y1, Color color, float width)
        {
            float dx = x1 - x0;
            float dy = y1 - y0;
            float length = Mathf.Sqrt(dx * dx + dy * dy);
            int steps = Mathf.CeilToInt(length);
            if (steps == 0) return;

            for (int i = 0; i <= steps; i++)
            {
                float t = (float)i / steps;
                float px = x0 + dx * t;
                float py = y0 + dy * t;
                int ix = Mathf.RoundToInt(px);
                int iy = Mathf.RoundToInt(py);
                int w = Mathf.CeilToInt(width);

                for (int ody = -w; ody <= w; ody++)
                {
                    for (int odx = -w; odx <= w; odx++)
                    {
                        int sx = ix + odx;
                        int sy = iy + ody;
                        if (sx < 0 || sx >= textureWidth || sy < 0 || sy >= textureHeight) continue;
                        float dist = Mathf.Sqrt(odx * odx + ody * ody);
                        if (dist > width) continue;
                        float fade = 1.0f - dist / width;
                        int idx = sy * textureWidth + sx;
                        colors[idx] = Color.Lerp(colors[idx], color, fade * 0.4f);
                    }
                }
            }
        }

        private void DrawParticles(Color[] colors, int count, Color color, System.Random rng)
        {
            for (int i = 0; i < count; i++)
            {
                int px = rng.Next(4, textureWidth - 4);
                int py = rng.Next(4, textureHeight - 4);
                float radius = 1.5f + (float)rng.NextDouble() * 2.5f;
                float brightness = 0.4f + (float)rng.NextDouble() * 0.6f;

                int r = Mathf.CeilToInt(radius);
                for (int dy = -r; dy <= r; dy++)
                {
                    for (int dx = -r; dx <= r; dx++)
                    {
                        int sx = px + dx;
                        int sy = py + dy;
                        if (sx < 0 || sx >= textureWidth || sy < 0 || sy >= textureHeight) continue;
                        float dist = Mathf.Sqrt(dx * dx + dy * dy);
                        if (dist > radius) continue;
                        float fade = 1.0f - dist / radius;
                        int idx = sy * textureWidth + sx;
                        colors[idx] = Color.Lerp(colors[idx], color, fade * brightness);
                    }
                }
            }
        }

        private void DrawGlowRing(Color[] colors, Color color)
        {
            float cx = textureWidth * 0.5f;
            float cy = textureHeight * 0.5f;
            float outerRadius = Mathf.Min(textureWidth, textureHeight) * 0.42f;
            float innerRadius = outerRadius - 6.0f;

            for (int y = 0; y < textureHeight; y++)
            {
                for (int x = 0; x < textureWidth; x++)
                {
                    float dist = Mathf.Sqrt((x - cx) * (x - cx) + (y - cy) * (y - cy));
                    if (dist >= innerRadius && dist <= outerRadius)
                    {
                        float mid = (innerRadius + outerRadius) * 0.5f;
                        float halfWidth = (outerRadius - innerRadius) * 0.5f;
                        float intensity = 1.0f - Mathf.Abs(dist - mid) / halfWidth;
                        int idx = y * textureWidth + x;
                        colors[idx] = Color.Lerp(colors[idx], color, intensity * 0.8f);
                    }
                    else if (dist > outerRadius && dist < outerRadius + 8.0f)
                    {
                        // Soft outer glow falloff
                        float falloff = 1.0f - (dist - outerRadius) / 8.0f;
                        int idx = y * textureWidth + x;
                        Color glowColor = color * 0.5f;
                        glowColor.a = 1.0f;
                        colors[idx] = Color.Lerp(colors[idx], glowColor, falloff * 0.3f);
                    }
                }
            }
        }

        private void DrawSigil(Color[] colors, Core.Archetypes.ArchetypeElement elem, Color color, System.Random rng)
        {
            float cx = textureWidth * 0.5f;
            float cy = textureHeight * 0.5f;
            float size = Mathf.Min(textureWidth, textureHeight) * 0.12f;

            // Inner sigil: element-specific small symbol
            switch (elem)
            {
                case Core.Archetypes.ArchetypeElement.Flame:
                    // Small diamond
                    DrawLine(colors, cx, cy - size, cx + size, cy, color, 2.0f);
                    DrawLine(colors, cx + size, cy, cx, cy + size, color, 2.0f);
                    DrawLine(colors, cx, cy + size, cx - size, cy, color, 2.0f);
                    DrawLine(colors, cx - size, cy, cx, cy - size, color, 2.0f);
                    break;
                case Core.Archetypes.ArchetypeElement.Tide:
                    // Small circle with dot
                    DrawConcentricCircles(colors, cx, cy, size, 1, color);
                    DrawParticles(colors, 1, color, rng);
                    break;
                case Core.Archetypes.ArchetypeElement.Gale:
                    // Cross
                    DrawLine(colors, cx - size, cy, cx + size, cy, color, 2.0f);
                    DrawLine(colors, cx, cy - size, cx, cy + size, color, 2.0f);
                    break;
            }
        }

        private void ApplyVignette(Color[] colors, float strength)
        {
            float cx = textureWidth * 0.5f;
            float cy = textureHeight * 0.5f;
            float maxDist = Mathf.Sqrt(cx * cx + cy * cy);

            for (int y = 0; y < textureHeight; y++)
            {
                for (int x = 0; x < textureWidth; x++)
                {
                    float dist = Mathf.Sqrt((x - cx) * (x - cx) + (y - cy) * (y - cy));
                    float vignette = Mathf.Clamp01(dist / maxDist);
                    vignette = vignette * vignette * strength; // quadratic falloff
                    int idx = y * textureWidth + x;
                    colors[idx] = Color.Lerp(colors[idx], Color.black, vignette);
                }
            }
        }

        private void OnDestroy()
        {
            if (_generatedTexture != null)
            {
                Destroy(_generatedTexture);
                _generatedTexture = null;
            }
        }
    }
}

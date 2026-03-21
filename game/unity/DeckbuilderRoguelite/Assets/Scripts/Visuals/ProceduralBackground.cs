using UnityEngine;

namespace Deckbuilder.Visuals
{
    /// <summary>
    /// Generates scrolling parallax background patterns using Perlin noise.
    /// Color-shifted by the current ThemePalette. Attach to a GameObject with
    /// a Renderer or RawImage to display the generated texture.
    /// </summary>
    public class ProceduralBackground : MonoBehaviour
    {
        [Header("Texture")]
        [SerializeField] private int textureWidth = 256;
        [SerializeField] private int textureHeight = 256;

        [Header("Noise")]
        [SerializeField] private float noiseScale = 6.0f;
        [SerializeField] private int octaves = 4;
        [SerializeField] private float persistence = 0.5f;
        [SerializeField] private float lacunarity = 2.0f;

        [Header("Scroll")]
        [SerializeField] private float scrollSpeedX = 0.02f;
        [SerializeField] private float scrollSpeedY = 0.01f;

        [Header("Parallax")]
        [SerializeField] private int layerCount = 3;
        [SerializeField] private float depthSpeedMultiplier = 0.5f;

        private Texture2D[] _layerTextures;
        private float[] _layerOffsets;
        private Color _paletteBackground = new Color(0.067f, 0.067f, 0.067f);
        private Color _palettePrimary = new Color(0.39f, 0.39f, 0.39f);
        private Color _paletteSecondary = new Color(0.31f, 0.31f, 0.31f);
        private Color _paletteAccent = new Color(0.78f, 0.63f, 0.16f);

        private void OnEnable()
        {
            Core.Theming.ThemeController.Instance.OnThemeChanged += OnThemeChanged;
            InitializeLayers();
        }

        private void OnDisable()
        {
            Core.Theming.ThemeController.Instance.OnThemeChanged -= OnThemeChanged;
            DestroyLayers();
        }

        private void OnThemeChanged(Core.Theming.ThemePalette palette)
        {
            _paletteBackground = palette.background;
            _palettePrimary = palette.primary;
            _paletteSecondary = palette.secondary;
            _paletteAccent = palette.accent;
            RegenerateLayers();
        }

        /// <summary>
        /// Set palette colors directly (useful when ThemeController hasn't been set up yet).
        /// </summary>
        public void SetPalette(Color background, Color primary, Color secondary, Color accent)
        {
            _paletteBackground = background;
            _palettePrimary = primary;
            _paletteSecondary = secondary;
            _paletteAccent = accent;
            RegenerateLayers();
        }

        private void InitializeLayers()
        {
            _layerTextures = new Texture2D[layerCount];
            _layerOffsets = new float[layerCount];

            for (int i = 0; i < layerCount; i++)
            {
                _layerTextures[i] = new Texture2D(textureWidth, textureHeight, TextureFormat.RGBA32, false);
                _layerTextures[i].filterMode = FilterMode.Bilinear;
                _layerTextures[i].wrapMode = TextureWrapMode.Repeat;
                _layerOffsets[i] = 0f;
            }

            RegenerateLayers();
        }

        private void DestroyLayers()
        {
            if (_layerTextures == null) return;
            for (int i = 0; i < _layerTextures.Length; i++)
            {
                if (_layerTextures[i] != null)
                {
                    Destroy(_layerTextures[i]);
                    _layerTextures[i] = null;
                }
            }
            _layerTextures = null;
        }

        private void RegenerateLayers()
        {
            if (_layerTextures == null) return;

            for (int layer = 0; layer < layerCount; layer++)
            {
                GenerateLayer(layer);
            }
        }

        private void GenerateLayer(int layerIndex)
        {
            var tex = _layerTextures[layerIndex];
            var colors = new Color[textureWidth * textureHeight];

            // Each layer uses a different noise seed offset and palette blend
            float seedOffset = layerIndex * 100f;
            float layerDepth = (float)layerIndex / Mathf.Max(1, layerCount - 1);

            // Deeper layers blend toward background; front layers toward primary/accent
            Color darkColor = Color.Lerp(_paletteBackground, _paletteSecondary, layerDepth * 0.3f);
            Color lightColor = Color.Lerp(_palettePrimary, _paletteAccent, layerDepth);

            // Deeper layers have lower contrast (more atmospheric)
            float contrastFade = 1.0f - layerDepth * 0.6f;

            for (int y = 0; y < textureHeight; y++)
            {
                for (int x = 0; x < textureWidth; x++)
                {
                    float nx = (float)x / textureWidth;
                    float ny = (float)y / textureHeight;
                    float noiseValue = SampleFractalNoise(nx, ny, seedOffset);

                    // Apply contrast reduction for deeper layers
                    noiseValue = 0.5f + (noiseValue - 0.5f) * contrastFade;

                    Color pixel = Color.Lerp(darkColor, lightColor, noiseValue);

                    // Deeper layers are more transparent for compositing
                    pixel.a = layerIndex == 0 ? 1.0f : 0.3f + 0.4f * (1.0f - layerDepth);

                    colors[y * textureWidth + x] = pixel;
                }
            }

            tex.SetPixels(colors);
            tex.Apply();
        }

        /// <summary>
        /// Fractal Brownian motion noise using Perlin noise octaves.
        /// Returns a value roughly in [0, 1].
        /// </summary>
        private float SampleFractalNoise(float x, float y, float seedOffset)
        {
            float amplitude = 1.0f;
            float frequency = noiseScale;
            float value = 0f;
            float maxValue = 0f;

            for (int i = 0; i < octaves; i++)
            {
                float sampleX = x * frequency + seedOffset;
                float sampleY = y * frequency + seedOffset * 0.7f;
                value += Mathf.PerlinNoise(sampleX, sampleY) * amplitude;
                maxValue += amplitude;
                amplitude *= persistence;
                frequency *= lacunarity;
            }

            return Mathf.Clamp01(value / maxValue);
        }

        private void Update()
        {
            if (_layerTextures == null) return;

            float dt = Time.deltaTime;

            for (int i = 0; i < layerCount; i++)
            {
                // Deeper layers scroll slower (parallax)
                float depthFactor = 1.0f - (float)i / layerCount * depthSpeedMultiplier;
                _layerOffsets[i] += dt * depthFactor;
            }
        }

        /// <summary>
        /// Get the texture for a specific parallax layer.
        /// Layer 0 is the farthest back; layerCount-1 is the closest.
        /// </summary>
        public Texture2D GetLayerTexture(int layerIndex)
        {
            if (_layerTextures == null || layerIndex < 0 || layerIndex >= _layerTextures.Length)
                return null;
            return _layerTextures[layerIndex];
        }

        /// <summary>
        /// Get the current scroll offset for a specific layer (for UV offset in materials).
        /// </summary>
        public Vector2 GetLayerScrollOffset(int layerIndex)
        {
            if (_layerOffsets == null || layerIndex < 0 || layerIndex >= _layerOffsets.Length)
                return Vector2.zero;

            float depthFactor = 1.0f - (float)layerIndex / layerCount * depthSpeedMultiplier;
            return new Vector2(
                _layerOffsets[layerIndex] * scrollSpeedX * depthFactor,
                _layerOffsets[layerIndex] * scrollSpeedY * depthFactor
            );
        }

        /// <summary>
        /// Number of parallax layers available.
        /// </summary>
        public int LayerCount => layerCount;
    }
}

# Production Setup Guide

Optimal workflow for high-quality audiobook production with a powerful GPU.

## Hardware Requirements

| Component | Minimum | Recommended | Your Setup |
|-----------|---------|-------------|------------|
| GPU | 8GB VRAM | 16GB+ VRAM | 5090 (32GB) |
| RAM | 16GB | 32GB+ | - |
| Storage | 50GB | 100GB+ SSD | - |

Your 5090 exceeds requirements for all current TTS models.

---

## Recommended TTS Models (Ranked by Quality)

### 1. Higgs Audio V2 (Primary Recommendation)

**Why**: 75% win rate vs GPT-4o-mini on emotional expression. Built on Llama 3.2 3B, trained on 10M+ hours.

```bash
# Installation
pip install higgs-audio
# or from source
git clone https://github.com/boson-ai/higgs-audio
cd higgs-audio
pip install -e .
```

**Best for**: Emotional children's narration, multi-character dialogue, audiobooks.

### 2. VibeVoice 7B (Long-Form Alternative)

**Why**: Microsoft model, handles up to 90 minutes continuous, excellent multi-speaker.

**Best for**: Longer works, consistent voice over extended passages.

### 3. FishAudio S1 (Voice Cloning Focus)

**Why**: Excellent voice cloning from 10-15 second samples, multilingual.

**Best for**: Matching specific voice references, international markets.

---

## Workflow Options

### Option A: Local Terminal (Simplest)

Direct control, no external dependencies.

```bash
# Using tts-audiobook-tool with Higgs V2
cd ~/tools/tts-audiobook-tool
python main.py \
    --input ~/StorytellingReferenceBank/projects/luna-the-little-cloud/drafts/manuscript-v1-tts.txt \
    --model higgs-v2 \
    --voice-ref ~/voices/warm-narrator.wav \
    --output ~/audiobooks/luna/
```

**Pros**: Full control, no latency, private
**Cons**: Manual trigger, no remote access

### Option B: GitHub Actions + Self-Hosted Runner (Automated)

Push manuscript → automatically generates audiobook.

**Setup self-hosted runner:**

```bash
# On your 5090 machine
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64.tar.gz -L https://github.com/actions/runner/releases/latest/download/actions-runner-linux-x64-2.XXX.X.tar.gz
tar xzf ./actions-runner-linux-x64.tar.gz
./config.sh --url https://github.com/YOUR_USER/StorytellingReferenceBank --token YOUR_TOKEN
./run.sh
```

**Workflow file** (`.github/workflows/produce-audiobook.yml`):

```yaml
name: Produce Audiobook

on:
  workflow_dispatch:
    inputs:
      project:
        description: 'Project folder name'
        required: true
        default: 'luna-the-little-cloud'
      model:
        description: 'TTS model'
        required: true
        default: 'higgs-v2'
        type: choice
        options:
          - higgs-v2
          - vibevoice-7b
          - fish-s1

jobs:
  produce:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4

      - name: Generate audiobook
        run: |
          cd ~/tools/tts-audiobook-tool
          python main.py \
            --input ${{ github.workspace }}/projects/${{ inputs.project }}/drafts/manuscript-v1-tts.txt \
            --model ${{ inputs.model }} \
            --output ${{ github.workspace }}/output/

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: audiobook-${{ inputs.project }}
          path: output/*.m4b
```

**Pros**: Version controlled, trigger from anywhere, automated
**Cons**: $0.002/min cost (negligible), setup complexity

### Option C: Local Web UI (Best of Both)

Run a simple web interface on your machine, accessible from any device on your network.

**Using Gradio:**

```python
# scripts/web_ui.py
import gradio as gr
from pathlib import Path

def generate_audiobook(manuscript, model, voice_ref):
    # Call your TTS pipeline
    # Return audio file path
    pass

demo = gr.Interface(
    fn=generate_audiobook,
    inputs=[
        gr.File(label="Manuscript"),
        gr.Dropdown(["higgs-v2", "vibevoice-7b", "fish-s1"], label="Model"),
        gr.Audio(label="Voice Reference (optional)", type="filepath"),
    ],
    outputs=gr.Audio(label="Generated Audiobook"),
    title="Storytelling TTS Studio"
)

demo.launch(server_name="0.0.0.0", server_port=7860)
```

Access from any device: `http://your-machine-ip:7860`

**Pros**: Easy to use, accessible from phone/tablet, visual feedback
**Cons**: Must keep machine running

---

## Recommended Setup (My Suggestion)

```
┌─────────────────────────────────────────────────────────┐
│                    Your 5090 Machine                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐    ┌──────────────────────────┐  │
│  │  StorytellingRef │───▶│  tts-audiobook-tool      │  │
│  │  (this repo)     │    │  (Higgs V2 backend)      │  │
│  └──────────────────┘    └──────────────────────────┘  │
│           │                         │                    │
│           ▼                         ▼                    │
│  ┌──────────────────┐    ┌──────────────────────────┐  │
│  │  Gradio Web UI   │    │  Output: M4B + Web Player│  │
│  │  (port 7860)     │    │                          │  │
│  └──────────────────┘    └──────────────────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
          ▲                           │
          │                           ▼
    ┌─────┴─────┐              ┌─────────────┐
    │ Any device│              │ ACX Upload  │
    │ (browser) │              │ or personal │
    └───────────┘              │ listening   │
                               └─────────────┘
```

**Why this setup:**
1. **tts-audiobook-tool** handles TTS complexity (Higgs V2, error correction, chapters)
2. **Gradio** gives you a simple web interface without full web dev
3. **Your toolkit** manages the creative side (story structure, personas, revision)
4. **GitHub** tracks versions, allows collaboration

---

## Quick Start

### Step 1: Install tts-audiobook-tool

```bash
cd ~
git clone https://github.com/zeropointnine/tts-audiobook-tool
cd tts-audiobook-tool
# Follow their Higgs V2 setup instructions
```

### Step 2: Install dependencies for your toolkit

```bash
cd ~/StorytellingReferenceBank
pip install gradio numpy soundfile
```

### Step 3: Create a bridge script

```bash
# scripts/produce.sh
#!/bin/bash
PROJECT=$1
MODEL=${2:-higgs-v2}

python ~/tts-audiobook-tool/main.py \
    --input "projects/${PROJECT}/drafts/manuscript-v1-tts.txt" \
    --config "projects/${PROJECT}/speaker-map.json" \
    --model "$MODEL" \
    --output "projects/${PROJECT}/output/"
```

### Step 4: Run

```bash
./scripts/produce.sh luna-the-little-cloud higgs-v2
```

---

## Cost Comparison

| Approach | Setup Time | Running Cost | Convenience |
|----------|------------|--------------|-------------|
| Local terminal | 1 hour | $0 (electricity) | Manual |
| GitHub self-hosted | 2-3 hours | ~$0.002/min | Automated |
| Gradio web UI | 30 min | $0 (electricity) | Very easy |
| Cloud GPU (Vast.ai) | 1 hour | ~$0.50/hour | Remote access |

With your hardware, **local + Gradio** is the sweet spot.

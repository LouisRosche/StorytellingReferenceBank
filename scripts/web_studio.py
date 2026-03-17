#!/usr/bin/env python3
"""
Storytelling TTS Studio - Web Interface

A Gradio-based web interface for audiobook production.
Access from any device on your network.

Usage:
    python web_studio.py
    # Then open http://localhost:7860 (or http://your-ip:7860 from other devices)

    # Custom port:
    python web_studio.py --port 8080

    # Allow external access:
    python web_studio.py --share
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple, List

# Check for required dependencies
try:
    import gradio as gr
except ImportError:
    print("Gradio not installed. Install with: pip install gradio")
    sys.exit(1)

# Add scripts dir to path for tts_providers import
sys.path.insert(0, str(Path(__file__).parent))

# Try to load tts_providers — graceful fallback if unavailable
_TTS_AVAILABLE = False
try:
    from tts_providers import get_provider, list_providers, TTSCapability
    _TTS_AVAILABLE = True
except ImportError:
    pass


# Get project root
PROJECT_ROOT = Path(__file__).parent.parent


def get_projects() -> List[str]:
    """Get list of available projects."""
    projects_dir = PROJECT_ROOT / "projects"
    if not projects_dir.exists():
        return []
    return [p.name for p in projects_dir.iterdir() if p.is_dir()]


def get_personas(project: Optional[str] = None) -> List[str]:
    """Get list of available personas."""
    personas = []

    # Global example personas
    examples_dir = PROJECT_ROOT / "personas" / "examples"
    if examples_dir.exists():
        for p in examples_dir.glob("*.json"):
            personas.append(f"examples/{p.stem}")

    # Project-specific personas
    if project:
        project_personas = PROJECT_ROOT / "projects" / project / "personas"
        if project_personas.exists():
            for p in project_personas.glob("*.json"):
                personas.append(f"{project}/{p.stem}")

    return personas


def get_manuscripts(project: str) -> List[str]:
    """Get list of manuscripts in a project."""
    drafts_dir = PROJECT_ROOT / "projects" / project / "drafts"
    if not drafts_dir.exists():
        return []
    return [m.name for m in drafts_dir.glob("*.txt")]


def _is_safe_path(resolved: Path, allowed_root: Path) -> bool:
    """Verify a resolved path is within the allowed root directory."""
    try:
        resolved.resolve().relative_to(allowed_root.resolve())
        return True
    except ValueError:
        return False


def load_manuscript(project: str, manuscript: str) -> str:
    """Load manuscript text."""
    path = PROJECT_ROOT / "projects" / project / "drafts" / manuscript
    if not _is_safe_path(path, PROJECT_ROOT):
        return ""
    if path.exists():
        return path.read_text()
    return ""


def load_persona_details(persona_path: str) -> str:
    """Load persona JSON for display."""
    if "/" in persona_path:
        parts = persona_path.split("/")
        if parts[0] == "examples":
            full_path = PROJECT_ROOT / "personas" / "examples" / f"{parts[1]}.json"
        else:
            full_path = PROJECT_ROOT / "projects" / parts[0] / "personas" / f"{parts[1]}.json"
    else:
        full_path = PROJECT_ROOT / "personas" / f"{persona_path}.json"

    if not _is_safe_path(full_path, PROJECT_ROOT):
        return "{}"
    if full_path.exists():
        return full_path.read_text()
    return "{}"


def _resolve_persona_path(persona_ref: str) -> Optional[Path]:
    """Resolve a persona dropdown value to a JSON file path."""
    if not persona_ref:
        return None
    parts = persona_ref.split("/")
    if parts[0] == "examples":
        resolved = PROJECT_ROOT / "personas" / "examples" / f"{parts[1]}.json"
    else:
        resolved = PROJECT_ROOT / "projects" / parts[0] / "personas" / f"{parts[1]}.json"
    if not _is_safe_path(resolved, PROJECT_ROOT):
        return None
    return resolved


def _load_voice_prompt(persona_path: Path) -> str:
    """Load voice_prompt from a persona JSON file."""
    if persona_path and persona_path.exists():
        with open(persona_path) as f:
            data = json.load(f)
        return data.get("voice_prompt", "")
    return ""


def generate_audio(
    text: str,
    persona: str,
    provider_id: str,
    progress=gr.Progress()
) -> Tuple[Optional[str], str]:
    """Generate audio using the built-in tts_providers system."""
    if not text or not text.strip():
        return None, "No text provided."

    log = []
    log.append(f"Provider: {provider_id}")
    log.append(f"Persona: {persona}")
    log.append(f"Text: {len(text)} characters")

    if not _TTS_AVAILABLE:
        log.append("")
        log.append("tts_providers not available. Install dependencies:")
        log.append("  pip install qwen-tts torch soundfile numpy")
        log.append("")
        log.append("Available providers: qwen (local), elevenlabs, openai, coqui")
        return None, "\n".join(log)

    try:
        # Resolve persona
        progress(0.1, desc="Loading persona...")
        persona_path = _resolve_persona_path(persona)
        voice_prompt = _load_voice_prompt(persona_path)
        if voice_prompt:
            log.append(f"Voice prompt loaded ({len(voice_prompt)} chars)")
        else:
            log.append("No persona selected, using provider default voice")

        # Get provider
        progress(0.2, desc="Initializing provider...")
        provider = get_provider(provider_id)
        log.append(f"Provider: {provider.name}")

        # Generate
        progress(0.4, desc="Generating audio...")
        result = provider.generate(
            text=text,
            voice=voice_prompt if voice_prompt else None,
        )
        log.append(f"Generated: {result.duration_seconds:.1f}s at {result.sample_rate} Hz")

        # Save to temp file
        progress(0.8, desc="Saving...")
        output_path = os.path.join(tempfile.gettempdir(), "web_studio_output.wav")
        provider.save_audio(result, output_path)
        log.append(f"Saved: {output_path}")

        progress(1.0, desc="Done")
        return output_path, "\n".join(log)

    except Exception as e:
        log.append(f"\nError: {e}")
        log.append(f"\nEnsure the provider '{provider_id}' is installed and configured.")
        return None, "\n".join(log)


def create_interface():
    """Create the Gradio interface."""

    with gr.Blocks(
        title="Storytelling TTS Studio",
        theme=gr.themes.Soft()
    ) as app:

        gr.Markdown("""
        # Storytelling TTS Studio

        Generate audiobooks from your manuscripts using AI voices.
        """)

        with gr.Tabs():
            # Tab 1: Quick Generate
            with gr.Tab("Quick Generate"):
                with gr.Row():
                    with gr.Column(scale=2):
                        text_input = gr.Textbox(
                            label="Text to generate",
                            placeholder="Enter or paste text here...",
                            lines=10
                        )

                    with gr.Column(scale=1):
                        _providers = list(list_providers().keys()) if _TTS_AVAILABLE else ["qwen"]
                        model_select = gr.Dropdown(
                            choices=_providers,
                            value=_providers[0] if _providers else "qwen",
                            label="TTS Provider"
                        )

                        persona_select = gr.Dropdown(
                            choices=get_personas(),
                            label="Voice Persona"
                        )

                        generate_btn = gr.Button("Generate Audio", variant="primary")

                with gr.Row():
                    audio_output = gr.Audio(label="Generated Audio", type="filepath")
                    status_output = gr.Textbox(label="Status", lines=10)

                generate_btn.click(
                    fn=generate_audio,
                    inputs=[text_input, persona_select, model_select],
                    outputs=[audio_output, status_output]
                )

            # Tab 2: Project Production
            with gr.Tab("Project Production"):
                with gr.Row():
                    project_select = gr.Dropdown(
                        choices=get_projects(),
                        label="Select Project"
                    )
                    refresh_btn = gr.Button("Refresh Projects")

                with gr.Row():
                    manuscript_select = gr.Dropdown(
                        label="Select Manuscript"
                    )

                manuscript_preview = gr.Textbox(
                    label="Manuscript Preview",
                    lines=15,
                    interactive=False
                )

                with gr.Row():
                    project_persona = gr.Dropdown(
                        label="Voice Persona"
                    )
                    project_model = gr.Dropdown(
                        choices=_providers,
                        value=_providers[0] if _providers else "qwen",
                        label="TTS Provider"
                    )

                produce_btn = gr.Button("Produce Audiobook", variant="primary")
                production_status = gr.Textbox(label="Production Status", lines=10)

                # Update manuscripts when project changes
                def update_project(project):
                    manuscripts = get_manuscripts(project) if project else []
                    personas = get_personas(project)
                    return (
                        gr.update(choices=manuscripts, value=manuscripts[0] if manuscripts else None),
                        gr.update(choices=personas, value=personas[0] if personas else None)
                    )

                project_select.change(
                    fn=update_project,
                    inputs=[project_select],
                    outputs=[manuscript_select, project_persona]
                )

                # Load manuscript preview
                def load_preview(project, manuscript):
                    if project and manuscript:
                        return load_manuscript(project, manuscript)
                    return ""

                manuscript_select.change(
                    fn=load_preview,
                    inputs=[project_select, manuscript_select],
                    outputs=[manuscript_preview]
                )

                # Refresh projects
                def refresh_projects():
                    return gr.update(choices=get_projects())

                refresh_btn.click(
                    fn=refresh_projects,
                    outputs=[project_select]
                )

            # Tab 3: Persona Editor
            with gr.Tab("Persona Editor"):
                gr.Markdown("### Create or Edit Voice Personas")

                with gr.Row():
                    with gr.Column():
                        persona_name = gr.Textbox(label="Persona Name (ID)")
                        persona_display_name = gr.Textbox(label="Display Name")
                        voice_prompt = gr.Textbox(
                            label="Voice Prompt",
                            lines=5,
                            placeholder="Perfect audio quality. Describe the voice in natural language..."
                        )

                    with gr.Column():
                        age_range = gr.Textbox(label="Age Range", placeholder="30s, 40s-50s, elderly")
                        gender = gr.Dropdown(
                            choices=["neutral", "male", "female"],
                            label="Gender"
                        )
                        pitch = gr.Dropdown(
                            choices=["low", "medium-low", "medium", "medium-high", "high"],
                            label="Pitch"
                        )
                        pace = gr.Dropdown(
                            choices=["slow", "measured", "medium", "natural", "fast"],
                            label="Pace"
                        )
                        accent = gr.Textbox(label="Accent", placeholder="American neutral, British RP, etc.")

                with gr.Row():
                    emotional_range = gr.Textbox(
                        label="Emotional Range (comma-separated)",
                        placeholder="warm, reflective, sardonic, tender"
                    )
                    use_cases = gr.Textbox(
                        label="Use Cases (comma-separated)",
                        placeholder="literary fiction, memoir, audiobooks"
                    )

                persona_json_output = gr.Code(label="Generated Persona JSON", language="json")

                def generate_persona_json(name, display, prompt, age, gender, pitch, pace, accent, emotions, uses):
                    persona = {
                        "id": name or "unnamed-persona",
                        "name": display or "Unnamed Persona",
                        "voice_prompt": prompt or "",
                        "voice_attributes": {
                            "age_range": age or "",
                            "gender": gender or "neutral",
                            "pitch": pitch or "medium",
                            "pace": pace or "natural",
                            "accent": accent or "",
                            "languages": ["en"]
                        },
                        "emotional_range": [e.strip() for e in (emotions or "").split(",") if e.strip()],
                        "use_cases": [u.strip() for u in (uses or "").split(",") if u.strip()],
                        "model_variant": "1.7B-VoiceDesign"
                    }
                    return json.dumps(persona, indent=2)

                # Update JSON on any change
                for input_component in [persona_name, persona_display_name, voice_prompt, age_range,
                                       gender, pitch, pace, accent, emotional_range, use_cases]:
                    input_component.change(
                        fn=generate_persona_json,
                        inputs=[persona_name, persona_display_name, voice_prompt, age_range,
                               gender, pitch, pace, accent, emotional_range, use_cases],
                        outputs=[persona_json_output]
                    )

            # Tab 4: Voice Cloning
            with gr.Tab("Voice Cloning"):
                gr.Markdown("""
                ### Voice Cloning

                Clone a voice from reference audio. You must have rights to use the voice.
                """)

                with gr.Row():
                    reference_audio = gr.Audio(
                        label="Reference Audio (10-30 seconds)",
                        type="filepath"
                    )

                    with gr.Column():
                        clone_name = gr.Textbox(label="Voice Name")
                        clone_notes = gr.Textbox(
                            label="Notes",
                            lines=3,
                            placeholder="Source, rights, intended use..."
                        )

                test_text = gr.Textbox(
                    label="Test Text",
                    value="This is a test of the cloned voice. The quick brown fox jumps over the lazy dog.",
                    lines=2
                )

                clone_btn = gr.Button("Test Clone", variant="primary")
                clone_output = gr.Audio(label="Cloned Voice Output")
                clone_status = gr.Textbox(label="Status")

                def clone_voice(ref_audio, name, text):
                    if not _TTS_AVAILABLE:
                        return None, "tts_providers not available. Install with: pip install qwen-tts torch"
                    if not ref_audio:
                        return None, "Provide reference audio."
                    if not text:
                        return None, "Provide test text."
                    try:
                        provider = get_provider("qwen")
                        if not provider.supports(TTSCapability.VOICE_CLONING):
                            return None, f"{provider.name} does not support voice cloning."
                        result = provider.generate_from_reference(
                            text=text,
                            reference_audio=ref_audio,
                        )
                        out = os.path.join(tempfile.gettempdir(), "clone_test.wav")
                        provider.save_audio(result, out)
                        return out, f"Cloned voice '{name}': {result.duration_seconds:.1f}s"
                    except Exception as e:
                        return None, f"Error: {e}"

                clone_btn.click(
                    fn=clone_voice,
                    inputs=[reference_audio, clone_name, test_text],
                    outputs=[clone_output, clone_status]
                )

            # Tab 5: Voice Finder (Bespoke Personalities)
            with gr.Tab("Voice Finder"):
                gr.Markdown("""
                ### Find the Right Voice for Your Story

                Describe your story and get persona recommendations ranked by compatibility.
                """)

                with gr.Row():
                    with gr.Column(scale=2):
                        story_genre = gr.Dropdown(
                            choices=[
                                "literary fiction", "thriller", "mystery", "romance",
                                "fantasy", "sci-fi", "horror", "memoir", "children's",
                                "young adult", "historical", "humor", "self-help"
                            ],
                            label="Genre",
                            value="literary fiction"
                        )
                        story_tone = gr.CheckboxGroup(
                            choices=[
                                "warm", "contemplative", "dark", "playful", "serious",
                                "intimate", "epic", "humorous", "tense", "melancholic"
                            ],
                            label="Tone (select all that apply)",
                            value=["contemplative"]
                        )
                        story_audience = gr.Dropdown(
                            choices=["children", "young adult", "adult", "all ages"],
                            label="Target Audience",
                            value="adult"
                        )
                        story_language = gr.Dropdown(
                            choices=["en", "es", "fr", "de"],
                            label="Language",
                            value="en"
                        )

                    with gr.Column(scale=1):
                        gr.Markdown("#### Optional Details")
                        cultural_context = gr.Textbox(
                            label="Cultural Context",
                            placeholder="Caribbean diaspora, Indian heritage, etc."
                        )
                        special_needs = gr.Textbox(
                            label="Special Requirements",
                            placeholder="Bilingual, specific accent, etc."
                        )

                find_voice_btn = gr.Button("Find Matching Voices", variant="primary")

                gr.Markdown("### Recommendations")
                recommendations_output = gr.Dataframe(
                    headers=["Rank", "Persona", "Score", "Why"],
                    label="Top Matches",
                    interactive=False
                )

                selected_persona_details = gr.Code(
                    label="Selected Persona Details",
                    language="json"
                )

                def find_matching_voices(genre, tone, audience, language, cultural, special):
                    """Score personas against story requirements."""
                    # Load all personas
                    personas_dir = PROJECT_ROOT / "personas" / "examples"
                    results = []

                    for persona_file in personas_dir.glob("*.json"):
                        try:
                            with open(persona_file) as f:
                                persona = json.load(f)

                            score = 0.0
                            reasons = []

                            # Genre matching (30%)
                            use_cases = persona.get("use_cases", [])
                            genre_words = genre.lower().split()
                            for uc in use_cases:
                                if any(w in uc.lower() for w in genre_words):
                                    score += 0.30
                                    reasons.append(f"Genre: {uc}")
                                    break

                            # Tone matching (25%)
                            emotional_range = persona.get("emotional_range", [])
                            tone_matches = sum(1 for t in tone if any(t.lower() in e.lower() for e in emotional_range))
                            if tone_matches > 0:
                                tone_score = min(0.25, 0.10 * tone_matches)
                                score += tone_score
                                reasons.append(f"Tone: {tone_matches} matches")

                            # Language (20%)
                            languages = persona.get("voice_attributes", {}).get("languages", ["en"])
                            if language in languages:
                                score += 0.20
                                reasons.append(f"Language: {language}")

                            # Audience (15%)
                            if audience == "children" and "children" in str(use_cases).lower():
                                score += 0.15
                                reasons.append("Children's specialist")
                            elif audience == "young adult" and any("ya" in uc.lower() or "young" in uc.lower() for uc in use_cases):
                                score += 0.15
                                reasons.append("YA suitable")
                            elif audience == "adult":
                                score += 0.10
                                reasons.append("Adult content")

                            # Cultural context bonus (10%)
                            if cultural:
                                accent = persona.get("voice_attributes", {}).get("accent", "")
                                if any(c.lower() in accent.lower() for c in cultural.split()):
                                    score += 0.10
                                    reasons.append(f"Cultural: {accent}")

                            results.append({
                                "id": persona.get("id", persona_file.stem),
                                "name": persona.get("name", persona_file.stem),
                                "score": score,
                                "reasons": ", ".join(reasons[:3]) if reasons else "General match"
                            })

                        except Exception as e:
                            continue

                    # Sort by score
                    results.sort(key=lambda x: x["score"], reverse=True)

                    # Format for display
                    table_data = [
                        [i + 1, r["name"], f"{r['score']:.0%}", r["reasons"]]
                        for i, r in enumerate(results[:8])
                    ]

                    return table_data

                find_voice_btn.click(
                    fn=find_matching_voices,
                    inputs=[story_genre, story_tone, story_audience, story_language, cultural_context, special_needs],
                    outputs=[recommendations_output]
                )

                # Show persona details on row select
                def show_persona_details(evt: gr.SelectData, data):
                    if evt.index and len(evt.index) > 0:
                        row_idx = evt.index[0]
                        if row_idx < len(data):
                            persona_name = data[row_idx][1]
                            # Find and load persona
                            personas_dir = PROJECT_ROOT / "personas" / "examples"
                            for pf in personas_dir.glob("*.json"):
                                with open(pf) as f:
                                    p = json.load(f)
                                    if p.get("name") == persona_name:
                                        return json.dumps(p, indent=2)
                    return "{}"

                recommendations_output.select(
                    fn=show_persona_details,
                    inputs=[recommendations_output],
                    outputs=[selected_persona_details]
                )

            # Tab 6: Settings
            with gr.Tab("Settings"):
                gr.Markdown("### Production Settings")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### Audio Output")
                        output_format = gr.Dropdown(
                            choices=["mp3", "wav", "flac", "m4b"],
                            value="mp3",
                            label="Output Format"
                        )
                        sample_rate = gr.Dropdown(
                            choices=["44100", "48000"],
                            value="44100",
                            label="Sample Rate (Hz)"
                        )
                        bitrate = gr.Dropdown(
                            choices=["128", "192", "256", "320"],
                            value="192",
                            label="Bitrate (kbps)"
                        )

                    with gr.Column():
                        gr.Markdown("#### Processing")
                        normalize = gr.Checkbox(label="Normalize to ACX spec", value=True)
                        noise_reduction = gr.Checkbox(label="Apply noise reduction", value=True)
                        room_tone = gr.Checkbox(label="Add room tone (head/tail)", value=True)

                gr.Markdown("### TTS Provider")
                tts_backend = gr.Dropdown(
                    choices=_providers,
                    value=_providers[0] if _providers else "qwen",
                    label="Default Provider"
                )
                provider_info = gr.Textbox(
                    label="Provider Status",
                    value="Available" if _TTS_AVAILABLE else "Not installed (pip install qwen-tts torch)",
                    interactive=False
                )

                save_settings_btn = gr.Button("Save Settings")

        return app


def main():
    parser = argparse.ArgumentParser(description="Storytelling TTS Studio")
    parser.add_argument("--port", type=int, default=7860, help="Port to run on")
    parser.add_argument("--share", action="store_true", help="Create public URL")
    parser.add_argument("--host", default="127.0.0.1",
                        help="Host to bind to (use 0.0.0.0 for network access)")

    args = parser.parse_args()

    app = create_interface()

    tts_status = "READY" if _TTS_AVAILABLE else "NOT INSTALLED (pip install qwen-tts torch)"
    print(f"""
  Storytelling TTS Studio
  Local:    http://localhost:{args.port}
  Network:  http://YOUR_IP:{args.port}
  TTS:      {tts_status}
  Providers: {', '.join(list_providers().keys()) if _TTS_AVAILABLE else 'none'}
    """)

    app.launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share
    )


if __name__ == "__main__":
    main()

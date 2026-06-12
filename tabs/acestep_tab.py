"""
ACE-Step Music Generation Tab for Hyper-RVC.

Provides a Gradio interface for:
- Simple Mode: Describe music in natural language, LM auto-generates caption + lyrics
- Custom Mode: Manual text2music with caption, lyrics, and metadata controls
- Cover Mode: Style-transfer / re-style existing audio
- Repaint Mode: Regenerate a specific segment of audio

Models are lazily loaded and can be hot-swapped without restarting the app.
"""

import os
import sys
import gradio as gr
import torch

now_dir = os.getcwd()
sys.path.append(now_dir)

from assets.i18n.i18n import I18nAuto
from main.acestep_inference import (
    initialize_handlers,
    unload_handlers,
    is_initialized,
    run_acestep_inference,
    run_acestep_simple_mode,
    get_available_dit_models,
    get_available_lm_models,
    get_output_files,
    clear_output_files,
)
from main.tools.logger import get_logger
from main.tools.variables import (
    ACESTEP_VALID_LANGUAGES as VALID_LANGUAGES,
    ACESTEP_AUDIO_FORMATS as AUDIO_FORMATS,
    ACESTEP_DIT_MODEL_CHOICES as DIT_MODEL_CHOICES,
    ACESTEP_LM_MODEL_CHOICES as LM_MODEL_CHOICES,
    ACESTEP_TIME_SIGNATURE_MAP as TIME_SIGNATURE_MAP,
    ACESTEP_TASK_MODES as TASK_MODES,
    ACESTEP_HF_ORG,
    ACESTEP_HF_REPO,
    ACESTEP_HF_MODELS,
    ACESTEP_GITHUB_REPO,
    get_acestep_defaults,
)

logger = get_logger(__name__)
i18n = I18nAuto()

# ---------------------------------------------------------------------------
# Constants are imported from main/tools/variables.py
# ---------------------------------------------------------------------------
# VALID_LANGUAGES, AUDIO_FORMATS, DIT_MODEL_CHOICES, LM_MODEL_CHOICES,
# TIME_SIGNATURE_MAP, TASK_MODES are all defined centrally in variables.py
# and imported above. Do NOT redefine them here.


# ---------------------------------------------------------------------------
# Tab builder
# ---------------------------------------------------------------------------

def acestep_tab():
    """Create the ACE-Step Music Generation tab."""

    with gr.Tabs():

        # ===== Model Loading =====
        with gr.Tab(i18n("Model Setup")):

            with gr.Row():
                _acestep_defaults = get_acestep_defaults()
                dit_model = gr.Dropdown(
                    label=i18n("DiT Model (Audio Generator)"),
                    info=i18n("Select the DiT model. Models auto-download from HuggingFace on first use."),
                    choices=DIT_MODEL_CHOICES,
                    value=_acestep_defaults["dit_model"],
                    interactive=True,
                    allow_custom_value=True,
                )
                lm_model = gr.Dropdown(
                    label=i18n("LM Model (Reasoning Planner)"),
                    info=i18n("Select the LM model for Chain-of-Thought reasoning. Optional but improves quality."),
                    choices=LM_MODEL_CHOICES,
                    value=_acestep_defaults["lm_model"],
                    interactive=True,
                    allow_custom_value=True,
                )

            with gr.Row():
                use_lm = gr.Checkbox(
                    label=i18n("Enable LM (recommended)"),
                    info=i18n("Load the 5Hz LM for metadata inference and audio-code planning."),
                    value=_acestep_defaults["use_lm"],
                    interactive=True,
                )
                lm_backend = gr.Radio(
                    label=i18n("LM Backend"),
                    choices=["vllm", "pytorch"],
                    value=_acestep_defaults["lm_backend"],
                    interactive=True,
                    visible=True,
                )
                device = gr.Dropdown(
                    label=i18n("Device"),
                    choices=["auto", "cuda", "mps", "cpu"],
                    value=_acestep_defaults["device"],
                    interactive=True,
                )

            with gr.Row():
                load_btn = gr.Button(
                    i18n("Load Models"),
                    variant="primary",
                    size="lg",
                )
                unload_btn = gr.Button(
                    i18n("Unload Models"),
                    variant="stop",
                    size="lg",
                )

            model_status = gr.Textbox(
                label=i18n("Model Status"),
                lines=2,
                interactive=False,
                value="No models loaded.",
            )

            # About section
            with gr.Accordion(i18n("About ACE-Step"), open=False):
                gr.Markdown(
                    value="""
                    ### ACE-Step 1.5 — Open-Source Text-to-Music Foundation Model

                    **Developed by:** ACE Studio + StepFun

                    **What it does:** Generates complete songs (vocals + instruments) from text descriptions and lyrics.

                    **Architecture:** Two-brain hybrid design:
                    - **5Hz LM (Planner):** Infers BPM, key, lyrics, and produces semantic audio codes
                    - **DiT (Executor):** Generates audio via flow-matching diffusion (noise → music)

                    **Model Links (HuggingFace):**
                    - All models: [ACE-Step/Ace-Step1.5](https://huggingface.co/ACE-Step/Ace-Step1.5)
                    - Turbo (recommended): [acestep-v15-turbo](https://huggingface.co/ACE-Step/acestep-v15-turbo) (~4.7GB, 8 steps)
                    - SFT: [acestep-v15-sft](https://huggingface.co/ACE-Step/acestep-v15-sft) (~4.7GB, 50 steps, CFG)
                    - Base: [acestep-v15-base](https://huggingface.co/ACE-Step/acestep-v15-base) (~4.7GB, all tasks)
                    - XL Turbo: [acestep-v15-xl-turbo](https://huggingface.co/ACE-Step/acestep-v15-xl-turbo) (~9GB, higher quality)

                    **GitHub:** [ACE-Step/ACE-Step-1.5](https://github.com/ACE-Step/ACE-Step-1.5)

                    **License:** MIT
                    """
                )

        # ===== Generation Modes =====
        with gr.Tab(i18n("Generate")):

            mode_selector = gr.Radio(
                label=i18n("Generation Mode"),
                choices=TASK_MODES,
                value="Simple",
                interactive=True,
            )

            # ---- Simple Mode ----
            with gr.Column(visible=True) as simple_mode_col:
                simple_query = gr.Textbox(
                    label=i18n("Describe the Music"),
                    info=i18n("Describe the music you want in natural language. The LM will auto-generate caption, lyrics, BPM, key, etc."),
                    placeholder="e.g. A soft Bengali love song for a quiet evening",
                    lines=3,
                    max_lines=10,
                )
                simple_lang = gr.Dropdown(
                    label=i18n("Vocal Language"),
                    choices=VALID_LANGUAGES,
                    value="en",
                    interactive=True,
                )

            # ---- Custom / Cover / Repaint shared controls ----
            with gr.Column(visible=False) as custom_mode_col:

                caption_input = gr.Textbox(
                    label=i18n("Caption / Description"),
                    info=i18n("Describe the desired music style, genre, mood, instruments, etc. (max 512 chars)"),
                    placeholder="upbeat electronic dance music with heavy bass and synth leads",
                    lines=2,
                    max_lines=5,
                )

                lyrics_input = gr.Textbox(
                    label=i18n("Lyrics"),
                    info=i18n("Paste lyrics or use [Instrumental]. Use [Verse], [Chorus] tags for structure. (max 4096 chars)"),
                    placeholder="[Verse 1]\nHello world, the sun is bright\n[Chorus]\nWe dance into the night",
                    lines=5,
                    max_lines=20,
                )

                with gr.Row():
                    instrumental_chk = gr.Checkbox(
                        label=i18n("Instrumental"),
                        info=i18n("Generate instrumental music (no vocals)"),
                        value=False,
                        interactive=True,
                    )
                    vocal_lang = gr.Dropdown(
                        label=i18n("Vocal Language"),
                        choices=VALID_LANGUAGES,
                        value="en",
                        interactive=True,
                    )

                # Audio upload (cover / repaint)
                with gr.Column(visible=False) as src_audio_col:
                    src_audio_input = gr.Audio(
                        label=i18n("Source Audio"),
                        type="filepath",
                        interactive=True,
                    )

                # Repaint time range
                with gr.Column(visible=False) as repaint_settings_col:
                    with gr.Row():
                        repaint_start = gr.Slider(
                            label=i18n("Repaint Start (s)"),
                            minimum=0,
                            maximum=600,
                            value=0.0,
                            step=0.1,
                            interactive=True,
                        )
                        repaint_end = gr.Slider(
                            label=i18n("Repaint End (s)"),
                            minimum=-1,
                            maximum=600,
                            value=-1,
                            step=0.1,
                            interactive=True,
                            info="-1 = until end",
                        )
                    cover_strength = gr.Slider(
                        label=i18n("Cover Strength"),
                        minimum=0.0,
                        maximum=1.0,
                        value=0.8,
                        step=0.05,
                        interactive=True,
                        info="How much to keep from the original (cover mode)",
                        visible=False,
                    )

                # Metadata
                with gr.Accordion(i18n("Music Metadata"), open=False):
                    with gr.Row():
                        bpm_input = gr.Slider(
                            label=i18n("BPM"),
                            minimum=30,
                            maximum=300,
                            value=None,
                            step=1,
                            interactive=True,
                            info="Leave empty for auto",
                        )
                        duration_input = gr.Slider(
                            label=i18n("Duration (s)"),
                            minimum=10,
                            maximum=600,
                            value=30,
                            step=1,
                            interactive=True,
                            info="Seconds",
                        )
                    with gr.Row():
                        keyscale_input = gr.Textbox(
                            label=i18n("Key Scale"),
                            placeholder="C Major",
                            value="",
                            interactive=True,
                        )
                        time_sig_input = gr.Dropdown(
                            label=i18n("Time Signature"),
                            choices=list(TIME_SIGNATURE_MAP.keys()),
                            value="Auto",
                            interactive=True,
                        )

            # ---- Advanced Settings (shared) ----
            with gr.Accordion(i18n("Advanced Settings"), open=False):
                with gr.Row():
                    inference_steps = gr.Slider(
                        label=i18n("Inference Steps"),
                        info=i18n("8 for turbo, 50 for sft/base"),
                        minimum=1,
                        maximum=100,
                        value=_acestep_defaults["inference_steps"],
                        step=1,
                        interactive=True,
                    )
                    guidance_scale = gr.Slider(
                        label=i18n("Guidance Scale (CFG)"),
                        info=i18n("Higher = follow prompt more strictly (sft/base only)"),
                        minimum=1.0,
                        maximum=20.0,
                        value=_acestep_defaults["guidance_scale"],
                        step=0.5,
                        interactive=True,
                    )
                    seed_input = gr.Slider(
                        label=i18n("Seed"),
                        minimum=-1,
                        maximum=2147483647,
                        value=_acestep_defaults["seed"],
                        step=1,
                        interactive=True,
                        info="-1 = random",
                    )
                    batch_size = gr.Slider(
                        label=i18n("Batch Size"),
                        minimum=1,
                        maximum=4,
                        value=_acestep_defaults["batch_size"],
                        step=1,
                        interactive=True,
                        info="Number of outputs",
                    )
                with gr.Row():
                    thinking_chk = gr.Checkbox(
                        label=i18n("Enable LM Thinking (CoT)"),
                        info=i18n("Let LM plan metadata and audio codes"),
                        value=_acestep_defaults["thinking"],
                        interactive=True,
                    )
                    lm_temp = gr.Slider(
                        label=i18n("LM Temperature"),
                        minimum=0.0,
                        maximum=2.0,
                        value=_acestep_defaults["lm_temperature"],
                        step=0.05,
                        interactive=True,
                    )
                    audio_format = gr.Dropdown(
                        label=i18n("Output Format"),
                        choices=AUDIO_FORMATS,
                        value=_acestep_defaults["audio_format"],
                        interactive=True,
                    )

            # ---- Action buttons ----
            with gr.Row():
                generate_btn = gr.Button(
                    i18n("Generate Music"),
                    variant="primary",
                    size="lg",
                )
                clear_btn = gr.Button(
                    i18n("Clear"),
                    variant="stop",
                    size="lg",
                )

            # ---- Output ----
            with gr.Row():
                with gr.Column():
                    status_output = gr.Textbox(
                        label=i18n("Status"),
                        lines=3,
                        interactive=False,
                    )
                    audio_output = gr.Audio(
                        label=i18n("Generated Audio"),
                        type="filepath",
                        interactive=False,
                    )
                with gr.Column():
                    output_gallery = gr.File(
                        label=i18n("All Generated Files"),
                        interactive=False,
                    )
                    refresh_files_btn = gr.Button(
                        i18n("Refresh Files"),
                        size="sm",
                    )
                    clear_files_btn = gr.Button(
                        i18n("Clear All Outputs"),
                        size="sm",
                    )

    # ===================================================================
    # Event handlers
    # ===================================================================

    def toggle_lm_visibility(checked):
        return gr.update(visible=checked)

    def on_mode_change(mode):
        """Show/hide sections based on generation mode."""
        is_simple = mode == "Simple"
        is_cover = mode == "Cover"
        is_repaint = mode == "Repaint"
        needs_src = is_cover or is_repaint

        simple_visible = is_simple
        custom_visible = not is_simple
        src_visible = needs_src
        repaint_visible = is_repaint
        cover_str_visible = is_cover

        return (
            gr.update(visible=simple_visible),   # simple_mode_col
            gr.update(visible=custom_visible),   # custom_mode_col
            gr.update(visible=src_visible),      # src_audio_col
            gr.update(visible=repaint_visible),  # repaint_settings_col
            gr.update(visible=cover_str_visible), # cover_strength
        )

    def load_models_fn(dit, lm, use_lm_flag, backend, dev):
        return initialize_handlers(
            dit_model=dit,
            lm_model=lm,
            lm_backend=backend,
            device=dev,
            use_lm=use_lm_flag,
        )

    def generate_fn(mode, *args):
        """Route to the correct generation function based on mode."""
        if not is_initialized():
            return "Error: Models not loaded. Go to Model Setup and load models first.", None

        if mode == "Simple":
            # Simple mode args: query, lang, duration, steps, seed, batch, format
            query = args[0]
            lang = args[1]
            # Advanced settings indices (shared across all modes)
            duration = args[11]
            steps = args[14]
            seed = args[16]
            batch = args[17]
            fmt = args[20]
            return run_acestep_simple_mode(
                query=query,
                vocal_language=lang,
                duration=int(duration) if duration else 30,
                inference_steps=steps,
                seed=int(seed),
                batch_size=int(batch),
                audio_format=fmt,
            )

        else:
            # Custom / Cover / Repaint
            caption = args[2]
            lyrics = args[3]
            instrumental = args[4]
            vocal_lang = args[5]
            src_audio = args[6]
            repaint_start = args[7]
            repaint_end = args[8]
            cover_str = args[9]
            bpm = int(args[10]) if args[10] else None
            duration = args[11]
            keyscale = args[12]
            timesig = TIME_SIGNATURE_MAP.get(args[13], "")
            steps = args[14]
            guidance = args[15]
            seed = int(args[16])
            batch = int(args[17])
            thinking = args[18]
            lm_temp = args[19]
            fmt = args[20]

            task_map = {
                "Custom": "text2music",
                "Cover": "cover",
                "Repaint": "repaint",
            }
            task = task_map.get(mode, "text2music")

            return run_acestep_inference(
                task_type=task,
                caption=caption,
                lyrics=lyrics,
                instrumental=instrumental,
                bpm=bpm,
                keyscale=keyscale,
                timesignature=timesig,
                vocal_language=vocal_lang,
                duration=duration,
                src_audio=src_audio,
                audio_cover_strength=cover_str,
                repainting_start=repaint_start,
                repainting_end=repaint_end,
                inference_steps=steps,
                guidance_scale=guidance,
                seed=seed,
                batch_size=batch,
                thinking=thinking,
                lm_temperature=lm_temp,
                audio_format=fmt,
            )

    def refresh_files():
        files = get_output_files()
        return files if files else []

    def clear_outputs():
        clear_output_files()
        return "", None, []

    # ===================================================================
    # Connect events
    # ===================================================================

    use_lm.change(
        fn=toggle_lm_visibility,
        inputs=[use_lm],
        outputs=[lm_backend],
    )

    mode_selector.change(
        fn=on_mode_change,
        inputs=[mode_selector],
        outputs=[simple_mode_col, custom_mode_col, src_audio_col, repaint_settings_col, cover_strength],
    )

    load_btn.click(
        fn=load_models_fn,
        inputs=[dit_model, lm_model, use_lm, lm_backend, device],
        outputs=[model_status],
    )

    unload_btn.click(
        fn=lambda: unload_handlers(),
        outputs=[model_status],
    )

    generate_btn.click(
        fn=generate_fn,
        inputs=[
            mode_selector,
            # Simple mode
            simple_query,
            simple_lang,
            # Custom mode
            caption_input,
            lyrics_input,
            instrumental_chk,
            vocal_lang,
            src_audio_input,
            repaint_start,
            repaint_end,
            cover_strength,
            bpm_input,
            duration_input,
            keyscale_input,
            time_sig_input,
            # Advanced
            inference_steps,
            guidance_scale,
            seed_input,
            batch_size,
            thinking_chk,
            lm_temp,
            audio_format,
        ],
        outputs=[status_output, audio_output],
    )

    refresh_files_btn.click(
        fn=refresh_files,
        outputs=[output_gallery],
    )

    clear_btn.click(
        fn=clear_outputs,
        outputs=[status_output, audio_output, output_gallery],
    )

    clear_files_btn.click(
        fn=clear_outputs,
        outputs=[status_output, audio_output, output_gallery],
    )

    return audio_output

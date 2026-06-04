"""
HyperRVC Theme CSS Editor – Custom theme management system.

Replaces the old pre-made theme system with a fully customizable CSS
theme editor.  Users can design their own visual identity by adjusting
colors, button styles, border radius, shadows, and more.  Themes are
saved as JSON and loaded at startup, so customisations persist across
sessions.

Features:
  - Color pickers for every major UI surface (background, text, accents)
  - Button style presets (flat, rounded, pill, material, outline)
  - Fine-grained control over border-radius, shadows, and transitions
  - Save / load / delete named themes
  - Live CSS generation that injects into Gradio's custom CSS
"""

from __future__ import annotations

import json
import os
import copy
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
NOW_DIR = os.getcwd()
THEMES_DIR = os.path.join(NOW_DIR, "assets", "themes", "saved")
CONFIG_FILE = os.path.join(NOW_DIR, "assets", "config.json")

# Ensure saved themes directory exists
os.makedirs(THEMES_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Default theme values (mirrors the original HyperRVC dark theme)
# ---------------------------------------------------------------------------
DEFAULT_THEME: dict = {
    "name": "HyperRVC Default",

    # ── Backgrounds ────────────────────────────────────────────
    "bg_primary": "#0D0B12",
    "bg_secondary": "#12101A",
    "bg_block": "#16131F",
    "bg_input": "#12101A",
    "bg_input_hover": "#1A1628",
    "bg_label": "#1E1B2E",
    "bg_title": "#1E1B2E",

    # ── Text ───────────────────────────────────────────────────
    "text_body": "#E8E6F0",
    "text_subdued": "#8B87A0",
    "text_placeholder": "#5B5775",
    "text_label": "#a5b4fc",
    "text_title": "#a5b4fc",

    # ── Primary accent ────────────────────────────────────────
    "primary_300": "#a5b4fc",
    "primary_400": "#818cf8",
    "primary_500": "#6366f1",
    "primary_600": "#4f46e5",

    # ── Secondary accent ──────────────────────────────────────
    "secondary_500": "#8b5cf6",
    "secondary_600": "#7c3aed",

    # ── Borders ───────────────────────────────────────────────
    "border_primary": "#1E1B2E",
    "border_accent": "#4f46e5",
    "border_input": "#2A2640",
    "border_input_hover": "#71717a",

    # ── Buttons ───────────────────────────────────────────────
    "btn_style": "rounded",            # flat | rounded | pill | material | outline
    "btn_primary_bg": "#4f46e5",
    "btn_primary_bg_hover": "#6366f1",
    "btn_primary_border": "#6366f1",
    "btn_primary_border_hover": "#818cf8",
    "btn_primary_text": "#ffffff",
    "btn_secondary_bg": "transparent",
    "btn_secondary_bg_hover": "#27272a",
    "btn_secondary_border": "#52525b",
    "btn_secondary_border_hover": "#71717a",
    "btn_secondary_text": "#E8E6F0",
    "btn_cancel_bg": "#27272a",
    "btn_cancel_bg_hover": "#3f3f46",
    "btn_cancel_border": "#52525b",
    "btn_cancel_text": "#E8E6F0",
    "btn_border_width": "1px",
    "btn_transition": "0.25s ease all",

    # ── Radius ────────────────────────────────────────────────
    "radius_sm": "4px",
    "radius_md": "8px",
    "radius_lg": "12px",
    "radius_xl": "16px",

    # ── Shadows ───────────────────────────────────────────────
    "shadow_block": "0 2px 8px rgba(0,0,0,0.3)",
    "shadow_input_focus": "0 0 0 2px rgba(99,102,241,0.25)",
    "shadow_drop": "rgba(0,0,0,0.15) 0px 1px 3px 0px",

    # ── Checkbox / Slider ─────────────────────────────────────
    "checkbox_bg": "#2A2640",
    "checkbox_bg_hover": "#332E4A",
    "checkbox_bg_selected": "#7c3aed",
    "checkbox_border": "#52525b",
    "slider_color": "#8B5CF6",

    # ── Table ─────────────────────────────────────────────────
    "table_even_bg": "#16131F",
    "table_odd_bg": "#12101A",
    "table_border": "#2A2640",

    # ── Error ─────────────────────────────────────────────────
    "error_bg": "#1C0F0F",
    "error_border": "#7F1D1D",
    "error_text": "#FCA5A5",
}

# ---------------------------------------------------------------------------
# Button style presets
# ---------------------------------------------------------------------------
BUTTON_PRESETS = {
    "flat": {
        "btn_style": "flat",
        "radius_sm": "0px",
        "radius_md": "0px",
        "radius_lg": "0px",
        "radius_xl": "0px",
        "btn_border_width": "0px",
        "shadow_block": "none",
        "shadow_input_focus": "0 0 0 1px rgba(99,102,241,0.5)",
        "shadow_drop": "none",
    },
    "rounded": {
        "btn_style": "rounded",
        "radius_sm": "4px",
        "radius_md": "8px",
        "radius_lg": "12px",
        "radius_xl": "16px",
        "btn_border_width": "1px",
        "shadow_block": "0 2px 8px rgba(0,0,0,0.3)",
        "shadow_input_focus": "0 0 0 2px rgba(99,102,241,0.25)",
        "shadow_drop": "rgba(0,0,0,0.15) 0px 1px 3px 0px",
    },
    "pill": {
        "btn_style": "pill",
        "radius_sm": "999px",
        "radius_md": "999px",
        "radius_lg": "999px",
        "radius_xl": "999px",
        "btn_border_width": "1px",
        "shadow_block": "0 2px 8px rgba(0,0,0,0.2)",
        "shadow_input_focus": "0 0 0 2px rgba(99,102,241,0.25)",
        "shadow_drop": "rgba(0,0,0,0.1) 0px 1px 2px 0px",
    },
    "material": {
        "btn_style": "material",
        "radius_sm": "4px",
        "radius_md": "8px",
        "radius_lg": "12px",
        "radius_xl": "16px",
        "btn_border_width": "0px",
        "shadow_block": "0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23)",
        "shadow_input_focus": "0 3px 6px rgba(99,102,241,0.3)",
        "shadow_drop": "0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)",
    },
    "outline": {
        "btn_style": "outline",
        "radius_sm": "4px",
        "radius_md": "8px",
        "radius_lg": "12px",
        "radius_xl": "16px",
        "btn_border_width": "2px",
        "shadow_block": "none",
        "shadow_input_focus": "0 0 0 1px rgba(99,102,241,0.5)",
        "shadow_drop": "none",
        "btn_primary_bg": "transparent",
        "btn_primary_bg_hover": "#4f46e5",
        "btn_primary_border": "#4f46e5",
        "btn_primary_text": "#a5b4fc",
        "btn_secondary_bg": "transparent",
        "btn_secondary_bg_hover": "transparent",
    },
}


# ---------------------------------------------------------------------------
# Helper: merge a preset into a theme dict (shallow-override)
# ---------------------------------------------------------------------------
def apply_button_preset(theme: dict, preset_name: str) -> dict:
    """Return a copy of *theme* with the chosen button preset merged in."""
    preset = BUTTON_PRESETS.get(preset_name)
    if preset is None:
        return theme
    merged = copy.deepcopy(theme)
    merged.update(preset)
    return merged


# ---------------------------------------------------------------------------
# CSS generation
# ---------------------------------------------------------------------------
def generate_css(theme: Optional[dict] = None) -> str:
    """Generate the complete CSS string from a theme dictionary.

    If *theme* is ``None`` the default theme is used.
    """
    t = theme or DEFAULT_THEME

    css = f"""
/* ═══════════════════════════════════════════════════════════
   HyperRVC Custom Theme – auto-generated by theme_editor.py
   Theme name: {t.get('name', 'Untitled')}
   ═══════════════════════════════════════════════════════════ */

:root {{
    --hyperrvc-bg-primary: {t['bg_primary']};
    --hyperrvc-bg-secondary: {t['bg_secondary']};
    --hyperrvc-bg-block: {t['bg_block']};
    --hyperrvc-bg-input: {t['bg_input']};
    --hyperrvc-bg-input-hover: {t['bg_input_hover']};
    --hyperrvc-bg-label: {t['bg_label']};
    --hyperrvc-bg-title: {t['bg_title']};

    --hyperrvc-text-body: {t['text_body']};
    --hyperrvc-text-subdued: {t['text_subdued']};
    --hyperrvc-text-placeholder: {t['text_placeholder']};
    --hyperrvc-text-label: {t['text_label']};
    --hyperrvc-text-title: {t['text_title']};

    --hyperrvc-primary-300: {t['primary_300']};
    --hyperrvc-primary-400: {t['primary_400']};
    --hyperrvc-primary-500: {t['primary_500']};
    --hyperrvc-primary-600: {t['primary_600']};

    --hyperrvc-secondary-500: {t['secondary_500']};
    --hyperrvc-secondary-600: {t['secondary_600']};

    --hyperrvc-border-primary: {t['border_primary']};
    --hyperrvc-border-accent: {t['border_accent']};
    --hyperrvc-border-input: {t['border_input']};
    --hyperrvc-border-input-hover: {t['border_input_hover']};

    --hyperrvc-btn-primary-bg: {t['btn_primary_bg']};
    --hyperrvc-btn-primary-bg-hover: {t['btn_primary_bg_hover']};
    --hyperrvc-btn-primary-border: {t['btn_primary_border']};
    --hyperrvc-btn-primary-border-hover: {t['btn_primary_border_hover']};
    --hyperrvc-btn-primary-text: {t['btn_primary_text']};

    --hyperrvc-btn-secondary-bg: {t['btn_secondary_bg']};
    --hyperrvc-btn-secondary-bg-hover: {t['btn_secondary_bg_hover']};
    --hyperrvc-btn-secondary-border: {t['btn_secondary_border']};
    --hyperrvc-btn-secondary-border-hover: {t['btn_secondary_border_hover']};
    --hyperrvc-btn-secondary-text: {t['btn_secondary_text']};

    --hyperrvc-btn-cancel-bg: {t['btn_cancel_bg']};
    --hyperrvc-btn-cancel-bg-hover: {t['btn_cancel_bg_hover']};
    --hyperrvc-btn-cancel-border: {t['btn_cancel_border']};
    --hyperrvc-btn-cancel-text: {t['btn_cancel_text']};

    --hyperrvc-radius-sm: {t['radius_sm']};
    --hyperrvc-radius-md: {t['radius_md']};
    --hyperrvc-radius-lg: {t['radius_lg']};
    --hyperrvc-radius-xl: {t['radius_xl']};

    --hyperrvc-shadow-block: {t['shadow_block']};
    --hyperrvc-shadow-input-focus: {t['shadow_input_focus']};
    --hyperrvc-shadow-drop: {t['shadow_drop']};

    --hyperrvc-checkbox-bg: {t['checkbox_bg']};
    --hyperrvc-checkbox-bg-hover: {t['checkbox_bg_hover']};
    --hyperrvc-checkbox-bg-selected: {t['checkbox_bg_selected']};
    --hyperrvc-checkbox-border: {t['checkbox_border']};
    --hyperrvc-slider-color: {t['slider_color']};

    --hyperrvc-table-even-bg: {t['table_even_bg']};
    --hyperrvc-table-odd-bg: {t['table_odd_bg']};
    --hyperrvc-table-border: {t['table_border']};

    --hyperrvc-error-bg: {t['error_bg']};
    --hyperrvc-error-border: {t['error_border']};
    --hyperrvc-error-text: {t['error_text']};

    --hyperrvc-btn-border-width: {t['btn_border_width']};
    --hyperrvc-btn-transition: {t['btn_transition']};
}}

/* ── Global background ─────────────────────────────────────── */
.gradio-container,
.prose,
.main,
.wrap,
footer {{
    background: var(--hyperrvc-bg-primary) !important;
    color: var(--hyperrvc-text-body) !important;
}}

body {{
    background: var(--hyperrvc-bg-primary) !important;
    color: var(--hyperrvc-text-body) !important;
}}

/* ── Blocks / panels ───────────────────────────────────────── */
.gr-box,
.gr-panel,
.gr-form,
.gr-accordion,
.gr-group,
.block {{
    background: var(--hyperrvc-bg-block) !important;
    border-color: var(--hyperrvc-border-primary) !important;
    border-radius: var(--hyperrvc-radius-lg) !important;
    box-shadow: var(--hyperrvc-shadow-block) !important;
}}

/* ── Labels & titles ───────────────────────────────────────── */
.gr-input-label,
.gr-radio-label,
.label-wrap label,
.gr-box > .label-wrap {{
    background: var(--hyperrvc-bg-label) !important;
    color: var(--hyperrvc-text-label) !important;
    border-radius: var(--hyperrvc-radius-lg) var(--hyperrvc-radius-lg) 0 0 !important;
}}

.gr-box > .label-wrap > span {{
    color: var(--hyperrvc-text-title) !important;
}}

/* ── Inputs ────────────────────────────────────────────────── */
input[type="text"],
input[type="number"],
input[type="password"],
textarea,
select,
.gr-input,
.gr-text-input,
.gr-number,
.gr-dropdown {{
    background: var(--hyperrvc-bg-input) !important;
    border-color: var(--hyperrvc-border-input) !important;
    color: var(--hyperrvc-text-body) !important;
    border-radius: var(--hyperrvc-radius-md) !important;
}}

input[type="text"]:hover,
input[type="number"]:hover,
textarea:hover,
select:hover,
.gr-input:hover,
.gr-text-input:hover,
.gr-number:hover,
.gr-dropdown:hover {{
    background: var(--hyperrvc-bg-input-hover) !important;
    border-color: var(--hyperrvc-border-input-hover) !important;
}}

input[type="text"]:focus,
input[type="number"]:focus,
textarea:focus,
select:focus,
.gr-input:focus,
.gr-text-input:focus,
.gr-number:focus,
.gr-dropdown:focus {{
    box-shadow: var(--hyperrvc-shadow-input-focus) !important;
    border-color: var(--hyperrvc-border-accent) !important;
    outline: none !important;
}}

::placeholder {{
    color: var(--hyperrvc-text-placeholder) !important;
}}

/* ── Primary buttons ───────────────────────────────────────── */
.gr-button.primary,
button.primary,
.btn-primary,
.gr-button[variant="primary"],
.gr-button[data-variant="primary"] {{
    background: var(--hyperrvc-btn-primary-bg) !important;
    border-color: var(--hyperrvc-btn-primary-border) !important;
    color: var(--hyperrvc-btn-primary-text) !important;
    border-width: var(--hyperrvc-btn-border-width) !important;
    border-radius: var(--hyperrvc-radius-lg) !important;
    transition: var(--hyperrvc-btn-transition) !important;
}}

.gr-button.primary:hover,
button.primary:hover,
.btn-primary:hover {{
    background: var(--hyperrvc-btn-primary-bg-hover) !important;
    border-color: var(--hyperrvc-btn-primary-border-hover) !important;
    color: var(--hyperrvc-btn-primary-text) !important;
}}

/* ── Secondary buttons ─────────────────────────────────────── */
.gr-button.secondary,
button.secondary,
.btn-secondary,
.gr-button[variant="secondary"],
.gr-button[data-variant="secondary"] {{
    background: var(--hyperrvc-btn-secondary-bg) !important;
    border-color: var(--hyperrvc-btn-secondary-border) !important;
    color: var(--hyperrvc-btn-secondary-text) !important;
    border-width: var(--hyperrvc-btn-border-width) !important;
    border-radius: var(--hyperrvc-radius-lg) !important;
    transition: var(--hyperrvc-btn-transition) !important;
}}

.gr-button.secondary:hover,
button.secondary:hover,
.btn-secondary:hover {{
    background: var(--hyperrvc-btn-secondary-bg-hover) !important;
    border-color: var(--hyperrvc-btn-secondary-border-hover) !important;
}}

/* ── Stop / cancel buttons ─────────────────────────────────── */
.gr-button.stop,
button.stop,
.btn-cancel,
.gr-button[variant="stop"],
.gr-button[data-variant="stop"] {{
    background: var(--hyperrvc-btn-cancel-bg) !important;
    border-color: var(--hyperrvc-btn-cancel-border) !important;
    color: var(--hyperrvc-btn-cancel-text) !important;
    border-width: var(--hyperrvc-btn-border-width) !important;
    border-radius: var(--hyperrvc-radius-lg) !important;
    transition: var(--hyperrvc-btn-transition) !important;
}}

.gr-button.stop:hover,
button.stop:hover,
.btn-cancel:hover {{
    background: var(--hyperrvc-btn-cancel-bg-hover) !important;
}}

/* ── All generic buttons catch-all ─────────────────────────── */
.gr-button,
button {{
    border-radius: var(--hyperrvc-radius-lg) !important;
    transition: var(--hyperrvc-btn-transition) !important;
}}

/* ── Checkboxes ────────────────────────────────────────────── */
.gr-checkbox input[type="checkbox"],
input[type="checkbox"] {{
    background: var(--hyperrvc-checkbox-bg) !important;
    border-color: var(--hyperrvc-checkbox-border) !important;
    border-radius: var(--hyperrvc-radius-sm) !important;
}}

.gr-checkbox input[type="checkbox"]:checked,
input[type="checkbox"]:checked {{
    background: var(--hyperrvc-checkbox-bg-selected) !important;
    border-color: var(--hyperrvc-checkbox-bg-selected) !important;
}}

/* ── Sliders ───────────────────────────────────────────────── */
input[type="range"] {{
    accent-color: var(--hyperrvc-slider-color) !important;
}}

.gr-slider .handle {{
    background: var(--hyperrvc-slider-color) !important;
}}

/* ── Tables ────────────────────────────────────────────────── */
table tr:nth-child(even) td {{
    background: var(--hyperrvc-table-even-bg) !important;
}}

table tr:nth-child(odd) td {{
    background: var(--hyperrvc-table-odd-bg) !important;
}}

table th,
table td {{
    border-color: var(--hyperrvc-table-border) !important;
}}

/* ── Error states ──────────────────────────────────────────── */
.gr-error,
.error {{
    background: var(--hyperrvc-error-bg) !important;
    border-color: var(--hyperrvc-error-border) !important;
    color: var(--hyperrvc-error-text) !important;
}}

/* ── Tabs ──────────────────────────────────────────────────── */
.gr-tabs .tab-nav button {{
    border-radius: var(--hyperrvc-radius-md) var(--hyperrvc-radius-md) 0 0 !important;
    color: var(--hyperrvc-text-subdued) !important;
}}

.gr-tabs .tab-nav button.selected {{
    color: var(--hyperrvc-text-body) !important;
    border-bottom-color: var(--hyperrvc-border-accent) !important;
}}

/* ── Accordions ────────────────────────────────────────────── */
.gr-accordion .label-wrap {{
    border-radius: var(--hyperrvc-radius-lg) !important;
}}

/* ── Audio player ──────────────────────────────────────────── */
.audio-container {{
    border-radius: var(--hyperrvc-radius-lg) !important;
}}

/* ── Subdued text ──────────────────────────────────────────── */
.text-subdued,
.gr-info {{
    color: var(--hyperrvc-text-subdued) !important;
}}

/* ── Links ─────────────────────────────────────────────────── */
a {{
    color: var(--hyperrvc-primary-400) !important;
}}

a:hover {{
    color: var(--hyperrvc-primary-300) !important;
}}

/* ── Footer ────────────────────────────────────────────────── */
footer {{
    display: none !important;
}}

/* ── Scrollbar (webkit) ────────────────────────────────────── */
::-webkit-scrollbar {{
    width: 8px;
    height: 8px;
}}

::-webkit-scrollbar-track {{
    background: var(--hyperrvc-bg-primary) !important;
}}

::-webkit-scrollbar-thumb {{
    background: var(--hyperrvc-border-input) !important;
    border-radius: var(--hyperrvc-radius-sm) !important;
}}

::-webkit-scrollbar-thumb:hover {{
    background: var(--hyperrvc-border-input-hover) !important;
}}
"""
    return css


# ---------------------------------------------------------------------------
# Save / Load / Delete
# ---------------------------------------------------------------------------
def save_theme(theme: dict, name: Optional[str] = None) -> str:
    """Save a theme dict to a JSON file.  Returns a status message."""
    if name:
        theme["name"] = name
    theme_name = theme.get("name", "Untitled").strip()
    if not theme_name:
        return "Error: Theme name cannot be empty."

    # Sanitise filename
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in theme_name)
    filepath = os.path.join(THEMES_DIR, f"{safe_name}.json")

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(theme, f, indent=2, ensure_ascii=False)
        return f"Theme '{theme_name}' saved successfully."
    except Exception as e:
        return f"Error saving theme: {e}"


def load_theme(name: str) -> dict:
    """Load a theme dict from a JSON file.  Returns DEFAULT_THEME on error."""
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name)
    filepath = os.path.join(THEMES_DIR, f"{safe_name}.json")

    if not os.path.exists(filepath):
        return copy.deepcopy(DEFAULT_THEME)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            saved = json.load(f)
        # Merge with defaults so new keys are always present
        merged = copy.deepcopy(DEFAULT_THEME)
        merged.update(saved)
        return merged
    except Exception:
        return copy.deepcopy(DEFAULT_THEME)


def delete_theme(name: str) -> str:
    """Delete a saved theme.  Returns a status message."""
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name)
    filepath = os.path.join(THEMES_DIR, f"{safe_name}.json")

    if not os.path.exists(filepath):
        return f"Theme '{name}' not found."

    try:
        os.remove(filepath)
        return f"Theme '{name}' deleted."
    except Exception as e:
        return f"Error deleting theme: {e}"


def list_saved_themes() -> list[str]:
    """Return a sorted list of saved theme names."""
    themes = []
    for f in sorted(Path(THEMES_DIR).glob("*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                themes.append(data.get("name", f.stem))
        except Exception:
            themes.append(f.stem)
    return themes


# ---------------------------------------------------------------------------
# Active theme persistence in config.json
# ---------------------------------------------------------------------------
def get_active_theme() -> dict:
    """Read config.json and return the active theme (merged with defaults)."""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        theme_section = config.get("custom_theme", {})
        if theme_section:
            merged = copy.deepcopy(DEFAULT_THEME)
            merged.update(theme_section)
            return merged
    except Exception:
        pass
    return copy.deepcopy(DEFAULT_THEME)


def set_active_theme(theme: dict) -> str:
    """Write the active theme into config.json so it loads on next start."""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        config = {}

    config["custom_theme"] = theme

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return f"Theme '{theme.get('name', 'Untitled')}' applied. Restart to see full effect."
    except Exception as e:
        return f"Error applying theme: {e}"


def get_active_theme_name() -> str:
    """Return the name of the currently active theme, or 'HyperRVC Default'."""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("custom_theme", {}).get("name", "HyperRVC Default")
    except Exception:
        return "HyperRVC Default"

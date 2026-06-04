"""
Settings tab for Hyper-RVC WebUI.

UI-only settings: theme CSS editor, language, about, restart.

The old pre-made theme dropdown has been replaced with a full CSS theme
editor that lets users customise colors, button styles, border-radius,
and more.  Themes can be saved to / loaded from JSON files.
"""

import gradio as gr
import os
import sys
import json
import copy
from pathlib import Path

from assets.i18n.i18n import I18nAuto
import assets.themes.theme_editor as te

i18n = I18nAuto()

now_dir = os.getcwd()
sys.path.append(now_dir)

CONFIG_PATH = os.path.join(now_dir, "assets", "config.json")
LANGUAGE_PATH = os.path.join(now_dir, "assets", "i18n", "languages")


# ---------------------------------------------------------------------------
# Language helpers (unchanged)
# ---------------------------------------------------------------------------
def get_available_languages():
    """Get list of available language files."""
    language_files = list(Path(LANGUAGE_PATH).glob("*.json"))
    language_names = {
        "en_US": "English (US)",
        "pt_BR": "Portugues (Brasil)",
        "es_ES": "Espanol",
        "fr_FR": "Francais",
        "de_DE": "Deutsch",
        "ja_JP": "Japanese",
        "ko_KR": "Korean",
        "zh_CN": "Simplified Chinese",
        "zh_TW": "Traditional Chinese",
        "it_IT": "Italiano",
        "ru_RU": "Russian",
        "uk_UA": "Ukrainian",
        "hi_IN": "Hindi",
        "ar_SA": "Arabic",
        "tr_TR": "Turkce",
        "pl_PL": "Polski",
        "nl_NL": "Nederlands",
        "sv_SE": "Svenska",
        "cs_CZ": "Cestina",
        "ro_RO": "Romana",
        "id_ID": "Bahasa Indonesia",
        "vi_VN": "Tieng Viet",
        "th_TH": "Thai",
        "da_DK": "Dansk",
        "fi_FI": "Suomi",
        "el_GR": "Hellenic",
        "he_IL": "Hebrew",
        "hu_HU": "Magyar",
        "no_NO": "Norsk",
        "sk_SK": "Slovenscina",
        "ca_ES": "Catala",
        "bg_BG": "Bulgarian",
        "hr_HR": "Hrvatski",
        "sr_RS": "Srpski",
        "sl_SI": "Slovenscina",
        "et_EE": "Eesti",
        "lv_LV": "Latvian",
        "lt_LT": "Lietuviv",
        "ms_MY": "Bahasa Melayu",
        "fil_PH": "Filipino",
        "af_ZA": "Afrikaans",
        "bn_BD": "Bengali",
        "ta_IN": "Tamil",
        "te_IN": "Telugu",
        "ml_IN": "Malayalam",
        "mr_IN": "Marathi",
        "pa_IN": "Punjabi",
        "gu_IN": "Gujarati",
        "kn_IN": "Kannada",
        "ur_PK": "Urdu",
        "fa_IR": "Farsi",
        "sw_KE": "Kiswahili",
        "eu_ES": "Euskara",
        "gl_ES": "Galego",
        "is_IS": "Islenska",
        "en_GB": "English (UK)",
        "en_AU": "English (Australia)",
        "en_CA": "English (Canada)",
        "en_IN": "English (India)",
        "es_MX": "Espanol (Mexico)",
        "es_AR": "Espanol (Argentina)",
        "es_CO": "Espanol (Colombia)",
        "fr_CA": "Francais (Canada)",
        "fr_BE": "Francais (Belgique)",
        "de_AT": "Deutsch (Osterreich)",
        "de_CH": "Deutsch (Schweiz)",
        "it_CH": "Italiano (Svizzera)",
        "zh_HK": "Hong Kong Traditional Chinese",
        "ar_EG": "Arabic (Egypt)",
        "ar_MA": "Arabic (Morocco)",
        "pt_PT": "Portugues (Portugal)",
        "ms_SG": "Bahasa Melayu (Singapore)",
        "nl_BE": "Nederlands (Belgie)",
        "sv_FI": "Svenska (Finland)",
        "ru_KZ": "Russian (Kazakhstan)",
        "pa_PK": "Punjabi (Pakistan)",
        "sw_TZ": "Kiswahili (Tanzania)",
        "sq_AL": "Shqip (Albanian)",
        "be_BY": "Belaruskaya (Belarusian)",
        "bs_BA": "Bosanski (Bosnian)",
        "cy_GB": "Cymraeg (Welsh)",
        "fo_FO": "Føroyskt (Faroese)",
        "ga_IE": "Gaeilge (Irish)",
        "gd_GB": "Gaidhlig (Scottish Gaelic)",
        "lb_LU": "Letzebuergesch (Luxembourgish)",
        "nn_NO": "Norsk Nynorsk",
        "oc_FR": "Occitan",
        "sc_IT": "Sardu (Sardinian)",
        "am_ET": "Amharic",
        "as_IN": "Assamese",
        "az_AZ": "Azerbaijani",
        "bo_CN": "Bod skad (Tibetan)",
        "br_FR": "Brezhoneg (Breton)",
        "ha_NG": "Hausa",
        "haw_US": "Olelo Hawaii (Hawaiian)",
        "hy_AM": "Hayeren (Armenian)",
        "ig_NG": "Igbo",
        "ka_GE": "Kartuli (Georgian)",
        "kk_KZ": "Kazakh",
        "ku_TR": "Kurdish",
        "ky_KG": "Kyrgyz",
        "km_KH": "Khmer",
        "lg_UG": "Luganda",
        "ln_CD": "Lingala",
        "lo_LA": "Lao",
        "mg_MG": "Malagasy",
        "mi_NZ": "Te Reo Maori",
        "mk_MK": "Makedonski (Macedonian)",
        "mn_MN": "Mongolian",
        "mt_MT": "Malti (Maltese)",
        "my_MM": "Myanmar (Burmese)",
        "ne_NP": "Nepali",
        "or_IN": "Odia",
        "ps_AF": "Pashto",
        "sd_PK": "Sindhi",
        "si_LK": "Sinhala",
        "su_ID": "Basa Sunda (Sundanese)",
        "tg_TJ": "Tojiki (Tajik)",
        "tk_TM": "Turkmen",
        "tl_PH": "Tagalog",
        "tt_RU": "Tatar",
        "ug_CN": "Uyghur",
        "uz_UZ": "Uzbek",
        "bm_ML": "Bamanankan (Bambara)",
        "ee_GH": "Ewegbe (Ewe)",
        "qu_PE": "Runasimi (Quechua)",
        "rn_BI": "Ikirundi (Rundi)",
        "rw_RW": "Ikinyarwanda",
        "sa_IN": "Samskritam (Sanskrit)",
        "so_SO": "Soomaali (Somali)",
        "wo_SN": "Wolof",
        "xh_ZA": "isiXhosa (Xhosa)",
        "yi_US": "Yiddish",
        "yo_NG": "Yoruba",
        "zu_ZA": "isiZulu (Zulu)",
        "eo_XX": "Esperanto",
        "jv_ID": "Basa Jawa (Javanese)",
        "co_FR": "Corsu (Corsican)",
        "fy_NL": "Frysk (Western Frisian)",
        "li_NL": "Limburgs (Limburgish)",
        "nd_ZA": "isiNdebele (Northern Ndebele)",
        "ss_SZ": "SiSwati (Swati)",
        "ts_ZA": "Xitsonga (Tsonga)",
        "ve_ZA": "Tshivenda (Venda)",
        "ia_FR": "Interlingua",
    }

    languages = []
    for lang_file in language_files:
        lang_code = lang_file.stem
        lang_name = language_names.get(lang_code, lang_code)
        languages.append((lang_name, lang_code))
    return sorted(languages, key=lambda x: x[0])


def _read_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_current_language():
    return _read_config().get("lang", {}).get("selected_lang", "en_US")


def save_language_selection(language):
    try:
        config = _read_config()
        config.setdefault("lang", {})
        config["lang"]["selected_lang"] = language
        config["lang"]["override"] = True
        _write_config(config)
        return "Language changed. Restart the app to apply."
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Theme editor callback helpers
# ---------------------------------------------------------------------------

def _build_theme_dict(
    # backgrounds
    bg_primary, bg_secondary, bg_block, bg_input, bg_input_hover,
    bg_label, bg_title,
    # text
    text_body, text_subdued, text_placeholder, text_label, text_title,
    # primary accent
    primary_300, primary_400, primary_500, primary_600,
    # secondary accent
    secondary_500, secondary_600,
    # borders
    border_primary, border_accent, border_input, border_input_hover,
    # button style
    btn_style,
    # primary button
    btn_primary_bg, btn_primary_bg_hover, btn_primary_border,
    btn_primary_border_hover, btn_primary_text,
    # secondary button
    btn_secondary_bg, btn_secondary_bg_hover, btn_secondary_border,
    btn_secondary_border_hover, btn_secondary_text,
    # cancel button
    btn_cancel_bg, btn_cancel_bg_hover, btn_cancel_border, btn_cancel_text,
    # radius
    radius_sm, radius_md, radius_lg, radius_xl,
    # shadows
    shadow_block, shadow_input_focus, shadow_drop,
    # checkbox / slider
    checkbox_bg, checkbox_bg_hover, checkbox_bg_selected,
    checkbox_border, slider_color,
    # table
    table_even_bg, table_odd_bg, table_border,
    # error
    error_bg, error_border, error_text,
    # name
    theme_name,
) -> dict:
    """Pack all widget values back into a theme dictionary."""
    return {
        "name": theme_name,
        "bg_primary": bg_primary,
        "bg_secondary": bg_secondary,
        "bg_block": bg_block,
        "bg_input": bg_input,
        "bg_input_hover": bg_input_hover,
        "bg_label": bg_label,
        "bg_title": bg_title,
        "text_body": text_body,
        "text_subdued": text_subdued,
        "text_placeholder": text_placeholder,
        "text_label": text_label,
        "text_title": text_title,
        "primary_300": primary_300,
        "primary_400": primary_400,
        "primary_500": primary_500,
        "primary_600": primary_600,
        "secondary_500": secondary_500,
        "secondary_600": secondary_600,
        "border_primary": border_primary,
        "border_accent": border_accent,
        "border_input": border_input,
        "border_input_hover": border_input_hover,
        "btn_style": btn_style,
        "btn_primary_bg": btn_primary_bg,
        "btn_primary_bg_hover": btn_primary_bg_hover,
        "btn_primary_border": btn_primary_border,
        "btn_primary_border_hover": btn_primary_border_hover,
        "btn_primary_text": btn_primary_text,
        "btn_secondary_bg": btn_secondary_bg,
        "btn_secondary_bg_hover": btn_secondary_bg_hover,
        "btn_secondary_border": btn_secondary_border,
        "btn_secondary_border_hover": btn_secondary_border_hover,
        "btn_secondary_text": btn_secondary_text,
        "btn_cancel_bg": btn_cancel_bg,
        "btn_cancel_bg_hover": btn_cancel_bg_hover,
        "btn_cancel_border": btn_cancel_border,
        "btn_cancel_text": btn_cancel_text,
        "radius_sm": radius_sm,
        "radius_md": radius_md,
        "radius_lg": radius_lg,
        "radius_xl": radius_xl,
        "shadow_block": shadow_block,
        "shadow_input_focus": shadow_input_focus,
        "shadow_drop": shadow_drop,
        "checkbox_bg": checkbox_bg,
        "checkbox_bg_hover": checkbox_bg_hover,
        "checkbox_bg_selected": checkbox_bg_selected,
        "checkbox_border": checkbox_border,
        "slider_color": slider_color,
        "table_even_bg": table_even_bg,
        "table_odd_bg": table_odd_bg,
        "table_border": table_border,
        "error_bg": error_bg,
        "error_border": error_border,
        "error_text": error_text,
    }


def _apply_preset_callback(preset_name):
    """Return a list of values for all widgets based on a button preset."""
    merged = te.apply_button_preset(te.get_active_theme(), preset_name)
    return _theme_to_widget_values(merged)


def _theme_to_widget_values(t: dict) -> list:
    """Convert a theme dict into the flat list expected by Gradio outputs."""
    d = te.DEFAULT_THEME
    keys = [
        "bg_primary", "bg_secondary", "bg_block", "bg_input", "bg_input_hover",
        "bg_label", "bg_title",
        "text_body", "text_subdued", "text_placeholder", "text_label", "text_title",
        "primary_300", "primary_400", "primary_500", "primary_600",
        "secondary_500", "secondary_600",
        "border_primary", "border_accent", "border_input", "border_input_hover",
        "btn_style",
        "btn_primary_bg", "btn_primary_bg_hover", "btn_primary_border",
        "btn_primary_border_hover", "btn_primary_text",
        "btn_secondary_bg", "btn_secondary_bg_hover", "btn_secondary_border",
        "btn_secondary_border_hover", "btn_secondary_text",
        "btn_cancel_bg", "btn_cancel_bg_hover", "btn_cancel_border", "btn_cancel_text",
        "radius_sm", "radius_md", "radius_lg", "radius_xl",
        "shadow_block", "shadow_input_focus", "shadow_drop",
        "checkbox_bg", "checkbox_bg_hover", "checkbox_bg_selected",
        "checkbox_border", "slider_color",
        "table_even_bg", "table_odd_bg", "table_border",
        "error_bg", "error_border", "error_text",
        "name",
    ]
    return [t.get(k, d[k]) for k in keys]


# Callback: apply button preset
def on_preset_change(preset_name):
    return _apply_preset_callback(preset_name)


# Callback: save current theme
def on_save_theme(theme_name, *values):
    theme = _build_theme_dict(*values, theme_name=theme_name)
    return te.save_theme(theme, theme_name)


# Callback: load a saved theme
def on_load_theme(theme_name):
    theme = te.load_theme(theme_name)
    return _theme_to_widget_values(theme)


# Callback: delete a saved theme
def on_delete_theme(theme_name):
    return te.delete_theme(theme_name)


# Callback: apply (activate) current theme
def on_apply_theme(theme_name, *values):
    theme = _build_theme_dict(*values, theme_name=theme_name)
    return te.set_active_theme(theme)


# Callback: reset to defaults
def on_reset_theme():
    return _theme_to_widget_values(te.DEFAULT_THEME)


# Callback: refresh the list of saved themes
def on_refresh_themes():
    return gr.update(choices=te.list_saved_themes())


def reset_to_defaults():
    try:
        _write_config({
            "theme": {"file": None, "class": "HyperRVC"},
            "lang": {"override": False, "selected_lang": "en_US"},
        })
        return "Settings reset. Restart the app to apply."
    except Exception as e:
        return f"Error: {e}"


def restart_app():
    return "Please restart the application to apply changes."


def select_themes_tab():
    """Create the settings tab UI -- theme editor, language, about."""

    current_lang = get_current_language()
    active_theme = te.get_active_theme()

    with gr.Tabs():
        # ── Theme CSS Editor ──────────────────────────────────
        with gr.TabItem("Theme Editor"):
            gr.Markdown(
                """
                ### Custom Theme Editor
                Design your own visual theme by adjusting colors, button styles, and more.
                Changes are applied after clicking **Apply Theme** and restarting the app.
                """
            )

            # ── Load / Save bar ──
            with gr.Row():
                saved_themes = gr.Dropdown(
                    choices=te.list_saved_themes(),
                    label="Load Saved Theme",
                    scale=3,
                )
                load_btn = gr.Button("Load", variant="secondary", scale=1)
                delete_btn = gr.Button("Delete", variant="stop", scale=1)
                refresh_btn = gr.Button("Refresh List", variant="secondary", scale=1)

            # ── Button style presets ──
            with gr.Row():
                preset_dropdown = gr.Dropdown(
                    choices=["flat", "rounded", "pill", "material", "outline"],
                    value=active_theme.get("btn_style", "rounded"),
                    label="Button Style Preset",
                    scale=3,
                )
                apply_preset_btn = gr.Button("Apply Preset", variant="primary", scale=1)

            # ── Background colors ──
            with gr.Accordion("Background Colors", open=True):
                bg_primary = gr.ColorPicker(value=active_theme["bg_primary"], label="Primary Background")
                bg_secondary = gr.ColorPicker(value=active_theme["bg_secondary"], label="Secondary Background")
                bg_block = gr.ColorPicker(value=active_theme["bg_block"], label="Block Background")
                bg_input = gr.ColorPicker(value=active_theme["bg_input"], label="Input Background")
                bg_input_hover = gr.ColorPicker(value=active_theme["bg_input_hover"], label="Input Background (Hover)")
                bg_label = gr.ColorPicker(value=active_theme["bg_label"], label="Label Background")
                bg_title = gr.ColorPicker(value=active_theme["bg_title"], label="Title Background")

            # ── Text colors ──
            with gr.Accordion("Text Colors", open=True):
                text_body = gr.ColorPicker(value=active_theme["text_body"], label="Body Text")
                text_subdued = gr.ColorPicker(value=active_theme["text_subdued"], label="Subdued Text")
                text_placeholder = gr.ColorPicker(value=active_theme["text_placeholder"], label="Placeholder Text")
                text_label = gr.ColorPicker(value=active_theme["text_label"], label="Label Text")
                text_title = gr.ColorPicker(value=active_theme["text_title"], label="Title Text")

            # ── Primary accent ──
            with gr.Accordion("Primary Accent", open=False):
                primary_300 = gr.ColorPicker(value=active_theme["primary_300"], label="Primary 300")
                primary_400 = gr.ColorPicker(value=active_theme["primary_400"], label="Primary 400")
                primary_500 = gr.ColorPicker(value=active_theme["primary_500"], label="Primary 500")
                primary_600 = gr.ColorPicker(value=active_theme["primary_600"], label="Primary 600")

            # ── Secondary accent ──
            with gr.Accordion("Secondary Accent", open=False):
                secondary_500 = gr.ColorPicker(value=active_theme["secondary_500"], label="Secondary 500")
                secondary_600 = gr.ColorPicker(value=active_theme["secondary_600"], label="Secondary 600")

            # ── Borders ──
            with gr.Accordion("Borders", open=False):
                border_primary = gr.ColorPicker(value=active_theme["border_primary"], label="Primary Border")
                border_accent = gr.ColorPicker(value=active_theme["border_accent"], label="Accent Border")
                border_input = gr.ColorPicker(value=active_theme["border_input"], label="Input Border")
                border_input_hover = gr.ColorPicker(value=active_theme["border_input_hover"], label="Input Border (Hover)")

            # ── Button colors ──
            with gr.Accordion("Button Colors", open=True):
                with gr.Group():
                    gr.Markdown("**Primary Button**")
                    with gr.Row():
                        btn_primary_bg = gr.ColorPicker(value=active_theme["btn_primary_bg"], label="Background")
                        btn_primary_bg_hover = gr.ColorPicker(value=active_theme["btn_primary_bg_hover"], label="Background (Hover)")
                    with gr.Row():
                        btn_primary_border = gr.ColorPicker(value=active_theme["btn_primary_border"], label="Border")
                        btn_primary_border_hover = gr.ColorPicker(value=active_theme["btn_primary_border_hover"], label="Border (Hover)")
                    btn_primary_text = gr.ColorPicker(value=active_theme["btn_primary_text"], label="Text Color")

                with gr.Group():
                    gr.Markdown("**Secondary Button**")
                    with gr.Row():
                        btn_secondary_bg = gr.ColorPicker(value=active_theme["btn_secondary_bg"], label="Background")
                        btn_secondary_bg_hover = gr.ColorPicker(value=active_theme["btn_secondary_bg_hover"], label="Background (Hover)")
                    with gr.Row():
                        btn_secondary_border = gr.ColorPicker(value=active_theme["btn_secondary_border"], label="Border")
                        btn_secondary_border_hover = gr.ColorPicker(value=active_theme["btn_secondary_border_hover"], label="Border (Hover)")
                    btn_secondary_text = gr.ColorPicker(value=active_theme["btn_secondary_text"], label="Text Color")

                with gr.Group():
                    gr.Markdown("**Cancel / Stop Button**")
                    with gr.Row():
                        btn_cancel_bg = gr.ColorPicker(value=active_theme["btn_cancel_bg"], label="Background")
                        btn_cancel_bg_hover = gr.ColorPicker(value=active_theme["btn_cancel_bg_hover"], label="Background (Hover)")
                    btn_cancel_border = gr.ColorPicker(value=active_theme["btn_cancel_border"], label="Border")
                    btn_cancel_text = gr.ColorPicker(value=active_theme["btn_cancel_text"], label="Text Color")

            # ── Border Radius ──
            with gr.Accordion("Border Radius", open=False):
                radius_sm = gr.Textbox(value=active_theme["radius_sm"], label="Small Radius (e.g. 4px)")
                radius_md = gr.Textbox(value=active_theme["radius_md"], label="Medium Radius (e.g. 8px)")
                radius_lg = gr.Textbox(value=active_theme["radius_lg"], label="Large Radius (e.g. 12px)")
                radius_xl = gr.Textbox(value=active_theme["radius_xl"], label="Extra-Large Radius (e.g. 16px)")

            # ── Shadows ──
            with gr.Accordion("Shadows", open=False):
                shadow_block = gr.Textbox(value=active_theme["shadow_block"], label="Block Shadow")
                shadow_input_focus = gr.Textbox(value=active_theme["shadow_input_focus"], label="Input Focus Shadow")
                shadow_drop = gr.Textbox(value=active_theme["shadow_drop"], label="Drop Shadow")

            # ── Checkbox / Slider ──
            with gr.Accordion("Checkbox & Slider", open=False):
                checkbox_bg = gr.ColorPicker(value=active_theme["checkbox_bg"], label="Checkbox Background")
                checkbox_bg_hover = gr.ColorPicker(value=active_theme["checkbox_bg_hover"], label="Checkbox Background (Hover)")
                checkbox_bg_selected = gr.ColorPicker(value=active_theme["checkbox_bg_selected"], label="Checkbox Background (Selected)")
                checkbox_border = gr.ColorPicker(value=active_theme["checkbox_border"], label="Checkbox Border")
                slider_color = gr.ColorPicker(value=active_theme["slider_color"], label="Slider Color")

            # ── Table ──
            with gr.Accordion("Table", open=False):
                table_even_bg = gr.ColorPicker(value=active_theme["table_even_bg"], label="Even Row Background")
                table_odd_bg = gr.ColorPicker(value=active_theme["table_odd_bg"], label="Odd Row Background")
                table_border = gr.ColorPicker(value=active_theme["table_border"], label="Table Border")

            # ── Error ──
            with gr.Accordion("Error States", open=False):
                error_bg = gr.ColorPicker(value=active_theme["error_bg"], label="Error Background")
                error_border = gr.ColorPicker(value=active_theme["error_border"], label="Error Border")
                error_text = gr.ColorPicker(value=active_theme["error_text"], label="Error Text")

            # ── Theme name & action buttons ──
            gr.Markdown("### Save & Apply")
            with gr.Row():
                theme_name_input = gr.Textbox(
                    value=active_theme.get("name", "My Custom Theme"),
                    label="Theme Name",
                    scale=3,
                )

            with gr.Row():
                apply_btn = gr.Button("Apply Theme", variant="primary", size="lg")
                save_btn = gr.Button("Save Theme", variant="secondary", size="lg")
                reset_btn = gr.Button("Reset to Default", variant="stop", size="lg")

            status_box = gr.Textbox(label="Status", interactive=False)

            # Collect all editable widgets for batch updates
            _all_widgets = [
                bg_primary, bg_secondary, bg_block, bg_input, bg_input_hover,
                bg_label, bg_title,
                text_body, text_subdued, text_placeholder, text_label, text_title,
                primary_300, primary_400, primary_500, primary_600,
                secondary_500, secondary_600,
                border_primary, border_accent, border_input, border_input_hover,
                preset_dropdown,
                btn_primary_bg, btn_primary_bg_hover, btn_primary_border,
                btn_primary_border_hover, btn_primary_text,
                btn_secondary_bg, btn_secondary_bg_hover, btn_secondary_border,
                btn_secondary_border_hover, btn_secondary_text,
                btn_cancel_bg, btn_cancel_bg_hover, btn_cancel_border, btn_cancel_text,
                radius_sm, radius_md, radius_lg, radius_xl,
                shadow_block, shadow_input_focus, shadow_drop,
                checkbox_bg, checkbox_bg_hover, checkbox_bg_selected,
                checkbox_border, slider_color,
                table_even_bg, table_odd_bg, table_border,
                error_bg, error_border, error_text,
            ]

            # ── Wire callbacks ─────────────────────────────────

            # Apply button preset
            apply_preset_btn.click(
                fn=on_preset_change,
                inputs=[preset_dropdown],
                outputs=_all_widgets + [theme_name_input],
            )

            # Save theme
            save_btn.click(
                fn=on_save_theme,
                inputs=[theme_name_input] + _all_widgets,
                outputs=[status_box],
            ).then(
                fn=on_refresh_themes,
                inputs=[],
                outputs=[saved_themes],
            )

            # Load saved theme
            load_btn.click(
                fn=on_load_theme,
                inputs=[saved_themes],
                outputs=_all_widgets + [theme_name_input],
            )

            # Delete saved theme
            delete_btn.click(
                fn=on_delete_theme,
                inputs=[saved_themes],
                outputs=[status_box],
            ).then(
                fn=on_refresh_themes,
                inputs=[],
                outputs=[saved_themes],
            )

            # Refresh theme list
            refresh_btn.click(
                fn=on_refresh_themes,
                inputs=[],
                outputs=[saved_themes],
            )

            # Apply (activate) theme
            apply_btn.click(
                fn=on_apply_theme,
                inputs=[theme_name_input] + _all_widgets,
                outputs=[status_box],
            )

            # Reset to defaults
            reset_btn.click(
                fn=on_reset_theme,
                inputs=[],
                outputs=_all_widgets + [theme_name_input],
            )

        # ── Language ───────────────────────────────────────────
        with gr.TabItem(i18n("Language")):
            gr.Markdown("### Language")
            language_select = gr.Dropdown(
                choices=get_available_languages(),
                value=current_lang,
                label=i18n("Language"),
                info=i18n("Select your preferred language. Requires restart."),
                interactive=True,
            )
            language_status = gr.Textbox(label=i18n("Status"), interactive=False, visible=True)
            language_select.change(
                fn=save_language_selection,
                inputs=[language_select],
                outputs=[language_status],
            )

        # ── About ──────────────────────────────────────────────
        with gr.TabItem(i18n("About")):
            gr.HTML("""
            <div style="text-align:center; padding: 20px 0 10px 0;">
                <h1 style="margin:0; font-size:2.2em; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Hyper-RVC WebUI</h1>
                <p style="margin:4px 0 0 0; color:#888; font-size:0.95em;">Version 1.0.0 -- Modular Architecture</p>
            </div>
            <p style="text-align:center; color:#aaa; max-width:650px; margin:0 auto 16px auto;">
                An autonomous pipeline to create covers with any RVC v2 trained AI voice
                from YouTube videos or a local audio file.
            </p>
            <div style="display:flex; gap:10px; justify-content:center; flex-wrap:wrap; margin-bottom:18px;">
                <a href="https://github.com/BF667-IDLE/Hyper-RVC" target="_blank" style="text-decoration:none; padding:6px 16px; border-radius:8px; background:#24292e; color:#fff; font-size:0.85em;">GitHub</a>
                <a href="https://colab.research.google.com/github/BF667-IDLE/Hyper-RVC/blob/main/assets/colab.ipynb" target="_blank" style="text-decoration:none; padding:6px 16px; border-radius:8px; background:#f9a825; color:#000; font-size:0.85em;">Colab</a>
                <a href="https://github.com/BF667-IDLE/Hyper-RVC/issues" target="_blank" style="text-decoration:none; padding:6px 16px; border-radius:8px; background:#e74c3c; color:#fff; font-size:0.85em;">Report Bug</a>
            </div>
            """)

            with gr.Accordion("Project Team", open=True):
                gr.HTML("""
                <table style="width:100%; border-collapse:collapse;">
                <tr>
                    <td style="padding:10px 14px; border-bottom:1px solid rgba(128,128,128,0.15); vertical-align:middle;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <img src="https://github.com/ShiromiyaG.png" width="36" height="36" style="border-radius:50%;" />
                            <div>
                                <strong><a href="https://github.com/ShiromiyaG" target="_blank">ShiromiyaG</a></strong><br/>
                                <span style="color:#888; font-size:0.85em;">Owner of RVC-AI-Cover-Maker-UI (Base Project)</span>
                            </div>
                        </div>
                    </td>
                    <td style="padding:10px 14px; border-bottom:1px solid rgba(128,128,128,0.15); vertical-align:middle;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <img src="https://github.com/Eddycrack864.png" width="36" height="36" style="border-radius:50%;" />
                            <div>
                                <strong><a href="https://github.com/Eddycrack864" target="_blank">Eddycrack864</a></strong><br/>
                                <span style="color:#888; font-size:0.85em;">Contributor to RVC-AI-Cover-Maker-UI</span>
                            </div>
                        </div>
                    </td>
                </tr>
                <tr>
                    <td style="padding:10px 14px; border-bottom:1px solid rgba(128,128,128,0.15); vertical-align:middle;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <img src="https://github.com/BF667-IDLE.png" width="36" height="36" style="border-radius:50%;" />
                            <div>
                                <strong><a href="https://github.com/BF667-IDLE" target="_blank">BF667-IDLE</a></strong><br/>
                                <span style="color:#888; font-size:0.85em;">Hyper RVC Fork Owner</span>
                            </div>
                        </div>
                    </td>
                    <td style="padding:10px 14px; border-bottom:1px solid rgba(128,128,128,0.15); vertical-align:middle;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <img src="https://github.com/Nick088.png" width="36" height="36" style="border-radius:50%;" />
                            <div>
                                <strong><a href="https://linktr.ee/Nick088" target="_blank">Nick088</a></strong><br/>
                                <span style="color:#888; font-size:0.85em;">Colab & Kaggle UI Cells</span>
                            </div>
                        </div>
                    </td>
                </tr>
                <tr>
                    <td style="padding:10px 14px; border-bottom:1px solid rgba(128,128,128,0.15); vertical-align:middle;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <img src="https://github.com/PhamHuynhAnh16.png" width="36" height="36" style="border-radius:50%;" />
                            <div>
                                <strong><a href="https://github.com/PhamHuynhAnh16" target="_blank">PhamHuynhAnh16</a></strong><br/>
                                <span style="color:#888; font-size:0.85em;">Vietnamese-RVC -- F0 Predictors & Method Fixes</span>
                            </div>
                        </div>
                    </td>
                    <td style="padding:10px 14px; border-bottom:1px solid rgba(128,128,128,0.15); vertical-align:middle;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <div style="width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg,#ff6b6b,#ffa500); display:flex; align-items:center; justify-content:center; color:#fff; font-weight:bold; font-size:0.8em;">FB</div>
                            <div>
                                <strong><a href="https://www.youtube.com/@FullmatheusBallZ" target="_blank">FullmatheusBallZ</a></strong><br/>
                                <span style="color:#888; font-size:0.85em;">Colab Testing & QA</span>
                            </div>
                        </div>
                    </td>
                </tr>
                </table>
                """)

            with gr.Accordion("Core Projects & Libraries", open=False):
                gr.HTML("""
                <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap:10px;">
                    <div style="padding:12px; border-radius:10px; background:rgba(102,126,234,0.08); border:1px solid rgba(102,126,234,0.2);">
                        <strong>RVC-AI-Cover-Maker-UI</strong><br/>
                        <span style="color:#888; font-size:0.85em;">by <a href="https://github.com/ShiromiyaG">ShiromiyaG</a></span><br/>
                        <span style="font-size:0.82em;">Original UI framework and cover pipeline design</span><br/>
                        <a href="https://github.com/Eddycrack864/RVC-AI-Cover-Maker-UI" target="_blank" style="font-size:0.8em;">Visit Repo</a>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(46,204,113,0.08); border:1px solid rgba(46,204,113,0.2);">
                        <strong>Applio</strong><br/>
                        <span style="color:#888; font-size:0.85em;">by <a href="https://github.com/IAHispano">IAHispano</a></span><br/>
                        <span style="font-size:0.82em;">RVC inference engine, pitch extraction & model management</span><br/>
                        <a href="https://github.com/IAHispano/Applio" target="_blank" style="font-size:0.8em;">Visit Repo</a>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(231,76,60,0.08); border:1px solid rgba(231,76,60,0.2);">
                        <strong>Audio Separator</strong><br/>
                        <span style="color:#888; font-size:0.85em;">by <a href="https://github.com/beveradb">Andrew Beveridge</a></span><br/>
                        <span style="font-size:0.82em;">Python audio source separation wrapping UVR models</span><br/>
                        <a href="https://github.com/karaokenerds/python-audio-separator" target="_blank" style="font-size:0.8em;">Visit Repo</a>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(241,196,15,0.08); border:1px solid rgba(241,196,15,0.2);">
                        <strong>Ultimate Vocal Remover GUI</strong><br/>
                        <span style="color:#888; font-size:0.85em;">by <a href="https://github.com/Anjok07">Anjok07</a></span><br/>
                        <span style="font-size:0.82em;">Gold standard vocal removal with pretrained model weights</span><br/>
                        <a href="https://github.com/Anjok07/ultimatevocalremovergui" target="_blank" style="font-size:0.8em;">Visit Repo</a>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(155,89,182,0.08); border:1px solid rgba(155,89,182,0.2);">
                        <strong>Music Source Separation Training</strong><br/>
                        <span style="color:#888; font-size:0.85em;">by <a href="https://github.com/ZFTurbo">ZFTurbo</a></span><br/>
                        <span style="font-size:0.82em;">BS-Roformer, Mel-Band-Roformer, SCNet, MDX23C, Bandit, Demucs</span><br/>
                        <a href="https://github.com/ZFTurbo/Music-Source-Separation-Training" target="_blank" style="font-size:0.8em;">Visit Repo</a>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(52,152,219,0.08); border:1px solid rgba(52,152,219,0.2);">
                        <strong>AICoverGen</strong><br/>
                        <span style="color:#888; font-size:0.85em;">by <a href="https://github.com/SociallyIneptWeeb">SociallyIneptWeeb</a></span><br/>
                        <span style="font-size:0.82em;">AI cover generation pipeline with core processing concepts</span><br/>
                        <a href="https://github.com/SociallyIneptWeeb/AICoverGen" target="_blank" style="font-size:0.8em;">Visit Repo</a>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(255,193,7,0.08); border:1px solid rgba(255,193,7,0.2);">
                        <strong>Vietnamese-RVC</strong><br/>
                        <span style="color:#888; font-size:0.85em;">by <a href="https://github.com/PhamHuynhAnh16">PhamHuynhAnh16</a></span><br/>
                        <span style="font-size:0.82em;">DJCM, PESTO, SWIFT, SWIPE, PENN, HPA-RMVPE, FCPE-legacy, Mangio-CREPE</span><br/>
                        <a href="https://github.com/PhamHuynhAnh16/Vietnamese-RVC" target="_blank" style="font-size:0.8em;">Visit Repo</a>
                    </div>
                </div>
                """)

            with gr.Accordion("AI Models & Frameworks", open=False):
                gr.HTML("""
                <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap:10px;">
                    <div style="padding:12px; border-radius:10px; background:rgba(46,204,113,0.08); border:1px solid rgba(46,204,113,0.15);">
                        <strong>OpenAI Whisper</strong> -- Speech recognition<br/>
                        <span style="font-size:0.82em; color:#888;">by <a href="https://github.com/openai">OpenAI</a></span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(52,152,219,0.08); border:1px solid rgba(52,152,219,0.15);">
                        <strong>SpeechBrain</strong> -- Speaker diarization & ECAPA-TDNN<br/>
                        <span style="font-size:0.82em; color:#888;">by SpeechBrain Team</span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(231,76,60,0.08); border:1px solid rgba(231,76,60,0.15);">
                        <strong>PyTorch</strong> -- Deep learning framework<br/>
                        <span style="font-size:0.82em; color:#888;">by <a href="https://github.com/pytorch">Meta AI</a></span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(241,196,15,0.08); border:1px solid rgba(241,196,15,0.15);">
                        <strong>Transformers</strong> -- Model loading & inference<br/>
                        <span style="font-size:0.82em; color:#888;">by <a href="https://github.com/huggingface">HuggingFace</a></span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(155,89,182,0.08); border:1px solid rgba(155,89,182,0.15);">
                        <strong>NumPy</strong> -- Numerical computing<br/>
                        <span style="font-size:0.82em; color:#888;">by NumPy Team</span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(102,126,234,0.08); border:1px solid rgba(102,126,234,0.15);">
                        <strong>ONNX Runtime</strong> -- Fast model inference<br/>
                        <span style="font-size:0.82em; color:#888;">by <a href="https://github.com/microsoft">Microsoft</a></span>
                    </div>
                </div>
                """)

            with gr.Accordion("Voice & Pitch Extraction", open=False):
                gr.HTML("""
                <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap:10px;">
                    <div style="padding:12px; border-radius:10px; background:rgba(102,126,234,0.08); border:1px solid rgba(102,126,234,0.15);">
                        <strong>Edge TTS</strong> -- 400+ voices in 11 languages<br/>
                        <span style="font-size:0.82em; color:#888;">by <a href="https://github.com/rany2">rany2</a></span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(46,204,113,0.08); border:1px solid rgba(46,204,113,0.15);">
                        <strong>CREPE</strong> -- Pitch estimation (F0)<br/>
                        <span style="font-size:0.82em; color:#888;">by <a href="https://github.com/maxrmorrison">Max Morrison</a></span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(231,76,60,0.08); border:1px solid rgba(231,76,60,0.15);">
                        <strong>RMVPE</strong> -- Robust vocal pitch estimation<br/>
                        <span style="font-size:0.82em; color:#888;">by <a href="https://github.com/openvpi">OpenVPI</a></span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(241,196,15,0.08); border:1px solid rgba(241,196,15,0.15);">
                        <strong>FCPE</strong> -- Fundamental frequency contour extraction<br/>
                        <span style="font-size:0.82em; color:#888;">by <a href="https://github.com/SCToolsystem">SCToolsystem</a></span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(52,152,219,0.08); border:1px solid rgba(52,152,219,0.15);">
                        <strong>Faiss</strong> -- Voice embedding similarity search<br/>
                        <span style="font-size:0.82em; color:#888;">by <a href="https://github.com/facebookresearch">Meta Research</a></span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(155,89,182,0.08); border:1px solid rgba(155,89,182,0.15);">
                        <strong>TorchCREPE</strong> -- PyTorch-native CREPE implementation<br/>
                        <span style="font-size:0.82em; color:#888;">by <a href="https://github.com/maxrmorrison">Max Morrison</a></span>
                    </div>
                </div>
                """)

            with gr.Accordion("Audio Processing", open=False):
                gr.HTML("""
                <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap:10px;">
                    <div style="padding:12px; border-radius:10px; background:rgba(46,204,113,0.08); border:1px solid rgba(46,204,113,0.15);">
                        <strong>Pedalboard</strong> -- Studio-quality audio effects<br/>
                        <span style="font-size:0.82em; color:#888;">by <a href="https://github.com/spotify">Spotify</a></span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(231,76,60,0.08); border:1px solid rgba(231,76,60,0.15);">
                        <strong>pydub</strong> -- Audio manipulation & format conversion<br/>
                        <span style="font-size:0.82em; color:#888;">by <a href="https://github.com/jiaaro">James Robert</a></span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(241,196,15,0.08); border:1px solid rgba(241,196,15,0.15);">
                        <strong>librosa</strong> -- Music & audio analysis<br/>
                        <span style="font-size:0.82em; color:#888;">by librosa Team</span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(102,126,234,0.08); border:1px solid rgba(102,126,234,0.15);">
                        <strong>ffmpeg</strong> -- Audio/video processing engine<br/>
                        <span style="font-size:0.82em; color:#888;">FFmpeg Project</span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(52,152,219,0.08); border:1px solid rgba(52,152,219,0.15);">
                        <strong>SoundFile</strong> -- Audio file I/O (libsndfile)<br/>
                        <span style="font-size:0.82em; color:#888;">by Bastian Bechtold</span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(155,89,182,0.08); border:1px solid rgba(155,89,182,0.15);">
                        <strong>SciPy</strong> -- Signal processing & scientific computing<br/>
                        <span style="font-size:0.82em; color:#888;">by SciPy Team</span>
                    </div>
                </div>
                """)

            with gr.Accordion("Download & Network", open=False):
                gr.HTML("""
                <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap:10px;">
                    <div style="padding:12px; border-radius:10px; background:rgba(231,76,60,0.08); border:1px solid rgba(231,76,60,0.15);">
                        <strong>yt-dlp</strong> -- YouTube & 1000+ site downloader<br/>
                        <span style="font-size:0.82em; color:#888;">by yt-dlp contributors</span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(241,196,15,0.08); border:1px solid rgba(241,196,15,0.15);">
                        <strong>HuggingFace Hub</strong> -- Model & dataset hosting<br/>
                        <span style="font-size:0.82em; color:#888;">by <a href="https://github.com/huggingface">HuggingFace</a></span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(102,126,234,0.08); border:1px solid rgba(102,126,234,0.15);">
                        <strong>gdown</strong> -- Google Drive file downloader<br/>
                        <span style="font-size:0.82em; color:#888;">by <a href="https://github.com/wkentaro">Kentaro Wada</a></span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(46,204,113,0.08); border:1px solid rgba(46,204,113,0.15);">
                        <strong>MediaFire</strong> -- Cloud storage downloads<br/>
                        <span style="font-size:0.82em; color:#888;">MediaFire API</span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(155,89,182,0.08); border:1px solid rgba(155,89,182,0.15);">
                        <strong>Requests</strong> -- HTTP library for Python<br/>
                        <span style="font-size:0.82em; color:#888;">by Kenneth Reitz</span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(52,152,219,0.08); border:1px solid rgba(52,152,219,0.15);">
                        <strong>tqdm</strong> -- Progress bars for downloads<br/>
                        <span style="font-size:0.82em; color:#888;">by Casper da Costa-Luis</span>
                    </div>
                </div>
                """)

            with gr.Accordion("UI & Design", open=False):
                gr.HTML("""
                <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap:10px;">
                    <div style="padding:12px; border-radius:10px; background:rgba(241,196,15,0.08); border:1px solid rgba(241,196,15,0.15);">
                        <strong>Gradio</strong> -- Web UI framework<br/>
                        <span style="font-size:0.82em; color:#888;">by <a href="https://github.com/gradio-app">HuggingFace</a></span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(231,76,60,0.08); border:1px solid rgba(231,76,60,0.15);">
                        <strong>Freepik</strong> -- Cyber-themed cover image<br/>
                        <span style="font-size:0.82em; color:#888;"><a href="https://www.freepik.com">Freepik</a></span>
                    </div>
                    <div style="padding:12px; border-radius:10px; background:rgba(46,204,113,0.08); border:1px solid rgba(46,204,113,0.15);">
                        <strong>Python 3.12+</strong> -- Core language runtime<br/>
                        <span style="font-size:0.82em; color:#888;">by <a href="https://www.python.org">Python Software Foundation</a></span>
                    </div>
                </div>
                """)

        # ── Actions ────────────────────────────────────────────
        with gr.TabItem(i18n("Actions")):
            gr.Markdown("### Restart & Reset")

            restart_btn = gr.Button(
                i18n("Restart Application"),
                variant="primary",
                size="lg",
            )
            restart_info = gr.Textbox(
                label=i18n("Status"),
                interactive=False,
                visible=True,
            )
            restart_btn.click(
                fn=restart_app,
                inputs=[],
                outputs=[restart_info],
            )

            gr.Markdown("### Danger Zone")

            reset_btn = gr.Button(
                i18n("Reset All Settings to Defaults"),
                variant="stop",
                size="lg",
            )
            reset_info = gr.Textbox(
                label=i18n("Status"),
                interactive=False,
                visible=True,
            )
            reset_btn.click(
                fn=reset_to_defaults,
                inputs=[],
                outputs=[reset_info],
            )

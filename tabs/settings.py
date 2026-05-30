"""
Settings tab for Hyper-RVC WebUI.

UI-only settings: theme, language, about, restart.
"""

import gradio as gr
import os
import sys
import json
from pathlib import Path

from assets.i18n.i18n import I18nAuto
import assets.themes.loadThemes as loadThemes

i18n = I18nAuto()

now_dir = os.getcwd()
sys.path.append(now_dir)

CONFIG_PATH = os.path.join(now_dir, "assets", "config.json")
LANGUAGE_PATH = os.path.join(now_dir, "assets", "i18n", "languages")


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
        # --- New languages added ---
        # English regional variants
        "en_GB": "English (UK)",
        "en_AU": "English (Australia)",
        "en_CA": "English (Canada)",
        "en_IN": "English (India)",
        # Spanish regional variants
        "es_MX": "Espanol (Mexico)",
        "es_AR": "Espanol (Argentina)",
        "es_CO": "Espanol (Colombia)",
        # French regional variants
        "fr_CA": "Francais (Canada)",
        "fr_BE": "Francais (Belgique)",
        # German regional variants
        "de_AT": "Deutsch (Osterreich)",
        "de_CH": "Deutsch (Schweiz)",
        # Italian regional variant
        "it_CH": "Italiano (Svizzera)",
        # Chinese regional variant
        "zh_HK": "Hong Kong Traditional Chinese",
        # Arabic regional variants
        "ar_EG": "Arabic (Egypt)",
        "ar_MA": "Arabic (Morocco)",
        # Portuguese regional variant
        "pt_PT": "Portugues (Portugal)",
        # Other regional variants
        "ms_SG": "Bahasa Melayu (Singapore)",
        "nl_BE": "Nederlands (Belgie)",
        "sv_FI": "Svenska (Finland)",
        "ru_KZ": "Russian (Kazakhstan)",
        "pa_PK": "Punjabi (Pakistan)",
        "sw_TZ": "Kiswahili (Tanzania)",
        # European languages
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
        # Asian languages
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
        # African languages
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
        # Additional languages
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
    """Read config.json, returning dict or empty dict on error."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_config(config):
    """Write config dict to config.json."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_current_language():
    """Get currently selected language."""
    return _read_config().get("lang", {}).get("selected_lang", "en_US")


def save_language_selection(language):
    """Save language selection to config."""
    try:
        config = _read_config()
        config.setdefault("lang", {})
        config["lang"]["selected_lang"] = language
        config["lang"]["override"] = True
        _write_config(config)
        return "Language changed. Restart the app to apply."
    except Exception as e:
        return f"Error: {e}"


def save_theme_selection(theme):
    """Save theme selection to config."""
    try:
        config = _read_config()
        config.setdefault("theme", {})
        config["theme"]["class"] = theme
        config["theme"]["file"] = None
        _write_config(config)
        loadThemes.select_theme(theme)
        return f"Theme applied: {theme}"
    except Exception as e:
        return f"Error: {e}"


def get_current_theme():
    """Get currently selected theme."""
    return _read_config().get("theme", {}).get("class", "HyperRVC")


def reset_to_defaults():
    """Reset all settings to defaults."""
    try:
        _write_config({
            "theme": {"file": None, "class": "HyperRVC"},
            "lang": {"override": False, "selected_lang": "en_US"},
        })
        return "Settings reset. Restart the app to apply."
    except Exception as e:
        return f"Error: {e}"


def restart_app():
    """Return a message instructing the user to restart the app."""
    return "Please restart the application to apply changes."


def select_themes_tab():
    """Create the settings tab UI -- appearance, language, about."""

    current_lang = get_current_language()
    current_theme = get_current_theme()
    available_languages = get_available_languages()
    available_themes = loadThemes.get_list()

    with gr.Tabs():
        # -- Appearance --
        with gr.TabItem(i18n("Appearance")):
            gr.Markdown("### Theme")
            themes_select = gr.Dropdown(
                choices=available_themes,
                value=current_theme,
                label=i18n("Theme"),
                info=i18n("Select a theme. Changes apply immediately."),
                interactive=True,
            )
            theme_status = gr.Textbox(label=i18n("Status"), interactive=False, visible=True)
            themes_select.change(
                fn=save_theme_selection,
                inputs=[themes_select],
                outputs=[theme_status],
            )

            gr.Markdown("### Language")
            language_select = gr.Dropdown(
                choices=available_languages,
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

        # -- About --
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

        # -- Actions --
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

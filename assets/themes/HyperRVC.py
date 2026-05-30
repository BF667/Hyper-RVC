"""
HyperRVC – Custom Gradio theme for Hyper-RVC WebUI.

Based on Applio's dark theme design (https://github.com/IAHispano/Applio)
and modified for Hyper-RVC with a distinctive purple/blue gradient identity.

Design principles:
  - Near-black background (#0D0B12) with subtle purple undertones
  - Purple-to-blue accent palette for voice/audio branding
  - High contrast white text on dark surfaces
  - Rounded corners, soft shadows, and smooth transitions
  - Inter + JetBrains Mono font pairing
"""

from __future__ import annotations

from typing import Iterable

import gradio as gr
from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts, sizes


class HyperRVC(Base):
    def __init__(
        self,
        *,
        primary_hue: colors.Color | str = colors.indigo,
        secondary_hue: colors.Color | str = colors.violet,
        neutral_hue: colors.Color | str = colors.zinc,
        spacing_size: sizes.Size | str = sizes.spacing_md,
        radius_size: sizes.Size | str = sizes.radius_md,
        text_size: sizes.Size | str = sizes.text_lg,
        font: fonts.Font | str | Iterable[fonts.Font | str] = (
            "Inter",
            fonts.GoogleFont("Inter"),
            "ui-sans-serif",
            "system-ui",
            "-apple-system",
        ),
        font_mono: fonts.Font | str | Iterable[fonts.Font | str] = (
            "JetBrains Mono",
            fonts.GoogleFont("JetBrains Mono"),
            "ui-monospace",
            "SFMono-Regular",
        ),
    ):
        super().__init__(
            primary_hue=primary_hue,
            secondary_hue=secondary_hue,
            neutral_hue=neutral_hue,
            spacing_size=spacing_size,
            radius_size=radius_size,
            text_size=text_size,
            font=font,
            font_mono=font_mono,
        )
        self.name = "HyperRVC"

        # Custom secondary palette — violet/purple for voice identity
        self.secondary_50 = "#f5f3ff"
        self.secondary_100 = "#ede9fe"
        self.secondary_200 = "#ddd6fe"
        self.secondary_300 = "#c4b5fd"
        self.secondary_400 = "#a78bfa"
        self.secondary_500 = "#8b5cf6"
        self.secondary_600 = "#7c3aed"
        self.secondary_700 = "#6d28d9"
        self.secondary_800 = "#5b21b6"
        self.secondary_900 = "#4c1d95"
        self.secondary_950 = "#2e1065"

        # Primary palette — indigo/blue for interactive elements
        self.primary_50 = "#eef2ff"
        self.primary_100 = "#e0e7ff"
        self.primary_200 = "#c7d2fe"
        self.primary_300 = "#a5b4fc"
        self.primary_400 = "#818cf8"
        self.primary_500 = "#6366f1"
        self.primary_600 = "#4f46e5"
        self.primary_700 = "#4338ca"
        self.primary_800 = "#3730a3"
        self.primary_900 = "#312e81"
        self.primary_950 = "#1e1b4b"

        super().set(
            # ── Background ──────────────────────────────────────────
            background_fill_primary="#0D0B12",
            background_fill_primary_dark="#0D0B12",
            background_fill_secondary="#12101A",
            background_fill_secondary_dark="#12101A",
            body_background_fill="#0D0B12",
            body_background_fill_dark="#0D0B12",

            # ── Block ───────────────────────────────────────────────
            block_background_fill="#16131F",
            block_background_fill_dark="#16131F",
            block_border_color="#1E1B2E",
            block_border_color_dark="#1E1B2E",
            block_border_width="1px",
            block_border_width_dark="1px",
            block_info_text_color="*neutral_400",
            block_info_text_color_dark="*neutral_400",
            block_info_text_size="*text_sm",
            block_info_text_weight="400",
            block_label_background_fill="#1E1B2E",
            block_label_background_fill_dark="#1E1B2E",
            block_label_border_color="*border_color_primary",
            block_label_border_color_dark="*border_color_primary",
            block_label_border_width="1px",
            block_label_border_width_dark="1px",
            block_label_margin="0",
            block_label_padding="*spacing_sm *spacing_lg",
            block_label_radius="calc(*radius_lg - 1px) 0 calc(*radius_lg - 1px) 0",
            block_label_right_radius="0 calc(*radius_lg - 1px) 0 calc(*radius_lg - 1px)",
            block_label_shadow="*block_shadow",
            block_label_text_color="*primary_300",
            block_label_text_color_dark="*primary_300",
            block_label_text_weight="600",
            block_padding="*spacing_xl",
            block_radius="*radius_md",
            block_shadow="0 2px 8px rgba(0,0,0,0.3)",
            block_shadow_dark="0 2px 8px rgba(0,0,0,0.3)",
            block_title_background_fill="#1E1B2E",
            block_title_background_fill_dark="#1E1B2E",
            block_title_border_color="none",
            block_title_border_color_dark="none",
            block_title_border_width="0px",
            block_title_padding="*block_label_padding",
            block_title_radius="*block_label_radius",
            block_title_text_color="*primary_300",
            block_title_text_color_dark="*primary_300",
            block_title_text_size="*text_md",
            block_title_text_weight="600",

            # ── Body text ────────────────────────────────────────────
            body_text_color="#E8E6F0",
            body_text_color_dark="#E8E6F0",
            body_text_color_subdued="#8B87A0",
            body_text_color_subdued_dark="#8B87A0",
            body_text_size="*text_md",
            body_text_weight="400",

            # ── Borders ─────────────────────────────────────────────
            border_color_accent="*primary_600",
            border_color_accent_dark="*primary_600",
            border_color_primary="#1E1B2E",
            border_color_primary_dark="#1E1B2E",

            # ── Buttons ───────────────────────────────────────────────
            button_border_width="*input_border_width",
            button_border_width_dark="*input_border_width",
            button_cancel_background_fill="*neutral_800",
            button_cancel_background_fill_dark="*neutral_800",
            button_cancel_background_fill_hover="*neutral_700",
            button_cancel_background_fill_hover_dark="*neutral_700",
            button_cancel_border_color="*neutral_600",
            button_cancel_border_color_dark="*neutral_600",
            button_cancel_border_color_hover="*neutral_500",
            button_cancel_border_color_hover_dark="*neutral_500",
            button_cancel_text_color="*body_text_color",
            button_cancel_text_color_dark="*body_text_color",
            button_cancel_text_color_hover="*body_text_color",
            button_cancel_text_color_hover_dark="*body_text_color",
            button_large_padding="*spacing_lg calc(2 * *spacing_lg)",
            button_large_radius="*radius_lg",
            button_large_text_size="*text_lg",
            button_large_text_weight="600",
            button_primary_background_fill="*primary_600",
            button_primary_background_fill_dark="*primary_600",
            button_primary_background_fill_hover="*primary_500",
            button_primary_background_fill_hover_dark="*primary_500",
            button_primary_border_color="*primary_500",
            button_primary_border_color_dark="*primary_500",
            button_primary_border_color_hover="*primary_400",
            button_primary_border_color_hover_dark="*primary_400",
            button_primary_text_color="white",
            button_primary_text_color_dark="white",
            button_primary_text_color_hover="white",
            button_primary_text_color_hover_dark="white",
            button_secondary_background_fill="transparent",
            button_secondary_background_fill_dark="transparent",
            button_secondary_background_fill_hover="*neutral_800",
            button_secondary_background_fill_hover_dark="*neutral_800",
            button_secondary_border_color="*neutral_600",
            button_secondary_border_color_dark="*neutral_600",
            button_secondary_border_color_hover="*neutral_500",
            button_secondary_border_color_hover_dark="*neutral_500",
            button_secondary_text_color="*body_text_color",
            button_secondary_text_color_dark="*body_text_color",
            button_secondary_text_color_hover="*body_text_color",
            button_secondary_text_color_hover_dark="*body_text_color",
            button_small_padding="*spacing_sm calc(2 * *spacing_sm)",
            button_small_radius="*radius_lg",
            button_small_text_size="*text_md",
            button_small_text_weight="400",
            button_transition="0.25s ease all",

            # ── Checkbox ─────────────────────────────────────────────
            checkbox_background_color="#2A2640",
            checkbox_background_color_dark="#2A2640",
            checkbox_background_color_focus="*checkbox_background_color",
            checkbox_background_color_focus_dark="*checkbox_background_color",
            checkbox_background_color_hover="#332E4A",
            checkbox_background_color_hover_dark="#332E4A",
            checkbox_background_color_selected="*secondary_600",
            checkbox_background_color_selected_dark="*secondary_600",
            checkbox_border_color="*neutral_600",
            checkbox_border_color_dark="*neutral_600",
            checkbox_border_color_focus="*secondary_500",
            checkbox_border_color_focus_dark="*secondary_500",
            checkbox_border_color_hover="*neutral_500",
            checkbox_border_color_hover_dark="*neutral_500",
            checkbox_border_color_selected="*secondary_600",
            checkbox_border_color_selected_dark="*secondary_600",
            checkbox_border_radius="*radius_sm",
            checkbox_border_width="*input_border_width",
            checkbox_border_width_dark="*input_border_width",
            checkbox_check="url(\"data:image/svg+xml,%3csvg viewBox='0 0 16 16' fill='white' xmlns='http://www.w3.org/2000/svg'%3e%3cpath d='M12.207 4.793a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0l-2-2a1 1 0 011.414-1.414L6.5 9.086l4.293-4.293a1 1 0 011.414 0z'/%3e%3c/svg%3e\")",
            checkbox_label_background_fill="transparent",
            checkbox_label_background_fill_dark="transparent",
            checkbox_label_background_fill_hover="transparent",
            checkbox_label_background_fill_hover_dark="transparent",
            checkbox_label_background_fill_selected="transparent",
            checkbox_label_background_fill_selected_dark="transparent",
            checkbox_label_border_color="transparent",
            checkbox_label_border_color_dark="transparent",
            checkbox_label_border_color_hover="transparent",
            checkbox_label_border_color_hover_dark="transparent",
            checkbox_label_border_width="transparent",
            checkbox_label_border_width_dark="transparent",
            checkbox_label_gap="*spacing_lg",
            checkbox_label_padding="*spacing_md calc(2 * *spacing_md)",
            checkbox_label_shadow="none",
            checkbox_label_text_color="*body_text_color",
            checkbox_label_text_color_dark="*body_text_color",
            checkbox_label_text_color_selected="*checkbox_label_text_color",
            checkbox_label_text_color_selected_dark="*checkbox_label_text_color",
            checkbox_label_text_size="*text_md",
            checkbox_label_text_weight="400",
            checkbox_shadow="*input_shadow",

            # ── Color accents ────────────────────────────────────────
            color_accent="*primary_500",
            color_accent_soft="*primary_950",
            color_accent_soft_dark="*neutral_800",

            # ── Container / Embed ────────────────────────────────────
            container_radius="*radius_xl",
            embed_radius="*radius_lg",

            # ── Error ────────────────────────────────────────────────
            error_background_fill="#1C0F0F",
            error_background_fill_dark="#1C0F0F",
            error_border_color="#7F1D1D",
            error_border_color_dark="#7F1D1D",
            error_border_width="1px",
            error_border_width_dark="1px",
            error_text_color="#FCA5A5",
            error_text_color_dark="#FCA5A5",

            # ── Form ─────────────────────────────────────────────────
            form_gap_width="0px",

            # ── Input ─────────────────────────────────────────────────
            input_background_fill="#12101A",
            input_background_fill_dark="#12101A",
            input_background_fill_focus="*secondary_600",
            input_background_fill_focus_dark="*secondary_600",
            input_background_fill_hover="#1A1628",
            input_background_fill_hover_dark="#1A1628",
            input_border_color="#2A2640",
            input_border_color_dark="#2A2640",
            input_border_color_focus="*primary_500",
            input_border_color_focus_dark="*primary_500",
            input_border_color_hover="*neutral_600",
            input_border_color_hover_dark="*neutral_600",
            input_border_width="1px",
            input_border_width_dark="1px",
            input_padding="*spacing_xl",
            input_placeholder_color="#5B5775",
            input_placeholder_color_dark="#5B5775",
            input_radius="*radius_lg",
            input_shadow="none",
            input_shadow_dark="none",
            input_shadow_focus="0 0 0 2px rgba(99,102,241,0.25)",
            input_shadow_focus_dark="0 0 0 2px rgba(99,102,241,0.25)",
            input_text_size="*text_md",
            input_text_weight="400",

            # ── Layout ───────────────────────────────────────────────
            layout_gap="*spacing_xxl",

            # ── Links ────────────────────────────────────────────────
            link_text_color="*primary_400",
            link_text_color_active="*primary_400",
            link_text_color_active_dark="*primary_400",
            link_text_color_dark="*primary_400",
            link_text_color_hover="*primary_300",
            link_text_color_hover_dark="*primary_300",
            link_text_color_visited="*secondary_500",
            link_text_color_visited_dark="*secondary_500",

            # ── Loader ───────────────────────────────────────────────
            loader_color="*primary_500",
            loader_color_dark="*primary_500",

            # ── Panel ───────────────────────────────────────────────
            panel_background_fill="*background_fill_secondary",
            panel_background_fill_dark="*background_fill_secondary",
            panel_border_color="*border_color_primary",
            panel_border_color_dark="*border_color_primary",
            panel_border_width="1px",
            panel_border_width_dark="1px",

            # ── Prose ────────────────────────────────────────────────
            prose_header_text_weight="600",
            prose_text_size="*text_md",
            prose_text_weight="400",

            # ── Radio ────────────────────────────────────────────────
            radio_circle="url(\"data:image/svg+xml,%3csvg viewBox='0 0 16 16' fill='white' xmlns='http://www.w3.org/2000/svg'%3e%3ccircle cx='8' cy='8' r='3'/%3e%3c/svg%3e\")",

            # ── Section headers ──────────────────────────────────────
            section_header_text_size="*text_md",
            section_header_text_weight="400",

            # ── Shadows ─────────────────────────────────────────────
            shadow_drop="rgba(0,0,0,0.15) 0px 1px 3px 0px",
            shadow_drop_lg="0 4px 12px 0 rgba(99,102,241,0.1), 0 2px 6px 0 rgba(0,0,0,0.2)",
            shadow_inset="rgba(0,0,0,0.08) 0px 2px 4px 0px inset",
            shadow_spread="3px",
            shadow_spread_dark="1px",

            # ── Slider ───────────────────────────────────────────────
            slider_color="#8B5CF6",
            slider_color_dark="#8B5CF6",

            # ── Stat ─────────────────────────────────────────────────
            stat_background_fill="*primary_500",
            stat_background_fill_dark="*primary_500",

            # ── Table ────────────────────────────────────────────────
            table_border_color="#2A2640",
            table_border_color_dark="#2A2640",
            table_even_background_fill="#16131F",
            table_even_background_fill_dark="#16131F",
            table_odd_background_fill="#12101A",
            table_odd_background_fill_dark="#12101A",
            table_radius="*radius_lg",
            table_row_focus="*color_accent_soft",
            table_row_focus_dark="*color_accent_soft",
        )

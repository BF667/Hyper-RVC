"""
Legacy theme loader – kept for backward compatibility only.

All theme management has been migrated to ``theme_editor.py`` which
provides a full CSS theme editor with save/load capability.  This
module re-exports the new functions so that any code still importing
from ``loadThemes`` continues to work.
"""

import assets.themes.theme_editor as te

# Re-export for backward compatibility
get_list = te.list_saved_themes
load_json = lambda: None   # No longer returns a Gradio theme class
read_json = te.get_active_theme_name
select_theme = lambda name: None   # No-op; themes are now managed via CSS editor

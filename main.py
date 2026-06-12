"""
Hyper-RVC WebUI – legacy entry point.

This file is kept for backward compatibility.  The actual WebUI code now
lives in ``app.py``.  Running ``python main.py`` will redirect to
``app.py`` automatically.
"""

import sys
import os

# Run the new app module instead
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.argv = sys.argv  # preserve CLI args

from app import app, get_port_from_args, MAX_PORT_ATTEMPTS  # noqa: F401

if __name__ == "__main__":
    port = get_port_from_args()
    for _ in range(MAX_PORT_ATTEMPTS):
        try:
            app.launch(
                server_port=port,
                share="--share" in sys.argv,
                inbrowser="--open" in sys.argv,
                show_error=True,
            )
            break
        except OSError:
            print(
                f"Failed to launch on port {port}, trying again on port {port - 1}..."
            )
            port -= 1
        except Exception as error:
            print(f"An error occurred launching Gradio: {error}")
            break

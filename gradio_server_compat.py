"""
Compatibility shim for ``gradio.Server``.

Implements the ``gradio.Server`` API described in
https://huggingface.co/blog/introducing-gradio-server so that Hyper-RVC
can use ``@app.api()`` with Gradio's **real** queuing engine even though
the ``Server`` class is not yet in the released Gradio package (<= 6.x).

Architecture
------------
* ``Server`` extends ``fastapi.FastAPI`` – all standard FastAPI routes
  (``@app.get``, ``@app.post``, middleware, etc.) work natively.
* Internally a hidden ``gradio.Blocks`` is created inside a context
  manager.  Every function decorated with ``@app.api(name=...)`` is
  registered as an *API-only* endpoint on that Blocks using invisible
  JSON components, which gives us:
  - Gradio's queuing engine (concurrency control, serialization)
  - ``gradio_client`` / JS Client compatibility
  - ZeroGPU ``@spaces.GPU`` support
* ``app.launch()`` uses ``gradio.mount_gradio_app()`` to mount the
  Blocks onto the same FastAPI instance, then starts uvicorn.  This
  means the Gradio API routes live under ``/gradio_api/`` while custom
  FastAPI routes (like ``@app.get("/")`` for the homepage) coexist
  naturally.
* The custom static front-end is served via FastAPI routes and a
  ``StaticFiles`` mount – the HTML/JS connects to
  ``/gradio_api/`` using the Gradio JS Client.

Usage (identical to the blog post)::

    from gradio_server_compat import Server
    from gradio.data_classes import FileData
    from fastapi.responses import HTMLResponse

    app = Server()

    @app.get("/", response_class=HTMLResponse)
    async def homepage():
        return "<h1>Hello</h1>"

    @app.api(name="my_endpoint")
    def my_endpoint(param: str):
        return {"result": param.upper()}

    app.launch(server_port=7860)
"""

from __future__ import annotations

import asyncio
import inspect
import os
import sys
from typing import Any, Callable, Dict, Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

import gradio
from gradio.blocks import Blocks
from gradio.components import JSON as JSONComponent, Textbox
from gradio import mount_gradio_app


# ---------------------------------------------------------------------------
# Server class
# ---------------------------------------------------------------------------

class Server(FastAPI):
    """
    A FastAPI subclass that adds ``@app.api()`` and ``app.launch()``
    following the ``gradio.Server`` specification.

    Behind the scenes a ``gradio.Blocks`` instance is maintained so that
    ``@app.api()`` endpoints go through Gradio's real queue engine.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # Internal Blocks that hosts the queued API endpoints.
        # We build the Blocks lazily in _finalize_blocks().
        self._api_registry: Dict[str, dict] = {}
        self._api_counter: int = 0
        self._blocks: Blocks | None = None
        self._blocks_mounted: bool = False

        # Store the static dir for serving
        self._static_dir: str | None = None

    # ------------------------------------------------------------------
    # @app.api(name="...") decorator
    # ------------------------------------------------------------------
    def api(self, name: str, *, concurrency_limit: int | None = 1):
        """
        Decorator that registers a function as a Gradio-queued API endpoint.

        The endpoint is accessible as
        ``POST /gradio_api/api/<name>`` via the Gradio JS client and
        ``gradio_client``.  Gradio's queue engine handles concurrency
        control, serialization, and GPU request management.

        Parameters
        ----------
        name : str
            The API name (used in the URL and client calls).
        concurrency_limit : int or None, default 1
            Maximum concurrent calls.  Use ``None`` for unlimited.
        """
        def decorator(fn: Callable) -> Callable:
            self._api_counter += 1
            fn_id = self._api_counter

            self._api_registry[name] = {
                "fn": fn,
                "fn_id": fn_id,
                "concurrency_limit": concurrency_limit,
            }

            # If blocks were already finalized, we need to rebuild
            self._blocks = None

            return fn

        return decorator

    # ------------------------------------------------------------------
    # serve_static() – register a directory for static file serving
    # ------------------------------------------------------------------
    def serve_static(self, directory: str, url_path: str = "/static") -> None:
        """
        Register a directory for static file serving.

        Parameters
        ----------
        directory : str
            Absolute path to the directory containing static files.
        url_path : str
            URL prefix for static files (default ``/static``).
        """
        self._static_dir = directory
        if os.path.isdir(directory):
            self.mount(url_path, StaticFiles(directory=directory), name="static")

    # ------------------------------------------------------------------
    # _finalize_blocks() – build the internal Gradio Blocks
    # ------------------------------------------------------------------
    def _finalize_blocks(self) -> Blocks:
        """
        Build (or rebuild) the internal ``gradio.Blocks`` from all
        registered ``@app.api()`` endpoints.

        This must be called *before* ``launch()``.
        """
        if self._blocks is not None:
            return self._blocks

        # Create Blocks and register all API endpoints inside the
        # context manager, exactly like normal Gradio usage.
        blocks = Blocks()
        blocks.queue()  # enable the queue

        with blocks:
            for api_name, info in self._api_registry.items():
                fn = info["fn"]
                cl = info["concurrency_limit"]
                sig = inspect.signature(fn)
                params = list(sig.parameters.values())

                # We use a single JSON component as input and output.
                # The Gradio client will send JSON data which gets
                # deserialized by the JSON component.
                json_input = JSONComponent(visible=False, label=f"api_in_{api_name}")
                json_output = JSONComponent(visible=False, label=f"api_out_{api_name}")

                # Build a wrapper that bridges the JSON component
                # to the user's function signature.
                def _make_wrapper(original_fn, original_params):
                    async def _api_wrapper(data: Any) -> Any:
                        if len(original_params) == 1 and _is_dict_annotation(original_params[0].annotation):
                            kwargs = {original_params[0].name: data}
                        elif len(original_params) >= 1 and original_params[0].name == "params" and _is_dict_annotation(original_params[0].annotation):
                            kwargs = {original_params[0].name: data}
                        elif isinstance(data, dict):
                            accepted = {p.name for p in original_params}
                            kwargs = {k: v for k, v in data.items() if k in accepted}
                        else:
                            kwargs = {}

                        if inspect.iscoroutinefunction(original_fn):
                            result = await original_fn(**kwargs)
                        else:
                            loop = asyncio.get_event_loop()
                            result = await loop.run_in_executor(
                                None, lambda: original_fn(**kwargs)
                            )

                        return _serialize(result)

                    return _api_wrapper

                wrapper = _make_wrapper(fn, params)

                # Register as an API-only event on the Blocks.
                # Using .change() on a virtual input component creates a
                # callable API endpoint that goes through the queue.
                json_input.change(
                    fn=wrapper,
                    inputs=[json_input],
                    outputs=[json_output],
                    api_name=api_name,
                    concurrency_limit=cl,
                )

        self._blocks = blocks
        return blocks

    # ------------------------------------------------------------------
    # launch() – start the Gradio server
    # ------------------------------------------------------------------
    def launch(
        self,
        server_port: int = 7860,
        server_name: str = "0.0.0.0",
        share: bool = False,
        inbrowser: bool = False,
        show_error: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Start the server.

        If API endpoints were registered with ``@app.api()``, the
        internal Gradio Blocks is mounted at ``/gradio_api`` using
        ``gradio.mount_gradio_app()``.  Custom FastAPI routes coexist
        naturally because the Gradio App is itself a FastAPI sub-app.

        The server is started via uvicorn with the combined app.
        """
        # Finalize the internal Blocks from all registered APIs
        if self._api_registry:
            blocks = self._finalize_blocks()

            # Mount Gradio Blocks onto this FastAPI at /gradio_api
            # mount_gradio_app creates a gradio.routes.App (FastAPI subclass)
            # and mounts it at the given path.
            if not self._blocks_mounted:
                mount_gradio_app(
                    self,
                    blocks,
                    path="/gradio_api",
                    server_name=server_name,
                    server_port=server_port,
                    show_error=show_error,
                )
                self._blocks_mounted = True

        # Start uvicorn with our combined FastAPI app
        try:
            import uvicorn
        except ImportError:
            print("ERROR: uvicorn is required. Install with: pip install uvicorn")
            sys.exit(1)

        print(f"╔══════════════════════════════════════════════════════╗")
        print(f"║         Hyper-RVC Server - Gradio Backend           ║")
        print(f"╠══════════════════════════════════════════════════════╣")
        print(f"║  Frontend:  http://{server_name}:{server_port}/")
        print(f"║  Gradio API: http://{server_name}:{server_port}/gradio_api/")
        print(f"║  API Docs:   http://{server_name}:{server_port}/docs")
        print(f"╚══════════════════════════════════════════════════════╝")

        uvicorn.run(self, host=server_name, port=server_port, log_level="info")


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _is_dict_annotation(annotation: Any) -> bool:
    """Check if a type annotation is ``dict`` or ``Dict``."""
    if annotation is inspect.Parameter.empty:
        return False
    origin = getattr(annotation, "__origin__", None)
    if origin is dict:
        return True
    return annotation is dict


def _serialize(obj: Any) -> Any:
    """Make an object JSON-serializable (best-effort)."""
    if obj is None or isinstance(obj, (bool, int, float, str, list, dict)):
        return obj
    if isinstance(obj, (tuple, set, frozenset)):
        return list(obj)
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return str(obj)
    return str(obj)


# ---------------------------------------------------------------------------
# Monkey-patch: inject Server into the gradio namespace so that
# ``from gradio import Server`` works transparently.
# ---------------------------------------------------------------------------

def _patch_gradio() -> None:
    """Inject this Server class into the ``gradio`` module."""
    try:
        import gradio
        if not hasattr(gradio, "Server"):
            gradio.Server = Server  # type: ignore[attr-defined]
    except ImportError:
        pass


# Auto-patch on import
_patch_gradio()

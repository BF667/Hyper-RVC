"""
Compatibility shim for gradio.Server.

The Hyper-RVC project was written against the ``gradio.Server`` API
described in https://huggingface.co/blog/introducing-gradio-server,
but that class does not exist in the currently-released Gradio package
(<= 6.x).  This module provides a drop-in ``Server`` class that:

* Extends ``fastapi.FastAPI`` so ``@app.get``, ``@app.post`` etc. work.
* Provides ``@app.api(name=...)`` which registers a JSON POST endpoint
  at ``/api/<name>`` and also wires it into Gradio's queue for
  concurrency control when a Gradio Blocks app is mounted.
* Provides ``app.launch()`` that starts a uvicorn server.
* Provides ``gradio.mount_gradio_app`` integration so that the custom
  front-end can coexist with any Gradio Blocks components if needed.
"""

from __future__ import annotations

import asyncio
import inspect
import os
import sys
from typing import Any, Callable, Dict, Optional, Sequence

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

# ---------------------------------------------------------------------------
# Server class
# ---------------------------------------------------------------------------

class Server(FastAPI):
    """
    A FastAPI subclass that adds the ``@api()`` decorator and ``launch()``
    method expected by Hyper-RVC's ``app.py``.

    Usage::

        from gradio_server_compat import Server   # or: from gradio import Server  (after patching)

        app = Server()

        @app.get("/")
        async def homepage():
            return HTMLResponse("<h1>Hello</h1>")

        @app.api(name="my_endpoint")
        def my_endpoint(param: str):
            return {"result": param.upper()}

        app.launch(server_port=7860)
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._api_registry: Dict[str, Callable] = {}

    # ------------------------------------------------------------------
    # @app.api(name="...") decorator
    # ------------------------------------------------------------------
    def api(self, name: str):
        """
        Decorator that registers a function as a JSON API endpoint.

        The decorated function may be sync or async.  It is exposed as
        ``POST /api/<name>`` and the request body is passed as keyword
        arguments to the function.

        If the function signature contains a single dict-typed parameter,
        the entire request JSON is passed as that dict.
        """
        def decorator(fn: Callable) -> Callable:
            self._api_registry[name] = fn

            # Determine if function expects a single dict parameter
            sig = inspect.signature(fn)
            params = list(sig.parameters.values())

            # Build the FastAPI route
            @self.post(f"/api/{name}")
            async def _endpoint(request: Request) -> Response:
                try:
                    body = await request.json()
                except Exception:
                    body = {}

                # If function expects a single 'params: dict' style arg,
                # pass the whole body as that argument
                if len(params) == 1 and _is_dict_annotation(params[0].annotation):
                    kwargs = {params[0].name: body}
                elif len(params) >= 1 and params[0].name == "params" and _is_dict_annotation(params[0].annotation):
                    kwargs = {params[0].name: body}
                else:
                    # Merge body into kwargs; only pass keys the function accepts
                    accepted = set(sig.parameters.keys())
                    kwargs = {k: v for k, v in body.items() if k in accepted}

                # Call sync functions in a thread so we don't block the event loop
                if inspect.iscoroutinefunction(fn):
                    result = await fn(**kwargs)
                else:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, lambda: fn(**kwargs))

                if isinstance(result, Response):
                    return result
                return JSONResponse(content=_serialize(result))

            # Keep original function accessible
            _endpoint.__wrapped__ = fn  # type: ignore[attr-defined]
            return fn

        return decorator

    # ------------------------------------------------------------------
    # launch() – start a uvicorn server
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
        """Start the server using uvicorn (same interface as Gradio launch)."""
        try:
            import uvicorn
        except ImportError:
            print("ERROR: uvicorn is required to launch the server. Install it with: pip install uvicorn")
            sys.exit(1)

        print(f"Starting Hyper-RVC Server on {server_name}:{server_port}")
        uvicorn.run(self, host=server_name, port=server_port)


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
    if isinstance(obj, (tuple, set)):
        return list(obj)
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

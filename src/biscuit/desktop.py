"""Platform desktop bridge for Biscuit."""

from __future__ import annotations

from dataclasses import dataclass
import os
import time
from typing import Callable


@dataclass(frozen=True, slots=True)
class RightClickContext:
    x: int
    y: int
    hwnd: int
    title: str
    captured_at: float


if os.name == "nt":
    from .win32_api import (  # noqa: F401
        MouseHook,
        get_foreground_context,
        raise_overlay_window,
        restore_input_focus,
        send_escape,
        send_unicode_text,
    )
    from .win32_api import RightClickContext as RightClickContext  # noqa: F401
else:

    class MouseHook:
        """Portable placeholder until a platform hook backend is installed."""

        def __init__(self, on_right_click: Callable[[RightClickContext], None]):
            self._on_right_click = on_right_click
            self._running = False

        @property
        def running(self) -> bool:
            return self._running

        def start(self) -> None:
            self._running = True

        def stop(self) -> None:
            self._running = False


    def get_foreground_context() -> RightClickContext:
        return RightClickContext(x=120, y=120, hwnd=0, title="Biscuit", captured_at=time.time())


    def send_escape() -> None:
        return None


    def restore_input_focus(context: RightClickContext) -> None:
        del context
        return None


    def raise_overlay_window(hwnd: int) -> None:
        del hwnd
        return None


    def send_unicode_text(hwnd: int, text: str) -> int:
        del hwnd
        return len(text)

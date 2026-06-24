"""Tray/menu-bar support for Biscuit."""

from __future__ import annotations

from dataclasses import dataclass
import threading
from typing import Callable

from PIL import Image, ImageDraw


BLUE_BLACK = (7, 17, 31)
PANEL = (16, 27, 45)
YELLOW = (255, 210, 63)
CYAN = (96, 215, 255)


def build_tray_icon_image(size: int = 64) -> Image.Image:
    image = Image.new("RGBA", (size, size), BLUE_BLACK + (255,))
    draw = ImageDraw.Draw(image)
    stripe_height = max(5, size // 6)
    draw.rectangle((0, 0, size, stripe_height), fill=YELLOW + (255,))
    inset = max(5, size // 10)
    draw.rounded_rectangle(
        (inset, stripe_height + inset // 2, size - inset, size - inset),
        radius=max(3, size // 10),
        outline=CYAN + (255,),
        width=max(2, size // 18),
        fill=PANEL + (255,),
    )
    draw.ellipse(
        (size * 0.34, size * 0.34, size * 0.66, size * 0.66),
        fill=YELLOW + (255,),
    )
    draw.rectangle(
        (size * 0.46, size * 0.58, size * 0.54, size * 0.78),
        fill=YELLOW + (255,),
    )
    return image


@dataclass(slots=True)
class TrayCallbacks:
    show_settings: Callable[[], None]
    dictate_at_cursor: Callable[[], None]
    start_biscuit: Callable[[], None]
    stop_biscuit: Callable[[], None]
    quit_app: Callable[[], None]


class TrayController:
    def __init__(self, callbacks: TrayCallbacks):
        self.callbacks = callbacks
        self.available = False
        self._icon = None
        self._thread: threading.Thread | None = None

    def start(self) -> bool:
        try:
            import pystray
        except Exception:
            return False

        menu = pystray.Menu(
            pystray.MenuItem("Biscuit Settings", lambda _icon, _item: self.callbacks.show_settings(), default=True),
            pystray.MenuItem("Dictate at Cursor", lambda _icon, _item: self.callbacks.dictate_at_cursor()),
            pystray.MenuItem("Start Biscuit", lambda _icon, _item: self.callbacks.start_biscuit()),
            pystray.MenuItem("Quit Biscuit", lambda _icon, _item: self.callbacks.stop_biscuit()),
            pystray.MenuItem("Quit Biscuit", lambda _icon, _item: self.callbacks.quit_app()),
        )
        self._icon = pystray.Icon("Biscuit", build_tray_icon_image(), "Biscuit", menu)
        self._thread = threading.Thread(target=self._icon.run, name="BiscuitTray", daemon=True)
        self._thread.start()
        self.available = True
        return True

    def stop(self) -> None:
        if self._icon is not None:
            self._icon.stop()
        self.available = False

"""Tkinter overlay surfaces for Biscuit."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from typing import Callable

from .config import BiscuitConfig
from .desktop import RightClickContext, raise_overlay_window
from .status import DictationOutcome, DictationResult, status_text


BLUE_BLACK = "#07111f"
GUNMETAL = "#101b2d"
PANEL = "#17243a"
PANEL_DEEP = "#0d192b"
YELLOW = "#ffd23f"
CYAN = "#60d7ff"
RED = "#ff4d5e"
GREEN = "#55d488"
TEXT = "#f4fbff"
ACCENT_TEXT = BLUE_BLACK
SURFACE_WHITE = "#ffffff"
EDGE_WHITE = "#dff7ff"
TRANSPARENT_KEY = "#ff00fe"
MUTED = "#8ea0b8"
MENU_BG = BLUE_BLACK
MENU_HOVER = PANEL
MENU_TEXT = TEXT
DROP_MENU_OUTLINE = "#61d0ff"
UI_FONT_FAMILY = "Segoe UI"
UI_FONT = (UI_FONT_FAMILY, 9)
UI_FONT_BOLD = (UI_FONT_FAMILY, 9, "bold")
UI_FONT_TITLE = (UI_FONT_FAMILY, 18, "bold")
ACTION_MENU_WIDTH = 236
ACTION_MENU_HEIGHT = 36
RECORDING_PILL_WIDTH = 292
RECORDING_PILL_HEIGHT = 86
RECORDING_PILL_OFFSET_Y = 28
SETTINGS_WINDOW_GEOMETRY = "720x560+120+120"
SETTINGS_WINDOW_MINSIZE = (680, 520)
CORNER_RADIUS_ACTION = 12
CORNER_RADIUS_PANEL = 18
FLOATING_INSET = 4
FLOATING_BORDER = 2
SETTINGS_ACTION_LABELS = {
    "update": "Find Model",
    "test": "Test Biscuit",
    "stop": "Stop Biscuit",
    "save": "Save",
}
STARTUP_SETTING_LABEL = "Run Biscuit when I log in"
PROCESSING_LABEL = "Processing"
READY_LABEL = "Ready"
FINISHED_RECORDING_STATUSES = {
    status_text(DictationOutcome(DictationResult.COPIED)),
    status_text(DictationOutcome(DictationResult.INSERTED)),
    status_text(DictationOutcome(DictationResult.NO_SPEECH)),
}
FINISHED_RECORDING_PREFIXES = (
    "microphone unavailable",
    "model unavailable",
    "transcription failed",
    "target unavailable",
)


def text_color_for_background(background: str) -> str:
    hex_color = background.lstrip("#")
    if len(hex_color) != 6:
        return TEXT
    red = int(hex_color[0:2], 16)
    green = int(hex_color[2:4], 16)
    blue = int(hex_color[4:6], 16)
    luminance = (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255
    return TEXT if luminance < 0.42 else ACCENT_TEXT


def rounded_rect_points(x1: int, y1: int, x2: int, y2: int, radius: int) -> list[tuple[int, int]]:
    radius = max(0, min(radius, (x2 - x1) // 2, (y2 - y1) // 2))
    return [
        (x1 + radius, y1),
        (x2 - radius, y1),
        (x2, y1),
        (x2, y1 + radius),
        (x2, y2 - radius),
        (x2, y2),
        (x2 - radius, y2),
        (x1 + radius, y2),
        (x1, y2),
        (x1, y2 - radius),
        (x1, y1 + radius),
    ]


def _flat_points(points: list[tuple[int, int]]) -> list[int]:
    return [coordinate for point in points for coordinate in point]


def _draw_rounded_rect(
    canvas: tk.Canvas,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    radius: int,
    *,
    fill: str,
    outline: str | None = None,
    width: int = 1,
) -> int:
    return canvas.create_polygon(
        _flat_points(rounded_rect_points(x1, y1, x2, y2, radius)),
        smooth=True,
        fill=fill,
        outline=outline or fill,
        width=width,
    )


def _draw_inset_accent(
    canvas: tk.Canvas,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    *,
    fill: str = YELLOW,
) -> int:
    return _draw_rounded_rect(canvas, x1, y1, x2, y2, 3, fill=fill, outline=fill)


def _enable_transparent_edges(window: tk.Toplevel, fallback_bg: str = BLUE_BLACK) -> bool:
    window.configure(bg=TRANSPARENT_KEY)
    try:
        window.attributes("-transparentcolor", TRANSPARENT_KEY)
        return True
    except tk.TclError:
        window.configure(bg=fallback_bg)
        return False


def biscuit_icon_path() -> Path:
    return Path(__file__).resolve().parents[2] / "assets" / "Biscuit.ico"


def apply_biscuit_icon(window: tk.Misc, icon_path: Path | None = None) -> bool:
    path = icon_path or biscuit_icon_path()
    if not path.exists():
        return False
    try:
        window.iconbitmap(str(path))
        return True
    except (OSError, tk.TclError):
        return False


def action_menu_position(
    cursor_x: int,
    cursor_y: int,
    screen_width: int | None = None,
    screen_height: int | None = None,
) -> tuple[int, int]:
    x = cursor_x
    y = cursor_y - ACTION_MENU_HEIGHT
    if screen_width is not None:
        x = min(max(0, x), max(0, screen_width - ACTION_MENU_WIDTH))
    if screen_height is not None:
        y = min(max(0, y), max(0, screen_height - ACTION_MENU_HEIGHT))
    else:
        y = max(0, y)
    return x, y


def recording_pill_position(
    cursor_x: int,
    cursor_y: int,
    screen_width: int | None = None,
    screen_height: int | None = None,
) -> tuple[int, int]:
    x = cursor_x
    y = cursor_y + RECORDING_PILL_OFFSET_Y
    if screen_width is not None:
        x = min(max(0, x), max(0, screen_width - RECORDING_PILL_WIDTH))
    if screen_height is not None:
        y = min(max(0, y), max(0, screen_height - RECORDING_PILL_HEIGHT))
    return x, y


@dataclass(slots=True)
class SettingsCallbacks:
    on_save: Callable[[BiscuitConfig], None]
    on_test: Callable[[], None]
    on_kill: Callable[[], None]
    on_update: Callable[[], str]


@dataclass(frozen=True, slots=True)
class RecordingControlState:
    text: str
    spinner: str
    tk_state: str
    bg: str
    fg: str
    active_bg: str


def recording_control_state(status: str, tick: int = 0) -> RecordingControlState:
    del tick
    if status == "processing":
        return RecordingControlState(
            text=PROCESSING_LABEL,
            spinner="",
            tk_state=tk.DISABLED,
            bg=GUNMETAL,
            fg=TEXT,
            active_bg=GUNMETAL,
        )
    if status in FINISHED_RECORDING_STATUSES or status.startswith(FINISHED_RECORDING_PREFIXES):
        return RecordingControlState(
            text=READY_LABEL,
            spinner="",
            tk_state=tk.DISABLED,
            bg=GREEN,
            fg=text_color_for_background(GREEN),
            active_bg=GREEN,
        )
    return RecordingControlState(
        text="Stop",
        spinner="",
        tk_state=tk.NORMAL,
        bg=RED,
        fg=text_color_for_background(RED),
        active_bg="#d63a49",
    )


class BiscuitOverlay:
    def __init__(
        self,
        root: tk.Tk,
        config: BiscuitConfig,
        settings_callbacks: SettingsCallbacks,
        show_fallback_toolbar: bool = True,
    ):
        self.root = root
        self.config = config
        self.settings_callbacks = settings_callbacks
        self.show_fallback_toolbar = show_fallback_toolbar
        self.action_window: tk.Toplevel | None = None
        self.recording_window: tk.Toplevel | None = None
        self.settings_window: tk.Toplevel | None = None
        self.recording_status: tk.StringVar | None = None
        self.recording_control_text: tk.StringVar | None = None
        self.recording_control_button: tk.Button | None = None
        self._recording_control_tick = 0
        self._recording_control_after: str | None = None
        self.settings_status: tk.StringVar | None = None
        self.test_output: tk.StringVar | None = None
        self.model_var = tk.StringVar(value=config.model_path)
        self.language_var = tk.StringVar(value=config.language)
        self.provider_var = tk.StringVar(value=config.provider)
        self.run_at_login_var = tk.BooleanVar(value=config.run_at_login)
        if show_fallback_toolbar:
            self._build_toolbar()
        else:
            self.root.withdraw()

    def show_action(self, context: RightClickContext, on_biscuit: Callable[[RightClickContext], None]) -> None:
        self.close_action()
        window = tk.Toplevel(self.root)
        window.overrideredirect(True)
        window.attributes("-topmost", True)
        try:
            window.attributes("-toolwindow", True)
        except tk.TclError:
            pass
        has_transparent_edges = _enable_transparent_edges(window, MENU_BG)
        x, y = action_menu_position(
            context.x,
            context.y,
            screen_width=self.root.winfo_screenwidth(),
            screen_height=self.root.winfo_screenheight(),
        )
        window.geometry(f"{ACTION_MENU_WIDTH}x{ACTION_MENU_HEIGHT}+{x}+{y}")
        self.action_window = window

        canvas = tk.Canvas(
            window,
            width=ACTION_MENU_WIDTH,
            height=ACTION_MENU_HEIGHT,
            bg=TRANSPARENT_KEY if has_transparent_edges else MENU_BG,
            highlightthickness=0,
            bd=0,
        )
        canvas.pack(fill=tk.BOTH, expand=True)
        _draw_rounded_rect(
            canvas,
            FLOATING_BORDER,
            FLOATING_BORDER,
            ACTION_MENU_WIDTH - FLOATING_BORDER - 1,
            ACTION_MENU_HEIGHT - FLOATING_BORDER - 1,
            CORNER_RADIUS_ACTION,
            fill=MENU_BG,
            outline=DROP_MENU_OUTLINE,
            width=2,
        )
        _draw_inset_accent(canvas, 12, 10, 16, ACTION_MENU_HEIGHT - 10)
        button = tk.Button(
            window,
            text="Biscuit",
            command=lambda: self._activate_action(context, on_biscuit),
            bg=MENU_BG,
            fg=MENU_TEXT,
            activebackground=MENU_HOVER,
            activeforeground=MENU_TEXT,
            relief=tk.FLAT,
            bd=0,
            anchor="w",
            padx=26,
            pady=0,
            font=UI_FONT,
            cursor="hand2",
        )
        canvas.create_window(
            FLOATING_INSET + 4,
            FLOATING_INSET + 1,
            anchor="nw",
            window=button,
            width=ACTION_MENU_WIDTH - (FLOATING_INSET * 2) - 8,
            height=ACTION_MENU_HEIGHT - (FLOATING_INSET * 2) - 2,
        )
        self._pin_action_window(window)
        window.after(4500, self.close_action)

    def _pin_action_window(self, window: tk.Toplevel, remaining: int = 12) -> None:
        if remaining <= 0 or self.action_window is not window:
            return
        try:
            window.lift()
            window.attributes("-topmost", True)
            window.update_idletasks()
            raise_overlay_window(int(window.winfo_id()))
            window.after(50, lambda: self._pin_action_window(window, remaining - 1))
        except tk.TclError:
            return

    def show_recording(self, context: RightClickContext, on_stop: Callable[[], None]) -> None:
        self.close_recording()
        window = tk.Toplevel(self.root)
        window.overrideredirect(True)
        window.attributes("-topmost", True)
        has_transparent_edges = _enable_transparent_edges(window, YELLOW)
        x, y = recording_pill_position(
            context.x,
            context.y,
            screen_width=self.root.winfo_screenwidth(),
            screen_height=self.root.winfo_screenheight(),
        )
        window.geometry(f"{RECORDING_PILL_WIDTH}x{RECORDING_PILL_HEIGHT}+{x}+{y}")
        self.recording_window = window
        self.recording_status = tk.StringVar(value="recording")
        self.recording_control_text = tk.StringVar(value=recording_control_state("recording").text)
        stopped = {"value": False}

        def request_stop(event=None):
            del event
            if stopped["value"]:
                return "break"
            stopped["value"] = True
            on_stop()
            return "break"

        canvas = tk.Canvas(
            window,
            width=RECORDING_PILL_WIDTH,
            height=RECORDING_PILL_HEIGHT,
            bg=TRANSPARENT_KEY if has_transparent_edges else YELLOW,
            highlightthickness=0,
            bd=0,
        )
        canvas.pack(fill=tk.BOTH, expand=True)
        _draw_rounded_rect(
            canvas,
            FLOATING_BORDER,
            FLOATING_BORDER,
            RECORDING_PILL_WIDTH - FLOATING_BORDER - 1,
            RECORDING_PILL_HEIGHT - FLOATING_BORDER - 1,
            CORNER_RADIUS_PANEL,
            fill=BLUE_BLACK,
            outline=EDGE_WHITE,
        )
        _draw_rounded_rect(
            canvas,
            FLOATING_INSET + 2,
            FLOATING_INSET + 2,
            RECORDING_PILL_WIDTH - FLOATING_INSET - 3,
            RECORDING_PILL_HEIGHT - FLOATING_INSET - 3,
            CORNER_RADIUS_PANEL - 4,
            fill=BLUE_BLACK,
            outline=CYAN,
        )
        _draw_inset_accent(canvas, 16, 16, 21, RECORDING_PILL_HEIGHT - 16)
        frame = tk.Frame(canvas, bg=BLUE_BLACK, padx=16, pady=10)
        canvas.create_window(
            24,
            8,
            anchor="nw",
            window=frame,
            width=RECORDING_PILL_WIDTH - 34,
            height=RECORDING_PILL_HEIGHT - 16,
        )
        frame.columnconfigure(0, weight=1, minsize=92)
        frame.columnconfigure(1, minsize=136)
        title = tk.Label(frame, text="BISCUIT", fg=SURFACE_WHITE, bg=BLUE_BLACK, font=UI_FONT_BOLD)
        title.grid(
            row=0, column=0, sticky="w"
        )
        status = tk.Label(frame, textvariable=self.recording_status, fg=EDGE_WHITE, bg=BLUE_BLACK, font=UI_FONT)
        status.grid(
            row=1, column=0, sticky="w", pady=(2, 0)
        )
        stop_button = tk.Button(
            frame,
            textvariable=self.recording_control_text,
            command=request_stop,
            bg=RED,
            fg=text_color_for_background(RED),
            disabledforeground=text_color_for_background(RED),
            activebackground="#d63a49",
            activeforeground=text_color_for_background("#d63a49"),
            relief=tk.FLAT,
            bd=0,
            width=15,
            padx=6,
            pady=4,
            font=UI_FONT,
            cursor="hand2",
        )
        self.recording_control_button = stop_button
        stop_button.grid(row=0, column=1, rowspan=2, padx=(14, 0), sticky="e")
        for widget in (window, canvas, frame, title, status, stop_button):
            widget.bind("<ButtonRelease-1>", request_stop)
        self._render_recording_control("recording")

    def set_recording_status(self, status: str) -> None:
        if self.recording_status:
            self.recording_status.set(status)
        self._render_recording_control(status)

    def _render_recording_control(self, status: str) -> None:
        self._cancel_recording_control_animation()
        state = recording_control_state(status)
        self._apply_recording_control_state(state)

    def _animate_recording_control(self) -> None:
        state = recording_control_state("processing", self._recording_control_tick)
        self._recording_control_tick += 1
        self._apply_recording_control_state(state)
        if self.recording_window:
            self._recording_control_after = self.recording_window.after(140, self._animate_recording_control)

    def _apply_recording_control_state(self, state: RecordingControlState) -> None:
        if self.recording_control_text:
            self.recording_control_text.set(state.text)
        if self.recording_control_button:
            self.recording_control_button.configure(
                state=state.tk_state,
                bg=state.bg,
                fg=state.fg,
                disabledforeground=state.fg,
                activebackground=state.active_bg,
            )

    def _cancel_recording_control_animation(self) -> None:
        if self._recording_control_after and self.recording_window:
            try:
                self.recording_window.after_cancel(self._recording_control_after)
            except tk.TclError:
                pass
        self._recording_control_after = None

    def close_action(self) -> None:
        if self.action_window:
            self.action_window.destroy()
            self.action_window = None

    def close_recording(self) -> None:
        self._cancel_recording_control_animation()
        if self.recording_window:
            self.recording_window.destroy()
            self.recording_window = None
            self.recording_status = None
            self.recording_control_text = None
            self.recording_control_button = None

    def show_settings(self) -> None:
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return

        window = tk.Toplevel(self.root)
        window.title("Biscuit")
        apply_biscuit_icon(window)
        window.protocol("WM_DELETE_WINDOW", self.close_settings)
        window.attributes("-topmost", True)
        window.configure(bg=BLUE_BLACK, highlightthickness=0)
        window.geometry(SETTINGS_WINDOW_GEOMETRY)
        window.minsize(*SETTINGS_WINDOW_MINSIZE)
        self.settings_window = window
        self.settings_status = tk.StringVar(value="ready")
        self.test_output = tk.StringVar(value="Test transcript will appear here.")

        body = tk.Frame(window, bg=BLUE_BLACK, padx=30, pady=24)
        body.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(body, bg=BLUE_BLACK)
        header.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 20))
        tk.Frame(header, bg=YELLOW, width=5, height=28).pack(
            side=tk.LEFT, padx=(0, 12), pady=(2, 0)
        )
        tk.Label(header, text="Biscuit", fg=SURFACE_WHITE, bg=BLUE_BLACK, font=UI_FONT_TITLE).pack(
            side=tk.LEFT
        )
        tk.Frame(header, bg=CYAN, height=2).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(18, 0), pady=(16, 0)
        )

        self._label(body, "Model").grid(row=1, column=0, sticky="w", pady=7)
        self._entry(body, self.model_var).grid(
            row=1, column=1, sticky="ew", pady=7, ipady=6
        )
        tk.Button(
            body,
            text="Browse",
            command=self._browse_model,
            bg=GUNMETAL,
            fg=EDGE_WHITE,
            activebackground=PANEL,
            activeforeground=SURFACE_WHITE,
            relief=tk.FLAT,
            bd=0,
            font=UI_FONT,
            cursor="hand2",
        ).grid(
            row=1, column=2, sticky="ew", padx=(12, 0), pady=7, ipady=4
        )

        self._label(body, "Language").grid(row=2, column=0, sticky="w", pady=7)
        self._entry(body, self.language_var).grid(
            row=2, column=1, sticky="ew", pady=7, ipady=6
        )

        self._label(body, "Provider").grid(row=3, column=0, sticky="w", pady=7)
        self._entry(body, self.provider_var).grid(
            row=3, column=1, sticky="ew", pady=7, ipady=6
        )

        tk.Checkbutton(
            body,
            text=STARTUP_SETTING_LABEL,
            variable=self.run_at_login_var,
            bg=BLUE_BLACK,
            fg=EDGE_WHITE,
            activebackground=BLUE_BLACK,
            activeforeground=SURFACE_WHITE,
            selectcolor=PANEL_DEEP,
            font=UI_FONT,
            anchor="w",
            relief=tk.FLAT,
        ).grid(row=4, column=1, sticky="w", pady=(8, 2))

        controls = tk.Frame(body, bg=BLUE_BLACK)
        controls.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(18, 8))
        self._button(controls, SETTINGS_ACTION_LABELS["update"], self._update).pack(side=tk.LEFT, padx=(0, 8))
        self._button(controls, SETTINGS_ACTION_LABELS["test"], self._test, GREEN).pack(
            side=tk.LEFT, padx=8
        )
        self._button(controls, SETTINGS_ACTION_LABELS["stop"], self.settings_callbacks.on_kill, RED).pack(
            side=tk.LEFT, padx=8
        )
        self._button(controls, SETTINGS_ACTION_LABELS["save"], self._save, CYAN).pack(side=tk.RIGHT)

        status_band = tk.Frame(body, bg=PANEL_DEEP, padx=14, pady=9, highlightthickness=1, highlightbackground=CYAN)
        status_band.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        tk.Label(status_band, textvariable=self.settings_status, fg=EDGE_WHITE, bg=PANEL_DEEP, font=UI_FONT).pack(
            side=tk.LEFT
        )

        test_panel = tk.Frame(body, bg=PANEL_DEEP, padx=14, pady=10, highlightthickness=1, highlightbackground=PANEL)
        test_panel.grid(row=7, column=0, columnspan=3, sticky="nsew", pady=(12, 0))
        tk.Label(
            test_panel,
            textvariable=self.test_output,
            fg=TEXT,
            bg=PANEL_DEEP,
            font=UI_FONT,
            justify=tk.LEFT,
            anchor="nw",
            wraplength=620,
        ).pack(fill=tk.BOTH, expand=True)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(7, weight=1)

    def set_settings_status(self, status: str) -> None:
        if self.settings_status:
            self.settings_status.set(status)

    def set_test_output(self, text: str) -> None:
        if self.test_output:
            self.test_output.set(text)

    def close_settings(self) -> None:
        if self.settings_window:
            self.settings_window.destroy()
            self.settings_window = None
        if self.show_fallback_toolbar:
            self.root.withdraw()

    def _build_toolbar(self) -> None:
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=BLUE_BLACK, highlightthickness=1, highlightbackground=EDGE_WHITE)
        self.root.geometry("104x38+24+24")
        button = tk.Button(
            self.root,
            text="biscuit",
            command=self.show_settings,
            bg=BLUE_BLACK,
            fg=TEXT,
            activebackground=PANEL,
            activeforeground=TEXT,
            relief=tk.FLAT,
            bd=0,
            font=UI_FONT_BOLD,
            cursor="hand2",
        )
        button.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _activate_action(self, context: RightClickContext, on_biscuit: Callable[[RightClickContext], None]) -> None:
        self.close_action()
        on_biscuit(context)

    def _browse_model(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose Biscuit model",
            filetypes=[
                ("Local model", "*.bin *.gguf *.onnx *.pt *.tflite"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.model_var.set(path)

    def _save(self) -> None:
        self._apply_visible_settings()
        self.settings_callbacks.on_save(self.config)
        self.set_settings_status("saved")

    def _test(self) -> None:
        self._apply_visible_settings()
        self.settings_callbacks.on_test()

    def _apply_visible_settings(self) -> None:
        self.config.model_path = self.model_var.get().strip()
        self.config.language = self.language_var.get().strip() or "en"
        self.config.provider = self.provider_var.get().strip() or "auto"
        self.config.run_at_login = bool(self.run_at_login_var.get())

    def _update(self) -> None:
        status = self.settings_callbacks.on_update()
        self.model_var.set(self.config.model_path)
        self.language_var.set(self.config.language)
        self.provider_var.set(self.config.provider)
        self.set_settings_status(status)

    def _label(self, parent: tk.Misc, text: str) -> tk.Label:
        return tk.Label(parent, text=text, fg=EDGE_WHITE, bg=BLUE_BLACK, font=UI_FONT_BOLD)

    def _entry(self, parent: tk.Misc, textvariable: tk.StringVar) -> tk.Entry:
        return tk.Entry(
            parent,
            textvariable=textvariable,
            bg=PANEL_DEEP,
            fg=TEXT,
            insertbackground=YELLOW,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=PANEL,
            highlightcolor=CYAN,
            font=UI_FONT,
        )

    def _button(
        self,
        parent: tk.Misc,
        text: str,
        command: Callable[[], None],
        bg: str = PANEL,
    ) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=text_color_for_background(bg),
            activebackground=GUNMETAL,
            activeforeground=TEXT,
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=6,
            font=UI_FONT,
            cursor="hand2",
        )

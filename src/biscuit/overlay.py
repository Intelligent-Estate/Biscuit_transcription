"""Tkinter overlay surfaces for Biscuit."""

from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import filedialog
from typing import Callable

from .config import BiscuitConfig
from .win32_api import RightClickContext


BLUE_BLACK = "#07111f"
GUNMETAL = "#101b2d"
PANEL = "#17243a"
YELLOW = "#ffd23f"
CYAN = "#60d7ff"
RED = "#ff4d5e"
GREEN = "#55d488"
TEXT = "#edf4ff"
MUTED = "#8ea0b8"


@dataclass(slots=True)
class SettingsCallbacks:
    on_save: Callable[[BiscuitConfig], None]
    on_start: Callable[[], None]
    on_kill: Callable[[], None]
    on_update: Callable[[], str]


class BiscuitOverlay:
    def __init__(self, root: tk.Tk, config: BiscuitConfig, settings_callbacks: SettingsCallbacks):
        self.root = root
        self.config = config
        self.settings_callbacks = settings_callbacks
        self.action_window: tk.Toplevel | None = None
        self.recording_window: tk.Toplevel | None = None
        self.settings_window: tk.Toplevel | None = None
        self.recording_status: tk.StringVar | None = None
        self.settings_status: tk.StringVar | None = None
        self.model_var = tk.StringVar(value=config.model_path)
        self.language_var = tk.StringVar(value=config.language)
        self.provider_var = tk.StringVar(value=config.provider)
        self._build_toolbar()

    def show_action(self, context: RightClickContext, on_biscuit: Callable[[RightClickContext], None]) -> None:
        self.close_action()
        window = tk.Toplevel(self.root)
        window.overrideredirect(True)
        window.attributes("-topmost", True)
        window.configure(bg=YELLOW)
        window.geometry(f"150x38+{context.x + 8}+{context.y + 8}")
        self.action_window = window

        button = tk.Button(
            window,
            text="\U0001f399 biscuit",
            command=lambda: self._activate_action(context, on_biscuit),
            bg=BLUE_BLACK,
            fg=TEXT,
            activebackground=PANEL,
            activeforeground=YELLOW,
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=6,
            font=("Segoe UI", 10, "bold"),
        )
        button.pack(fill=tk.BOTH, expand=True, padx=0, pady=(4, 0))
        window.after(4500, self.close_action)

    def show_recording(self, on_stop: Callable[[], None]) -> None:
        self.close_recording()
        window = tk.Toplevel(self.root)
        window.overrideredirect(True)
        window.attributes("-topmost", True)
        window.configure(bg=YELLOW)
        window.geometry("+60+60")
        self.recording_window = window
        self.recording_status = tk.StringVar(value="recording")

        frame = tk.Frame(window, bg=BLUE_BLACK, padx=12, pady=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        tk.Label(frame, text="BISCUIT", fg=YELLOW, bg=BLUE_BLACK, font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        tk.Label(frame, textvariable=self.recording_status, fg=TEXT, bg=BLUE_BLACK).grid(
            row=1, column=0, sticky="w", pady=(2, 0)
        )
        tk.Button(
            frame,
            text="Stop",
            command=on_stop,
            bg=RED,
            fg="#ffffff",
            activebackground="#d63a49",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=12,
            pady=4,
        ).grid(row=0, column=1, rowspan=2, padx=(18, 0))

    def set_recording_status(self, status: str) -> None:
        if self.recording_status:
            self.recording_status.set(status)

    def close_action(self) -> None:
        if self.action_window:
            self.action_window.destroy()
            self.action_window = None

    def close_recording(self) -> None:
        if self.recording_window:
            self.recording_window.destroy()
            self.recording_window = None
            self.recording_status = None

    def show_settings(self) -> None:
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return

        window = tk.Toplevel(self.root)
        window.title("Biscuit")
        window.attributes("-topmost", True)
        window.configure(bg=BLUE_BLACK)
        window.geometry("540x315+120+120")
        window.minsize(500, 295)
        self.settings_window = window
        self.settings_status = tk.StringVar(value="ready")

        stripe = tk.Frame(window, height=5, bg=YELLOW)
        stripe.pack(fill=tk.X, side=tk.TOP)
        body = tk.Frame(window, bg=BLUE_BLACK, padx=18, pady=16)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(body, text="BISCUIT", fg=YELLOW, bg=BLUE_BLACK, font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 14)
        )

        self._label(body, "Model").grid(row=1, column=0, sticky="w", pady=6)
        tk.Entry(body, textvariable=self.model_var, bg=PANEL, fg=TEXT, insertbackground=YELLOW, relief=tk.FLAT).grid(
            row=1, column=1, sticky="ew", pady=6, ipady=5
        )
        tk.Button(body, text="Browse", command=self._browse_model, bg=GUNMETAL, fg=TEXT, relief=tk.FLAT).grid(
            row=1, column=2, sticky="ew", padx=(8, 0), pady=6
        )

        self._label(body, "Language").grid(row=2, column=0, sticky="w", pady=6)
        tk.Entry(body, textvariable=self.language_var, bg=PANEL, fg=TEXT, insertbackground=YELLOW, relief=tk.FLAT).grid(
            row=2, column=1, sticky="ew", pady=6, ipady=5
        )

        self._label(body, "Provider").grid(row=3, column=0, sticky="w", pady=6)
        tk.Entry(body, textvariable=self.provider_var, bg=PANEL, fg=TEXT, insertbackground=YELLOW, relief=tk.FLAT).grid(
            row=3, column=1, sticky="ew", pady=6, ipady=5
        )

        controls = tk.Frame(body, bg=BLUE_BLACK)
        controls.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(14, 4))
        self._button(controls, "Update", self._update).pack(side=tk.LEFT, padx=(0, 8))
        self._button(controls, "Start Biscuit", self.settings_callbacks.on_start, GREEN).pack(side=tk.LEFT, padx=8)
        self._button(controls, "Kill Biscuit", self.settings_callbacks.on_kill, RED).pack(side=tk.LEFT, padx=8)
        self._button(controls, "Save", self._save, CYAN).pack(side=tk.RIGHT)

        tk.Label(body, textvariable=self.settings_status, fg=MUTED, bg=BLUE_BLACK).grid(
            row=5, column=0, columnspan=3, sticky="w", pady=(12, 0)
        )
        body.columnconfigure(1, weight=1)

    def set_settings_status(self, status: str) -> None:
        if self.settings_status:
            self.settings_status.set(status)

    def _build_toolbar(self) -> None:
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=YELLOW)
        self.root.geometry("92x34+24+24")
        button = tk.Button(
            self.root,
            text="biscuit",
            command=self.show_settings,
            bg=BLUE_BLACK,
            fg=YELLOW,
            activebackground=PANEL,
            activeforeground=TEXT,
            relief=tk.FLAT,
            bd=0,
            font=("Segoe UI", 9, "bold"),
        )
        button.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

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
        self.config.model_path = self.model_var.get().strip()
        self.config.language = self.language_var.get().strip() or "en"
        self.config.provider = self.provider_var.get().strip() or "auto"
        self.settings_callbacks.on_save(self.config)
        self.set_settings_status("saved")

    def _update(self) -> None:
        status = self.settings_callbacks.on_update()
        self.model_var.set(self.config.model_path)
        self.language_var.set(self.config.language)
        self.provider_var.set(self.config.provider)
        self.set_settings_status(status)

    def _label(self, parent: tk.Misc, text: str) -> tk.Label:
        return tk.Label(parent, text=text, fg=MUTED, bg=BLUE_BLACK, font=("Segoe UI", 9))

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
            fg="#ffffff" if bg in {RED, GREEN} else TEXT,
            activebackground=GUNMETAL,
            activeforeground=YELLOW,
            relief=tk.FLAT,
            padx=12,
            pady=6,
        )

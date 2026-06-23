"""Biscuit application coordinator."""

from __future__ import annotations

from pathlib import Path
import threading
import traceback
import tkinter as tk

from .audio import Recorder, RecordingError
from .config import (
    BiscuitConfig,
    choose_best_model,
    default_config_path,
    discover_model_candidates,
    load_config,
    save_config,
)
from .overlay import BiscuitOverlay, SettingsCallbacks
from .tray import TrayCallbacks, TrayController
from .desktop import MouseHook, RightClickContext, get_foreground_context, send_escape, send_unicode_text
from .transcription import TranscriptionError, transcribe_audio


class BiscuitApp:
    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or default_config_path()
        self.config = load_config(self.config_path)
        self.root = tk.Tk()
        self.root.title("Biscuit")
        self.root.protocol("WM_DELETE_WINDOW", self.show_settings)
        self.recorder = Recorder(sample_rate=self.config.sample_rate)
        self.hook = MouseHook(self.on_right_click)
        self.tray = TrayController(
            TrayCallbacks(
                show_settings=lambda: self.root.after(0, self.show_settings),
                dictate_at_cursor=lambda: self.root.after(0, self.begin_recording_from_cursor),
                start_biscuit=lambda: self.root.after(0, self.start_biscuit),
                stop_biscuit=lambda: self.root.after(0, self.kill_biscuit),
                quit_app=lambda: self.root.after(0, self.quit_app),
            )
        )
        tray_available = self.tray.start()
        callbacks = SettingsCallbacks(
            on_save=self.save_settings,
            on_start=self.start_biscuit,
            on_kill=self.kill_biscuit,
            on_update=self.update_model_state,
        )
        self.overlay = BiscuitOverlay(self.root, self.config, callbacks, show_fallback_toolbar=not tray_available)
        self.last_context: RightClickContext | None = None

    def run(self) -> None:
        self.start_biscuit()
        self.root.mainloop()

    def show_settings(self) -> None:
        self.root.deiconify()
        self.overlay.show_settings()

    def quit_app(self) -> None:
        self.kill_biscuit()
        self.tray.stop()
        self.root.destroy()

    def start_biscuit(self) -> None:
        self.hook.start()
        status = "listening" if self.hook.running else "hook not active"
        self.overlay.set_settings_status(status)

    def kill_biscuit(self) -> None:
        self.hook.stop()
        self.overlay.close_action()
        self.overlay.close_recording()
        self.overlay.set_settings_status("stopped")

    def save_settings(self, config: BiscuitConfig) -> None:
        self.config = config
        save_config(self.config_path, self.config)
        self.recorder.sample_rate = self.config.sample_rate

    def update_model_state(self) -> str:
        if self.config.model_path and Path(self.config.model_path).exists():
            return "model ready"
        best = choose_best_model(discover_model_candidates())
        if best:
            self.config.model_path = str(best)
            save_config(self.config_path, self.config)
            return f"found {best.name}"
        return "choose a local model"

    def on_right_click(self, context: RightClickContext) -> None:
        self.last_context = context
        self.root.after(0, lambda: self.overlay.show_action(context, self.begin_recording))

    def begin_recording(self, context: RightClickContext) -> None:
        self.last_context = context
        send_escape()
        self.overlay.show_recording(context, self.stop_recording)
        try:
            self.recorder.start()
            self.overlay.set_recording_status("recording")
        except Exception as exc:
            self.overlay.set_recording_status(f"microphone error: {exc}")

    def begin_recording_from_cursor(self) -> None:
        self.begin_recording(get_foreground_context())

    def stop_recording(self) -> None:
        self.overlay.set_recording_status("processing")
        worker = threading.Thread(target=self._finish_recording, name="BiscuitTranscribe", daemon=True)
        worker.start()

    def _finish_recording(self) -> None:
        try:
            recording = self.recorder.stop()
            text = self._transcribe(recording.path)
            if not text:
                self._ui_status("no speech found")
                return
            context = self.last_context
            if context is None:
                self._copy_to_clipboard(text)
                self._ui_status("copied")
                return
            try:
                send_unicode_text(context.hwnd, text)
                self._ui_status("inserted")
            except Exception:
                self._copy_to_clipboard(text)
                self._ui_status("copied fallback")
        except (RecordingError, TranscriptionError, Exception) as exc:
            self._ui_status(f"error: {exc}")
            traceback.print_exc()
        finally:
            self.root.after(900, self.overlay.close_recording)

    def _transcribe(self, audio_path: Path) -> str:
        if not self.config.model_path:
            self.update_model_state()
        if not self.config.model_path:
            raise TranscriptionError("No local model selected.")
        return transcribe_audio(
            audio_path=audio_path,
            model_path=Path(self.config.model_path),
            language=self.config.language,
            provider=self.config.provider,
        )

    def _copy_to_clipboard(self, text: str) -> None:
        self.root.after(0, lambda: self._copy_on_ui_thread(text))

    def _copy_on_ui_thread(self, text: str) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def _ui_status(self, status: str) -> None:
        self.root.after(0, lambda: self.overlay.set_recording_status(status))


def main() -> None:
    BiscuitApp().run()

"""Biscuit application coordinator."""

from __future__ import annotations

from pathlib import Path
import socket
import sys
import threading
import traceback
import tkinter as tk
from collections.abc import Sequence

from .audio import Recorder, RecordingError
from .config import (
    DEFAULT_MODEL_SOURCE,
    BiscuitConfig,
    choose_best_model,
    default_config_path,
    discover_model_candidates,
    load_config,
    save_config,
)
from .overlay import BiscuitOverlay, SettingsCallbacks, apply_biscuit_icon
from .readiness import (
    check_insertion_readiness,
    check_invocation_readiness,
    check_microphone_readiness,
    check_model_readiness,
    summarize_readiness,
)
from .status import DictationOutcome, DictationResult, status_text
from .startup import is_run_at_login_enabled, sync_run_at_login
from .tray import TrayCallbacks, TrayController
from .release import release_self_check
from .desktop import (
    MouseHook,
    RightClickContext,
    get_foreground_context,
    restore_input_focus,
    send_escape,
    send_unicode_text,
)
from .transcription import TranscriptionError, transcribe_audio, warm_transcription_model
from .transcription import detect_provider


BISCUIT_HOST = "127.0.0.1"
BISCUIT_PORT = 47821
BISCUIT_DICTATE_MESSAGE = b"dictate\n"
ACTION_MENU_DELAY_MS = 140


def send_dictation_request(timeout: float = 0.25) -> bool:
    try:
        with socket.create_connection((BISCUIT_HOST, BISCUIT_PORT), timeout=timeout) as connection:
            connection.settimeout(timeout)
            connection.sendall(BISCUIT_DICTATE_MESSAGE)
            return connection.recv(16).strip() == b"ok"
    except OSError:
        return False


def choose_transcribable_model(paths: list[Path], provider: str) -> Path | None:
    remaining = list(paths)
    while remaining:
        candidate = choose_best_model(remaining) or remaining[0]
        try:
            detect_provider(provider, candidate)
            return candidate
        except TranscriptionError:
            remaining = [path for path in remaining if path != candidate]
    return None


def save_config_if_possible(config_path: Path, config: BiscuitConfig) -> bool:
    try:
        save_config(config_path, config)
        return True
    except OSError:
        return False


def insert_text_into_context(context: RightClickContext, text: str) -> int:
    if not text:
        return 0
    restore_input_focus(context)
    return send_unicode_text(context.hwnd, text)


def finish_dictation_result(recording, context, transcribe, insert, copy) -> DictationOutcome:
    try:
        text = transcribe(recording.path)
    except TranscriptionError as exc:
        return DictationOutcome(DictationResult.TRANSCRIPTION_ERROR, str(exc))
    if not text:
        return DictationOutcome(DictationResult.NO_SPEECH)
    if context is None:
        copy(text)
        return DictationOutcome(DictationResult.COPIED, "target unavailable")
    try:
        insert(context, text)
    except Exception:
        copy(text)
        return DictationOutcome(DictationResult.COPIED, "direct insertion blocked")
    return DictationOutcome(DictationResult.INSERTED)


def finish_test_dictation_result(recording, transcribe, insert=None, copy=None) -> tuple[DictationOutcome, str]:
    del insert, copy
    try:
        text = transcribe(recording.path)
    except TranscriptionError as exc:
        return DictationOutcome(DictationResult.TRANSCRIPTION_ERROR, str(exc)), ""
    if not text:
        return DictationOutcome(DictationResult.NO_SPEECH), ""
    return DictationOutcome(DictationResult.INSERTED, "test complete"), text


def is_hugging_face_model_id(source: str) -> bool:
    if "\\" in source or source.startswith(("/", ".")):
        return False
    if len(source) > 2 and source[1:3] == ":/":
        return False
    parts = source.split("/")
    return len(parts) == 2 and all(parts)


class BiscuitApp:
    def __init__(self, config_path: Path | None = None, exit_after_recording: bool = False):
        self.config_path = config_path or default_config_path()
        self.config = load_config(self.config_path)
        self.repo_root = Path(__file__).resolve().parents[2]
        if is_run_at_login_enabled():
            self.config.run_at_login = True
        self.exit_after_recording = exit_after_recording
        self.root = tk.Tk()
        self.root.title("Biscuit")
        apply_biscuit_icon(self.root)
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
            on_test=self.begin_test_recording,
            on_kill=self.kill_biscuit,
            on_update=self.update_model_state,
        )
        self.overlay = BiscuitOverlay(self.root, self.config, callbacks, show_fallback_toolbar=not tray_available)
        self.last_context: RightClickContext | None = None
        self._test_recording = False
        self._request_socket: socket.socket | None = None
        self._request_thread: threading.Thread | None = None
        self._warmup_thread: threading.Thread | None = None

    def run(self) -> None:
        self.start_request_server()
        self.start_biscuit()
        self.preload_transcription_model()
        self.root.mainloop()

    def run_dictation_once(self) -> None:
        self.root.after(0, self.begin_recording_from_cursor)
        self.root.mainloop()

    def show_settings(self) -> None:
        self.overlay.show_settings()

    def quit_app(self) -> None:
        self.stop_request_server()
        self.kill_biscuit()
        self.tray.stop()
        self.root.destroy()

    def start_biscuit(self) -> None:
        self.hook.start()
        self.overlay.set_settings_status(self.readiness_summary())

    def start_request_server(self) -> None:
        if self._request_socket is not None:
            return
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind((BISCUIT_HOST, BISCUIT_PORT))
            server.listen(4)
        except OSError:
            server.close()
            return
        self._request_socket = server
        self._request_thread = threading.Thread(target=self._serve_requests, name="BiscuitRequestServer", daemon=True)
        self._request_thread.start()

    def preload_transcription_model(self) -> None:
        if self._warmup_thread is not None and self._warmup_thread.is_alive():
            return
        self._warmup_thread = threading.Thread(target=self._warm_transcription_model, name="BiscuitWarmModel", daemon=True)
        self._warmup_thread.start()

    def _warm_transcription_model(self) -> None:
        try:
            if not self.config.model_path:
                self.config.model_path = DEFAULT_MODEL_SOURCE
            if not self._model_ready(self.config.model_path):
                self.update_model_state()
            if self.config.model_path and self._model_ready(self.config.model_path):
                warm_transcription_model(self.config.model_path, self.config.provider)
        except Exception:
            traceback.print_exc()

    def stop_request_server(self) -> None:
        if self._request_socket is not None:
            self._request_socket.close()
            self._request_socket = None

    def _serve_requests(self) -> None:
        while self._request_socket is not None:
            try:
                connection, _address = self._request_socket.accept()
            except OSError:
                break
            with connection:
                try:
                    data = connection.recv(64).strip()
                    if data == BISCUIT_DICTATE_MESSAGE.strip():
                        self.root.after(0, self.begin_recording_from_cursor)
                        connection.sendall(b"ok\n")
                    else:
                        connection.sendall(b"error\n")
                except OSError:
                    pass

    def kill_biscuit(self) -> None:
        self.hook.stop()
        self.overlay.close_action()
        self.overlay.close_recording()
        self.overlay.set_settings_status("stopped")

    def readiness_summary(self) -> str:
        states = [
            check_invocation_readiness(
                listener_running=self.hook.running,
                request_server_running=self._request_socket is not None,
                tray_available=self.tray.available,
            ),
            check_microphone_readiness(),
            check_model_readiness(self.config),
            check_insertion_readiness(self.last_context),
        ]
        return summarize_readiness(states)

    def save_settings(self, config: BiscuitConfig) -> None:
        self.config = config
        save_config(self.config_path, self.config)
        sync_run_at_login(self.config.run_at_login, getattr(self, "repo_root", Path(__file__).resolve().parents[2]))
        self.recorder.sample_rate = self.config.sample_rate

    def update_model_state(self) -> str:
        if self.config.model_path and self._model_ready(self.config.model_path):
            return "model ready"
        best = choose_transcribable_model(discover_model_candidates(), self.config.provider)
        if best:
            self.config.model_path = str(best)
            if save_config_if_possible(self.config_path, self.config):
                return f"found {best.name}"
            return f"found {best.name} (not saved)"
        self.config.model_path = DEFAULT_MODEL_SOURCE
        save_config_if_possible(self.config_path, self.config)
        return "using public model source"

    def on_right_click(self, context: RightClickContext) -> None:
        self.last_context = context
        self.root.after(ACTION_MENU_DELAY_MS, lambda: self.overlay.show_action(context, self.begin_recording))

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

    def begin_test_recording(self) -> None:
        self.last_context = None
        self._test_recording = True
        self.overlay.set_test_output("Recording test. Use the red Stop control when finished.")
        self.begin_recording(get_foreground_context())

    def stop_recording(self) -> None:
        self.overlay.set_recording_status("processing")
        worker = threading.Thread(target=self._finish_recording, name="BiscuitTranscribe", daemon=True)
        worker.start()

    def _finish_recording(self) -> None:
        test_recording = self._test_recording
        self._test_recording = False
        try:
            recording = self.recorder.stop()
            if test_recording:
                outcome, transcript = finish_test_dictation_result(recording=recording, transcribe=self._transcribe)
                self._ui_status(status_text(outcome))
                self._ui_test_output(transcript or status_text(outcome))
            else:
                outcome = finish_dictation_result(
                    recording=recording,
                    context=self.last_context,
                    transcribe=self._transcribe,
                    insert=insert_text_into_context,
                    copy=self._copy_to_clipboard,
                )
                self._ui_status(status_text(outcome))
        except RecordingError as exc:
            status = status_text(DictationOutcome(DictationResult.MICROPHONE_ERROR, str(exc)))
            self._ui_status(status)
            if test_recording:
                self._ui_test_output(status)
            traceback.print_exc()
        except Exception as exc:
            status = status_text(DictationOutcome(DictationResult.TRANSCRIPTION_ERROR, str(exc)))
            self._ui_status(status)
            if test_recording:
                self._ui_test_output(status)
            traceback.print_exc()
        finally:
            self.root.after(900, self.overlay.close_recording)
            if self.exit_after_recording:
                self.root.after(1200, self.quit_app)

    def _transcribe(self, audio_path: Path) -> str:
        if not self.config.model_path or not self._model_ready(self.config.model_path):
            self.update_model_state()
        if not self.config.model_path or not self._model_ready(self.config.model_path):
            raise TranscriptionError("No transcription model selected.")
        return transcribe_audio(
            audio_path=audio_path,
            model_path=self.config.model_path,
            language=self.config.language,
            provider=self.config.provider,
        )

    def _model_ready(self, model_path: str | Path) -> bool:
        source = str(model_path)
        if is_hugging_face_model_id(source):
            try:
                detect_provider(self.config.provider, None)
                return True
            except TranscriptionError:
                return False
        path = Path(source)
        if path.suffix and not path.exists():
            return False
        try:
            detect_provider(self.config.provider, path if path.exists() else None)
            return True
        except TranscriptionError:
            return False

    def _copy_to_clipboard(self, text: str) -> None:
        self.root.after(0, lambda: self._copy_on_ui_thread(text))

    def _copy_on_ui_thread(self, text: str) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def _ui_status(self, status: str) -> None:
        self.root.after(0, lambda: self.overlay.set_recording_status(status))

    def _ui_test_output(self, text: str) -> None:
        self.root.after(0, lambda: self.overlay.set_test_output(text))


def main(argv: Sequence[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--self-check" in args:
        ok, lines = release_self_check()
        for line in lines:
            print(line)
        raise SystemExit(0 if ok else 1)

    dictate_once = "--dictate-once" in args
    if dictate_once and send_dictation_request():
        return
    app = BiscuitApp(exit_after_recording=dictate_once)
    if dictate_once:
        app.run_dictation_once()
        return
    app.run()

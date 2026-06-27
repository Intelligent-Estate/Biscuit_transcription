"""User login startup integration for Biscuit."""

from __future__ import annotations

import os
from pathlib import Path


STARTUP_RELATIVE_PATH = Path("Microsoft") / "Windows" / "Start Menu" / "Programs" / "Startup" / "Biscuit.lnk"
STARTUP_SCRIPT_RELATIVE_PATH = Path("Microsoft") / "Windows" / "Start Menu" / "Programs" / "Startup" / "Biscuit.vbs"


def startup_shortcut_path(appdata: str | Path | None = None) -> Path:
    base = Path(appdata or os.environ.get("APPDATA", ""))
    return base / STARTUP_RELATIVE_PATH


def startup_script_path(appdata: str | Path | None = None) -> Path:
    base = Path(appdata or os.environ.get("APPDATA", ""))
    return base / STARTUP_SCRIPT_RELATIVE_PATH


def is_run_at_login_enabled(appdata: str | Path | None = None) -> bool:
    return startup_script_path(appdata).exists() or startup_shortcut_path(appdata).exists()


def sync_run_at_login(
    enabled: bool,
    repo_root: Path,
    *,
    appdata: str | Path | None = None,
) -> bool:
    script_path = startup_script_path(appdata)
    legacy_shortcut_path = startup_shortcut_path(appdata)
    if not enabled:
        changed = False
        for path in (script_path, legacy_shortcut_path):
            if path.exists():
                path.unlink()
                changed = True
        return changed

    launcher = repo_root / "Biscuit-Windows.vbs"
    if not launcher.exists():
        launcher = repo_root / "Biscuit-Windows.cmd"
    if not launcher.exists():
        raise FileNotFoundError(f"Missing Biscuit launcher: {launcher}")

    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(_startup_script(launcher, repo_root), encoding="utf-8")
    return True


def _startup_script(launcher: Path, repo_root: Path) -> str:
    return "\n".join(
        [
            'Set shell = CreateObject("WScript.Shell")',
            f'shell.CurrentDirectory = "{_vbs_escape(repo_root)}"',
            f'shell.Run """" & "{_vbs_escape(launcher)}" & """" , 0, False',
            "",
        ]
    )


def _vbs_escape(path: Path) -> str:
    return str(path).replace('"', '""')

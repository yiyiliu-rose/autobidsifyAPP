"""
main.py
=======

AutoBIDSify ExecVal Desktop — application entry point.

Renders an HTML/CSS/JS interface inside the OS-native WebView via pywebview
(Edge WebView2 on Windows, WebKit on macOS, WebKitGTK on Linux). No browser
engine is bundled, keeping the packaged app small.

The trimmed autobidsify library lives under execval/vendor/autobidsify and is
added to sys.path below so `import autobidsify` resolves to it.
"""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path
from typing import List, Optional


def _base_dir() -> Path:
    """Directory containing this file's resources, in dev and when frozen."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


# Make the vendored autobidsify importable before importing worker.
_VENDOR = _base_dir() / "vendor"
if str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

import webview  # noqa: E402

import bundle  # noqa: E402
import worker  # noqa: E402


def _asset_dir() -> Path:
    return _base_dir() / "web"


class Api:
    """Methods exposed to the frontend JavaScript via the pywebview bridge."""

    def __init__(self) -> None:
        self._window: Optional[webview.Window] = None
        self._busy: bool = False

    def bind_window(self, window: webview.Window) -> None:
        self._window = window

    # -- file / folder pickers --
    def pick_files(self) -> List[str]:
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG, allow_multiple=True
        )
        return list(result) if result else []

    def pick_folder(self) -> Optional[str]:
        result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        return result[0] if result else None

    # -- plan bundle resolution --
    def resolve_bundle(self, paths: List[str]) -> dict:
        result = bundle.resolve_bundle([Path(p) for p in paths])
        return {
            "found": {k: str(v) for k, v in result.found.items()},
            "missing_required": result.missing_required,
            "missing_optional": result.missing_optional,
            "is_complete": result.is_complete,
        }

    # -- run pipeline --
    def run_pipeline(self, payload: dict) -> dict:
        if self._busy:
            return {"started": False, "reason": "already running"}
        self._busy = True
        t = threading.Thread(target=self._run_worker, args=(payload,), daemon=True)
        t.start()
        return {"started": True}

    def open_output(self, path: str) -> None:
        target = str(path)
        try:
            if sys.platform.startswith("win"):
                import os
                os.startfile(target)  # noqa: SIM115
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", target])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", target])
        except Exception:  # noqa: BLE001
            pass

    # -- internal --
    def _run_worker(self, payload: dict) -> None:
        self._set_state("running")
        resolver = None
        try:
            bundle_paths = [Path(p) for p in payload.get("bundle_paths", [])]
            input_dir = Path(payload["input_dir"])
            output_dir = Path(payload["output_dir"])
            do_validate = bool(payload.get("validate", True))

            resolver = bundle.BundleResolver()
            resolved = resolver.resolve(bundle_paths)
            found = {k: str(v) for k, v in resolved.found.items()}

            code = worker.run(
                found=found,
                input_root=input_dir,
                output_dir=output_dir,
                do_validate=do_validate,
                log=self._push_log,
            )
            self._set_state("done" if code == 0 else "error")
        except Exception as e:  # noqa: BLE001
            self._push_log(f"[FATAL] {e}")
            self._set_state("error")
        finally:
            if resolver is not None:
                resolver.cleanup()
            self._busy = False

    def _push_log(self, line: str) -> None:
        if self._window:
            self._window.evaluate_js(f"window.appendLog({json.dumps(line)})")

    def _set_state(self, state: str) -> None:
        if self._window:
            self._window.evaluate_js(f"window.setState({json.dumps(state)})")


def main() -> None:
    api = Api()
    window = webview.create_window(
        title="AutoBIDSify",
        url=str(_asset_dir() / "index.html"),
        js_api=api,
        width=940,
        height=860,
        min_size=(820, 720),
    )
    api.bind_window(window)
    webview.start()


if __name__ == "__main__":
    main()
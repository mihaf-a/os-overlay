"""Platform specific backends for system level services."""

from __future__ import annotations

import os
import sys

from .base import HotkeyBackend


def create_hotkey_backend() -> HotkeyBackend:
    """Return the hotkey backend that matches the current platform."""
    if os.environ.get("OS_OVERLAY_NO_HOTKEYS", "").strip().lower() in ("1", "true", "yes"):
        from .stub import NullHotkeyBackend

        return NullHotkeyBackend()
    if sys.platform == "win32":
        from .windows import WindowsHotkeyBackend

        return WindowsHotkeyBackend()
    from .stub import NullHotkeyBackend

    return NullHotkeyBackend()


__all__ = ["HotkeyBackend", "create_hotkey_backend"]

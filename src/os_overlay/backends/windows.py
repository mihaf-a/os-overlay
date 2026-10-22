"""Windows backend for system-wide hotkeys built on the Win32 RegisterHotKey API."""

from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes
from typing import Callable

from PySide6.QtCore import QAbstractNativeEventFilter, Qt
from PySide6.QtGui import QWindow
from PySide6.QtWidgets import QApplication

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312

ERROR_ACCESS_DENIED = 5
ERROR_INVALID_PARAMETER = 87
ERROR_HOTKEY_ALREADY_REGISTERED = 1409

MODIFIER_FLAGS: dict[str, int] = {
    "Alt": MOD_ALT,
    "Ctrl": MOD_CONTROL,
    "Shift": MOD_SHIFT,
    "Win": MOD_WIN,
}


def _build_vk_codes() -> dict[str, int]:
    """Return the virtual key code table used when registering hotkeys."""
    codes: dict[str, int] = {
        "Backspace": 0x08,
        "Tab": 0x09,
        "Enter": 0x0D,
        "Pause": 0x13,
        "CapsLock": 0x14,
        "Escape": 0x1B,
        "Space": 0x20,
        "PageUp": 0x21,
        "PageDown": 0x22,
        "End": 0x23,
        "Home": 0x24,
        "Left": 0x25,
        "Up": 0x26,
        "Right": 0x27,
        "Down": 0x28,
        "Print": 0x2A,
        "Insert": 0x2B,
        "Delete": 0x2C,
        "LWin": 0x5B,
        "RWin": 0x5C,
        "Apps": 0x5D,
        "Sleep": 0x5F,
        "NumLock": 0x90,
        "ScrollLock": 0x91,
        ";": 0xBA,
        "=": 0xBB,
        "+": 0xBB,
        ",": 0xBC,
        "-": 0xBD,
        ".": 0xBE,
        "/": 0xBF,
        "`": 0xC0,
        "[": 0xDB,
        "\\": 0xDC,
        "]": 0xDD,
        "'": 0xDE,
        "Mouse1": 0x01,
        "Mouse2": 0x02,
        "Mouse3": 0x04,
        "Mouse4": 0x05,
        "Mouse5": 0x06,
        "NumMultiply": 0x6A,
        "NumAdd": 0x6B,
        "NumSubtract": 0x6D,
        "NumDecimal": 0x6E,
        "NumDivide": 0x6F,
    }
    for index in range(26):
        codes[chr(ord("A") + index)] = 0x41 + index
    for index in range(10):
        codes[str(index)] = 0x30 + index
        codes[f"Num{index}"] = 0x60 + index
    for index in range(1, 25):
        codes[f"F{index}"] = 0x6F + index
    return codes


VK_CODES: dict[str, int] = _build_vk_codes()


def describe_error(code: int) -> str:
    """Return a readable explanation for a Windows error code."""
    if code == ERROR_HOTKEY_ALREADY_REGISTERED:
        return "This shortcut is already used by another program."
    if code == ERROR_INVALID_PARAMETER:
        return "Windows rejected this shortcut combination."
    if code == ERROR_ACCESS_DENIED:
        return "Access denied while registering the shortcut."
    formatter = getattr(ctypes, "FormatError", None)
    if formatter is not None:
        try:
            message = formatter(code).strip()
        except OSError:
            message = ""
        if message:
            return message
    return f"Windows error {code}."


class HotkeyAnchor(QWindow):
    """Hidden native window that receives the WM_HOTKEY messages we register."""

    def __init__(self) -> None:
        super().__init__()
        self.setFlags(Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        self.create()


class WindowsHotkeyBackend(QAbstractNativeEventFilter):
    """Registers global hotkeys and dispatches their activation callbacks."""

    def __init__(self) -> None:
        super().__init__()
        self._anchor = HotkeyAnchor()
        self._hwnd = int(self._anchor.winId())
        self._next_id = 0xB000
        self._callbacks: dict[int, Callable[[], None]] = {}
        self._last_fired: dict[int, float] = {}
        self._installed = False
        self._install_filter()

    def _install_filter(self) -> None:
        """Attach the filter to the application so the messages reach us."""
        if self._installed:
            return
        application = QApplication.instance()
        if application is None:
            return
        application.installNativeEventFilter(self)
        self._installed = True

    def register(
        self, modifiers: frozenset[str], key: str, callback: Callable[[], None]
    ) -> str | None:
        """Register a system-wide hotkey, returning an error message on failure."""
        if sys.platform != "win32":
            return "Global hotkeys are only available on Windows."
        self._install_filter()
        virtual_key = VK_CODES.get(key)
        if virtual_key is None:
            return f"Windows does not support the key '{key}'."
        flags = MOD_NOREPEAT
        for modifier in modifiers:
            flags |= MODIFIER_FLAGS.get(modifier, 0)

        hotkey_id = self._next_id
        self._next_id += 1
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        if not user32.RegisterHotKey(wintypes.HWND(self._hwnd), hotkey_id, flags, virtual_key):
            return describe_error(ctypes.get_last_error())
        self._callbacks[hotkey_id] = callback
        return None

    def unregister_all(self) -> None:
        """Remove every hotkey registered through this backend."""
        if not self._callbacks:
            return
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        for hotkey_id in list(self._callbacks):
            user32.UnregisterHotKey(wintypes.HWND(self._hwnd), hotkey_id)
        self._callbacks.clear()
        self._last_fired.clear()

    def nativeEventFilter(self, event_type, message):  # Qt naming convention.
        """Route WM_HOTKEY messages to the matching activation callback."""
        try:
            kind = bytes(event_type)
        except (TypeError, ValueError):
            return False, 0
        if kind not in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            return False, 0
        try:
            native = wintypes.MSG.from_address(int(message))
        except (TypeError, ValueError):
            return False, 0
        if native.message != WM_HOTKEY:
            return False, 0

        hotkey_id = int(native.wParam)
        callback = self._callbacks.get(hotkey_id)
        if callback is None:
            return False, 0

        now = time.monotonic()
        if now - self._last_fired.get(hotkey_id, 0.0) < 0.03:
            return True, 0
        self._last_fired[hotkey_id] = now
        callback()
        return True, 0


__all__ = ["VK_CODES", "HotkeyAnchor", "WindowsHotkeyBackend", "describe_error"]

"""Tests for the hotkey binding parser, formatter and the Windows backend."""

from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes

import pytest

from os_overlay.core.hotkeys import (
    HotkeyBinding,
    format_binding,
    normalize_key,
    parse_binding,
)


def test_parse_modifiers_and_key():
    binding = parse_binding("Ctrl+Alt+H")

    assert binding == HotkeyBinding(frozenset({"Ctrl", "Alt"}), "H")


def test_parse_is_case_insensitive():
    assert parse_binding("ctrl+alt+h") == parse_binding("Ctrl+Alt+H")


def test_parse_accepts_aliases():
    binding = parse_binding("Control+Option+Esc")

    assert binding is not None
    assert binding.modifiers == frozenset({"Ctrl", "Alt"})
    assert binding.key == "Escape"


def test_parse_reads_the_plus_key():
    binding = parse_binding("Ctrl++")

    assert binding is not None
    assert binding.key == "+"
    assert binding.modifiers == frozenset({"Ctrl"})


def test_parse_reads_a_trailing_plus_key():
    binding = parse_binding("Ctrl+")

    assert binding is not None
    assert binding.key == "+"


@pytest.mark.parametrize("text", ["", "   ", "Ctrl+Shift"])
def test_parse_rejects_incomplete_bindings(text):
    assert parse_binding(text) is None


def test_parse_rejects_unknown_keys():
    assert parse_binding("Ctrl+NotAKey") is None


def test_normalize_key_supports_function_keys():
    assert normalize_key("f7") == "F7"
    assert normalize_key("f24") == "F24"
    assert normalize_key("f25") is None


def test_normalize_key_supports_numpad():
    assert normalize_key("num5") == "Num5"
    assert normalize_key("numlock") == "NumLock"


def test_format_uses_a_fixed_modifier_order():
    assert format_binding({"Shift", "Ctrl"}, "H") == "Ctrl+Shift+H"
    assert format_binding({"Win", "Alt", "Ctrl", "Shift"}, "K") == "Ctrl+Alt+Shift+Win+K"


def test_binding_str_round_trips():
    binding = parse_binding("Ctrl+Alt+M")

    assert binding is not None
    assert parse_binding(str(binding)) == binding


@pytest.mark.skipif(sys.platform != "win32", reason="The hotkey backend is Windows only")
def test_the_backend_is_installed_as_a_native_event_filter(qt_app):
    from os_overlay.backends.windows import WindowsHotkeyBackend

    backend = WindowsHotkeyBackend()

    assert backend._installed is True


@pytest.mark.skipif(sys.platform != "win32", reason="The hotkey backend is Windows only")
def test_a_hotkey_message_reaches_the_callback(qt_app):
    from os_overlay.backends.windows import WM_HOTKEY, WindowsHotkeyBackend

    if qt_app.platformName() != "windows":
        pytest.skip("A real window handle is needed to receive hotkey messages.")

    backend = WindowsHotkeyBackend()
    fired: list[bool] = []
    error = backend.register(frozenset({"Ctrl", "Alt", "Shift"}), "F9", lambda: fired.append(True))

    assert error is None
    hotkey_id = next(iter(backend._callbacks))
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.PostMessageW(
        wintypes.HWND(backend._hwnd),
        WM_HOTKEY,
        wintypes.WPARAM(hotkey_id),
        wintypes.LPARAM(0),
    )

    deadline = time.monotonic() + 3.0
    while not fired and time.monotonic() < deadline:
        qt_app.processEvents()
        time.sleep(0.01)

    backend.unregister_all()
    assert fired


@pytest.mark.skipif(sys.platform != "win32", reason="The hotkey backend is Windows only")
def test_a_conflicting_shortcut_is_reported(qt_app, data_home):
    from os_overlay.core.controller import Controller

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    if not user32.RegisterHotKey(None, 0x7777, 0x0002 | 0x0001, ord("H")):
        pytest.skip("The shortcut is already taken on this machine.")
    try:
        controller = Controller()
    finally:
        user32.UnregisterHotKey(None, 0x7777)

    assert "toggle" in controller.hotkey_error_map
    assert "toggle" not in controller.hotkeys.bindings

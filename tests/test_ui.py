"""Tests for the control panel wiring."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt

from os_overlay.core.controller import Controller
from os_overlay.ui.main_window import MainWindow


def _collect_errors(monkeypatch) -> list:
    errors: list = []
    monkeypatch.setattr(sys, "excepthook", lambda *args: errors.append(args[1]))
    return errors


def test_the_panel_builds_without_errors(qt_app, data_home, monkeypatch):
    errors = _collect_errors(monkeypatch)

    controller = Controller()
    window = MainWindow(controller)
    window.show()

    assert not errors


def test_signals_are_handled_without_errors(qt_app, data_home, monkeypatch):
    errors = _collect_errors(monkeypatch)

    controller = Controller()
    window = MainWindow(controller)
    window.show()

    controller.profile_changed.emit()
    controller.active_profile_changed.emit(controller.active_profile)
    controller.profiles_changed.emit()
    controller.enabled_changed.emit(False)
    controller.move_mode_changed.emit(True)
    controller.status_message.emit("A status message.")
    controller.settings_changed.emit()
    controller.hotkey_errors.emit({"toggle": "This shortcut is already used."})

    assert not errors


def test_toggling_the_crosshair_updates_the_overlay(qt_app, data_home):
    controller = Controller()
    MainWindow(controller)

    assert controller.enabled is True
    controller.toggle_enabled()
    assert controller.enabled is False
    controller.toggle_enabled()
    assert controller.enabled is True


def test_the_stored_enabled_state_is_applied_on_start(qt_app, data_home):
    controller = Controller()
    assert controller.enabled is True

    controller.toggle_enabled()
    controller.save_settings()

    second = Controller()

    assert second.enabled is False


def test_the_panel_keeps_its_size_when_something_else_resizes_it(qt_app, data_home):
    controller = Controller()
    window = MainWindow(controller)
    window.show()
    qt_app.processEvents()
    expected = window.size()

    window.resize(1400, 1000)
    qt_app.processEvents()

    assert window.size() == expected


def test_the_panel_keeps_its_position_when_something_else_moves_it(qt_app, data_home):
    controller = Controller()
    window = MainWindow(controller)
    window.show()
    qt_app.processEvents()
    expected = window.geometry()

    window.move(expected.x() + 300, expected.y() + 200)
    qt_app.processEvents()

    assert window.geometry() == expected


def test_the_panel_is_a_floating_tool_window(qt_app, data_home):
    controller = Controller()
    window = MainWindow(controller)

    assert window.windowFlags() & Qt.Tool

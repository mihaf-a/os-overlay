"""Shared pytest fixtures for the os-overlay test suite."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# The tests never claim a global shortcut, so they cannot steal one from the user.
os.environ.setdefault("OS_OVERLAY_NO_HOTKEYS", "1")


@pytest.fixture(scope="session")
def qt_app():
    """Provide a headless Qt application for the tests that need one."""
    from PySide6.QtWidgets import QApplication

    application = QApplication.instance() or QApplication([])
    return application


@pytest.fixture
def data_home(tmp_path, monkeypatch):
    """Point the application data directory at a temporary folder."""
    home = tmp_path / "appdata"
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("OS_OVERLAY_HOME", str(home))
    return home

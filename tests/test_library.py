"""Tests for the settings storage and the profile library helpers."""

from __future__ import annotations

from PySide6.QtGui import QImage

from os_overlay.core.library import export_profile_file, import_asset, import_profile_file
from os_overlay.paths import resolve_asset_path
from os_overlay.profile import Profile
from os_overlay.settings import HotkeyMap, Settings, load_settings, save_settings


def test_settings_round_trip():
    settings = Settings()
    settings.hotkeys.toggle = "Ctrl+Alt+J"
    settings.overlay.click_through = False
    settings.crosshair_enabled = False
    settings.active_profile = "abc"

    restored = Settings.from_dict(settings.to_dict())

    assert restored.hotkeys.toggle == "Ctrl+Alt+J"
    assert restored.overlay.click_through is False
    assert restored.crosshair_enabled is False
    assert restored.active_profile == "abc"


def test_hotkey_map_defaults():
    hotkeys = HotkeyMap()

    assert hotkeys.toggle == "Ctrl+Alt+H"
    assert hotkeys.panel == "Ctrl+Alt+O"
    assert hotkeys.get("move_mode") == "Ctrl+Alt+M"


def test_hotkey_map_ignores_unknown_actions():
    hotkeys = HotkeyMap()
    hotkeys.set("unknown_action", "Ctrl+Alt+Z")

    assert hotkeys.get("unknown_action") == ""


def test_settings_are_saved_to_the_data_directory(data_home):
    settings = Settings()
    settings.hotkeys.toggle = "Ctrl+Alt+K"
    save_settings(settings)

    loaded = load_settings()

    assert loaded.hotkeys.toggle == "Ctrl+Alt+K"


def test_missing_settings_return_the_defaults(data_home):
    assert load_settings().hotkeys.toggle == HotkeyMap().toggle


def test_profile_export_and_import_round_trip(tmp_path):
    profile = Profile(name="Exported")
    profile.style.color = "#abcdef"
    profile.style.shape = "circle"
    target = tmp_path / "export" / "exported.json"

    export_profile_file(profile, target)

    assert target.exists()
    restored = import_profile_file(target)
    assert restored is not None
    assert restored.name == "Exported"
    assert restored.style.color == "#abcdef"
    assert restored.style.shape == "circle"


def test_importing_an_invalid_profile_returns_none(tmp_path):
    broken = tmp_path / "broken.json"
    broken.write_text("not json", encoding="utf-8")

    assert import_profile_file(broken) is None


def test_import_asset_copies_the_file_into_the_library(data_home, qt_app):
    source = data_home / "source.png"
    image = QImage(8, 8, QImage.Format_ARGB32)
    image.fill(0)
    image.save(str(source))

    reference = import_asset(source)

    assert reference
    stored = resolve_asset_path(reference)
    assert stored.exists()
    assert stored.parent == data_home / "assets"

"""Tests for the profile model and its JSON representation."""

from __future__ import annotations

from os_overlay.profile import Profile, Style


def test_round_trip_preserves_values():
    profile = Profile(name="Sample")
    profile.style.color = "#123456"
    profile.style.thickness = 5
    profile.style.shape = "circle"
    profile.image.path = "assets/example.gif"
    profile.position.x = 0.25
    profile.position.y = 0.75

    restored = Profile.from_dict(profile.to_dict())

    assert restored.name == "Sample"
    assert restored.style.color == "#123456"
    assert restored.style.thickness == 5
    assert restored.style.shape == "circle"
    assert restored.image.path == "assets/example.gif"
    assert restored.position.x == 0.25
    assert restored.position.y == 0.75


def test_unknown_keys_are_ignored():
    profile = Profile.from_dict(
        {"name": "Unknown", "extra": 1, "style": {"color": "#ff0000", "bogus": 2}}
    )

    assert profile.name == "Unknown"
    assert profile.style.color == "#ff0000"


def test_invalid_values_fall_back_to_defaults():
    default = Style()
    style = Style.from_dict(
        {"color": "not-a-color", "thickness": "thick", "opacity": 5, "shape": "blob"}
    )

    assert style.color == default.color
    assert style.thickness == default.thickness
    assert style.opacity == 1.0
    assert style.shape == default.shape


def test_screen_zero_is_preserved():
    profile = Profile.from_dict({"name": "First", "screen": 0})

    assert profile.screen == "0"


def test_duplicate_keeps_the_style_but_changes_identity():
    profile = Profile(name="Original")
    profile.style.color = "#00ff00"

    clone = profile.duplicate()

    assert clone.id != profile.id
    assert clone.name == "Original copy"
    assert clone.style.color == "#00ff00"


def test_to_dict_is_json_serialisable():
    import json

    payload = json.dumps(Profile(name="Serialisable").to_dict())

    assert "Serialisable" in payload

"""Built-in crosshair presets shipped with the application."""

from __future__ import annotations

from typing import Any

from .profile import Profile, Style, list_profiles, save_profile

PRESETS: tuple[dict[str, Any], ...] = (
    {
        "name": "Classic Dot",
        "style": {
            "mode": "shape",
            "shape": "dot",
            "color": "#00ff66",
            "thickness": 3,
            "dot": True,
            "dot_size": 3,
            "outline": True,
            "outline_width": 1,
            "gap": 0,
            "length": 0,
        },
    },
    {
        "name": "Precision Dot",
        "style": {
            "mode": "shape",
            "shape": "dot",
            "color": "#ff3b3b",
            "thickness": 2,
            "dot": True,
            "dot_size": 2,
            "outline": True,
            "outline_width": 1,
            "gap": 0,
            "length": 0,
        },
    },
    {
        "name": "Cross",
        "style": {
            "mode": "shape",
            "shape": "cross",
            "color": "#00ff66",
            "thickness": 2,
            "length": 9,
            "gap": 4,
            "dot": False,
            "outline": True,
            "outline_width": 1,
        },
    },
    {
        "name": "Precision Cross",
        "style": {
            "mode": "shape",
            "shape": "cross",
            "color": "#00e5ff",
            "thickness": 1,
            "length": 11,
            "gap": 5,
            "dot": True,
            "dot_size": 2,
            "outline": True,
            "outline_color": "#000000",
            "outline_width": 1,
        },
    },
    {
        "name": "Fine Cross",
        "style": {
            "mode": "shape",
            "shape": "cross",
            "color": "#ffffff",
            "thickness": 1,
            "length": 14,
            "gap": 6,
            "dot": False,
            "outline": False,
        },
    },
    {
        "name": "Chunky Cross",
        "style": {
            "mode": "shape",
            "shape": "cross",
            "color": "#ffd400",
            "thickness": 4,
            "length": 8,
            "gap": 3,
            "dot": False,
            "outline": True,
            "outline_color": "#000000",
            "outline_width": 2,
        },
    },
    {
        "name": "Long Cross",
        "style": {
            "mode": "shape",
            "shape": "cross",
            "color": "#00ff66",
            "thickness": 2,
            "length": 18,
            "gap": 8,
            "dot": False,
            "outline": True,
            "outline_width": 1,
        },
    },
    {
        "name": "Circle",
        "style": {
            "mode": "shape",
            "shape": "circle",
            "color": "#00ff66",
            "thickness": 2,
            "dot": False,
            "outline": True,
            "outline_width": 1,
        },
    },
    {
        "name": "Square",
        "style": {
            "mode": "shape",
            "shape": "square",
            "color": "#ffffff",
            "thickness": 2,
            "dot": False,
            "outline": True,
            "outline_color": "#000000",
            "outline_width": 1,
        },
    },
    {
        "name": "T-Square",
        "style": {
            "mode": "shape",
            "shape": "t-square",
            "color": "#00ff66",
            "thickness": 2,
            "length": 10,
            "gap": 3,
            "dot": False,
            "outline": True,
            "outline_width": 1,
        },
    },
    {
        "name": "Gap Cross",
        "style": {
            "mode": "shape",
            "shape": "gap-cross",
            "color": "#ff9f1c",
            "thickness": 2,
            "length": 12,
            "gap": 6,
            "dot": True,
            "dot_size": 2,
            "outline": True,
            "outline_color": "#000000",
            "outline_width": 1,
        },
    },
    {
        "name": "Brackets",
        "style": {
            "mode": "shape",
            "shape": "bracket",
            "color": "#ffffff",
            "thickness": 2,
            "length": 8,
            "gap": 8,
            "dot": False,
            "outline": True,
            "outline_color": "#000000",
            "outline_width": 1,
        },
    },
    {
        "name": "Minimal",
        "style": {
            "mode": "shape",
            "shape": "dot",
            "color": "#ffffff",
            "thickness": 1,
            "dot": True,
            "dot_size": 1,
            "outline": False,
            "gap": 0,
            "length": 0,
        },
    },
    {
        "name": "Magenta T-Square",
        "style": {
            "mode": "shape",
            "shape": "t-square",
            "color": "#ff00d4",
            "thickness": 2,
            "length": 12,
            "gap": 4,
            "dot": False,
            "outline": True,
            "outline_color": "#000000",
            "outline_width": 1,
        },
    },
)


def seed_default_profiles() -> None:
    """Create the built-in presets the first time the application runs."""
    if list_profiles():
        return
    for profile in built_in_profiles():
        save_profile(profile)


def built_in_profiles() -> list[Profile]:
    """Return the built-in presets as ready to use profiles."""
    profiles: list[Profile] = []
    for entry in PRESETS:
        style = Style.from_dict(entry.get("style", {}))
        profile = Profile(name=entry["name"], style=style)
        profiles.append(profile)
    return profiles

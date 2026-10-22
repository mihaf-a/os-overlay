"""Filesystem locations for settings, profiles and imported assets."""

from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "os-overlay"
HOME_ENV = "OS_OVERLAY_HOME"


def config_dir() -> Path:
    """Return the root data directory, honouring the portable-mode override."""
    override = os.environ.get(HOME_ENV)
    if override:
        return Path(override).expanduser().resolve()
    base = os.environ.get("APPDATA")
    root = Path(base) if base else Path.home() / ".config"
    return root / APP_NAME


def profiles_dir() -> Path:
    """Return the directory holding saved profile JSON files."""
    return config_dir() / "profiles"


def assets_dir() -> Path:
    """Return the directory holding imported image and animation assets."""
    return config_dir() / "assets"


def settings_path() -> Path:
    """Return the path of the application settings file."""
    return config_dir() / "settings.json"


def ensure_dirs() -> None:
    """Create the data directories if they do not exist yet."""
    for directory in (config_dir(), profiles_dir(), assets_dir()):
        directory.mkdir(parents=True, exist_ok=True)


def relative_asset_path(path: Path) -> str:
    """Return an asset path relative to the data directory for portable profiles."""
    try:
        return path.resolve().relative_to(config_dir()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def resolve_asset_path(reference: str) -> Path:
    """Resolve a stored asset reference back to an absolute path."""
    candidate = Path(reference)
    if candidate.is_absolute():
        return candidate
    return config_dir() / candidate

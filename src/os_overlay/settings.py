"""Application settings: hotkey bindings, overlay options and window state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .paths import settings_path
from .storage import read_json, write_json

SCHEMA = "os-overlay/settings@1"

HOTKEY_ACTIONS: tuple[tuple[str, str], ...] = (
    ("toggle", "Toggle crosshair"),
    ("panel", "Show / hide panel"),
    ("move_mode", "Move mode"),
    ("profile_prev", "Previous profile"),
    ("profile_next", "Next profile"),
)


@dataclass
class HotkeyMap:
    """Global hotkey bindings keyed by action name."""

    toggle: str = "Ctrl+Alt+H"
    panel: str = "Ctrl+Alt+O"
    move_mode: str = "Ctrl+Alt+M"
    profile_prev: str = "Ctrl+Alt+["
    profile_next: str = "Ctrl+Alt+]"

    def to_dict(self) -> dict[str, str]:
        """Return the JSON representation of this binding map."""
        return {key: getattr(self, key) for key, _ in HOTKEY_ACTIONS}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HotkeyMap:
        """Build a binding map from JSON data."""
        defaults = cls()
        return cls(
            **{key: str(data.get(key) or getattr(defaults, key)) for key, _ in HOTKEY_ACTIONS}
        )

    def get(self, action: str) -> str:
        """Return the binding registered for an action."""
        return str(getattr(self, action, ""))

    def set(self, action: str, binding: str) -> None:
        """Assign a binding to an action."""
        if action in dict(HOTKEY_ACTIONS):
            setattr(self, action, binding)


@dataclass
class OverlayOptions:
    """Behaviour flags for the on-screen overlay."""

    always_on_top: bool = True
    show_on_all_screens: bool = False
    click_through: bool = True

    def to_dict(self) -> dict[str, bool]:
        """Return the JSON representation of these options."""
        return {
            "always_on_top": self.always_on_top,
            "show_on_all_screens": self.show_on_all_screens,
            "click_through": self.click_through,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OverlayOptions:
        """Build overlay options from JSON data."""
        defaults = cls()
        return cls(
            always_on_top=bool(data.get("always_on_top", defaults.always_on_top)),
            show_on_all_screens=bool(data.get("show_on_all_screens", defaults.show_on_all_screens)),
            click_through=bool(data.get("click_through", defaults.click_through)),
        )


@dataclass
class Settings:
    """Everything the application remembers between sessions."""

    active_profile: str = ""
    crosshair_enabled: bool = True
    hotkeys: HotkeyMap = field(default_factory=HotkeyMap)
    overlay: OverlayOptions = field(default_factory=OverlayOptions)
    minimize_to_tray: bool = True
    nudge_step: int = 1
    window_geometry: dict[str, int] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the JSON representation of these settings."""
        return {
            "schema": SCHEMA,
            "active_profile": self.active_profile,
            "crosshair_enabled": self.crosshair_enabled,
            "hotkeys": self.hotkeys.to_dict(),
            "overlay": self.overlay.to_dict(),
            "minimize_to_tray": self.minimize_to_tray,
            "nudge_step": self.nudge_step,
            "window_geometry": self.window_geometry,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Settings:
        """Build settings from JSON data."""
        hotkeys = data.get("hotkeys")
        overlay = data.get("overlay")
        geometry = data.get("window_geometry")
        if not isinstance(geometry, dict):
            geometry = None
        defaults = cls()
        return cls(
            active_profile=str(data.get("active_profile") or ""),
            crosshair_enabled=bool(data.get("crosshair_enabled", True)),
            hotkeys=HotkeyMap.from_dict(hotkeys if isinstance(hotkeys, dict) else {}),
            overlay=OverlayOptions.from_dict(overlay if isinstance(overlay, dict) else {}),
            minimize_to_tray=bool(data.get("minimize_to_tray", True)),
            nudge_step=max(1, min(1000, int(data.get("nudge_step", defaults.nudge_step) or 1))),
            window_geometry=geometry,
        )


def load_settings() -> Settings:
    """Load settings from disk, returning defaults when they are missing."""
    data = read_json(settings_path())
    if not isinstance(data, dict):
        return Settings()
    try:
        return Settings.from_dict(data)
    except (TypeError, ValueError):
        return Settings()


def save_settings(settings: Settings) -> None:
    """Write settings to disk atomically."""
    write_json(settings_path(), settings.to_dict())

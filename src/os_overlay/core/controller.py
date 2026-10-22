"""Central application state: active profile, overlay state and persistence."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal

from ..backends import create_hotkey_backend
from ..presets import seed_default_profiles
from ..profile import Profile, delete_profile, list_profiles, save_profile
from ..settings import Settings, load_settings, save_settings
from .hotkeys import HotkeyManager
from .library import export_profile_file, import_profile_file
from .media import MediaPlayer
from .overlay_manager import OverlayManager


class Controller(QObject):
    """Owns the profile list, the active profile, the overlay and the hotkeys."""

    profile_changed = Signal()
    profiles_changed = Signal()
    active_profile_changed = Signal(object)
    enabled_changed = Signal(bool)
    move_mode_changed = Signal(bool)
    status_message = Signal(str)
    hotkey_errors = Signal(dict)
    settings_changed = Signal()
    panel_toggle_requested = Signal()
    position_changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        seed_default_profiles()
        self.settings: Settings = load_settings()
        self.profiles: list[Profile] = list_profiles()
        self.media = MediaPlayer(self)
        self.overlay = OverlayManager(self)
        self.hotkeys = HotkeyManager(create_hotkey_backend(), self)

        self._active: Profile | None = None
        self._enabled = False
        self._move_mode = False
        self._dirty = False
        self._media_signature: tuple = ()
        self._hotkey_errors: dict[str, str] = {}

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(400)
        self._save_timer.timeout.connect(self._flush)

        self.hotkeys.activated.connect(self._on_hotkey)
        self.overlay.position_changed.connect(self._on_overlay_moved)

        self._active = self._pick_initial_profile()
        self.apply_settings()
        self.load_active_profile()

    @property
    def active_profile(self) -> Profile | None:
        """Return the profile that is currently applied."""
        return self._active

    @property
    def enabled(self) -> bool:
        """Return True when the crosshair is visible."""
        return self._enabled

    @property
    def move_mode(self) -> bool:
        """Return True when the crosshair can be dragged."""
        return self._move_mode

    @property
    def hotkey_error_map(self) -> dict[str, str]:
        """Return the errors of the last hotkey registration."""
        return dict(self._hotkey_errors)

    def apply_settings(self) -> None:
        """Push the stored settings into the overlay and the hotkey manager."""
        overlay = self.settings.overlay
        self._enabled = self.settings.crosshair_enabled
        self.overlay.set_enabled(self._enabled)
        self.overlay.set_always_on_top(overlay.always_on_top)
        self.overlay.set_click_through(overlay.click_through)
        self.overlay.set_show_on_all_screens(overlay.show_on_all_screens)
        self.overlay.set_nudge_step(self.settings.nudge_step)
        errors = self.hotkeys.apply(self.settings.hotkeys.to_dict())
        self._hotkey_errors = errors
        self.hotkey_errors.emit(errors)
        self.enabled_changed.emit(self._enabled)
        self.settings_changed.emit()

    def save_settings(self) -> None:
        """Write the settings to disk."""
        save_settings(self.settings)

    def load_active_profile(self) -> None:
        """Apply the active profile to the overlay."""
        profile = self._active
        if profile is None:
            self.media.unload()
            self._media_signature = ()
            self.overlay.apply_profile(Profile(), self.media)
            self.profile_changed.emit()
            return
        self._sync_media(profile)
        self.overlay.apply_profile(profile, self.media)
        self.profile_changed.emit()
        self.active_profile_changed.emit(profile)

    def commit_profile(self) -> None:
        """Store the active profile and refresh the overlay and preview."""
        if self._active is None:
            return
        self._sync_media(self._active)
        self.overlay.apply_profile(self._active, self.media)
        self._dirty = True
        self._save_timer.start()
        self.profile_changed.emit()

    def set_active_profile(self, profile: Profile) -> None:
        """Switch to another profile."""
        if profile is self._active:
            return
        self._flush()
        self._active = profile
        self.settings.active_profile = profile.id
        self.save_settings()
        self.load_active_profile()

    def step_profile(self, delta: int) -> None:
        """Move to the next or previous profile in the list."""
        if not self.profiles:
            return
        index = self.profiles.index(self._active) if self._active in self.profiles else 0
        self.set_active_profile(self.profiles[(index + delta) % len(self.profiles)])

    def add_profile(self, profile: Profile) -> Profile:
        """Add a profile to the collection and store it."""
        self.profiles.append(profile)
        save_profile(profile)
        self.profiles_changed.emit()
        return profile

    def duplicate_profile(self, profile: Profile) -> Profile:
        """Create a copy of a profile and add it to the collection."""
        return self.add_profile(profile.duplicate())

    def rename_profile(self, profile: Profile, name: str) -> None:
        """Rename a profile and store the change."""
        profile.name = name.strip() or profile.name
        save_profile(profile)
        self.profiles_changed.emit()

    def remove_profile(self, profile: Profile) -> bool:
        """Delete a profile, refusing to remove the last remaining one."""
        if len(self.profiles) <= 1:
            self.status_message.emit("At least one profile is required.")
            return False
        delete_profile(profile)
        self.profiles.remove(profile)
        if self._active is profile:
            self._active = self.profiles[0]
            self.settings.active_profile = self._active.id
            self.save_settings()
            self.load_active_profile()
        self.profiles_changed.emit()
        return True

    def export_profile(self, profile: Profile, path: str | Path, include_assets: bool) -> None:
        """Write a profile to an external file."""
        export_profile_file(profile, path, include_assets)
        self.status_message.emit(f"Profile exported to {path}.")

    def import_profile(self, path: str | Path) -> Profile | None:
        """Read a profile from an external file and add it to the collection."""
        profile = import_profile_file(path)
        if profile is None:
            self.status_message.emit("That file is not a valid profile.")
            return None
        self.add_profile(profile)
        self.status_message.emit(f"Profile '{profile.name}' imported.")
        return profile

    def toggle_enabled(self) -> None:
        """Show or hide the crosshair."""
        self._enabled = not self._enabled
        self.overlay.set_enabled(self._enabled)
        self.settings.crosshair_enabled = self._enabled
        self.save_settings()
        self.enabled_changed.emit(self._enabled)

    def toggle_move_mode(self) -> None:
        """Enable or disable dragging the crosshair."""
        self._move_mode = not self._move_mode
        self.overlay.set_move_mode(self._move_mode)
        self.move_mode_changed.emit(self._move_mode)
        if self._move_mode:
            self.status_message.emit("Move mode on: drag the crosshair to reposition it.")
        else:
            self.status_message.emit("Move mode off.")

    def position_pixels(self) -> tuple[int, int]:
        """Return the crosshair offset in pixels from the centre of the screen."""
        profile = self._active
        if profile is None:
            return (0, 0)
        width, height = self.overlay.target_screen_size()
        if width <= 0 or height <= 0:
            return (0, 0)
        return (
            round((profile.position.x - 0.5) * width),
            round((profile.position.y - 0.5) * height),
        )

    def set_position_pixels(self, x: int, y: int) -> None:
        """Place the crosshair at a pixel offset from the centre of the screen."""
        profile = self._active
        if profile is None:
            return
        width, height = self.overlay.target_screen_size()
        if width <= 0 or height <= 0:
            return
        profile.position.x = max(0.0, min(1.0, 0.5 + x / width))
        profile.position.y = max(0.0, min(1.0, 0.5 + y / height))
        self.overlay.apply_profile(profile, self.media)
        self._dirty = True
        self._save_timer.start()
        self.position_changed.emit()

    def nudge_position(self, dx: int, dy: int) -> None:
        """Move the crosshair by a number of pixels."""
        x, y = self.position_pixels()
        self.set_position_pixels(x + dx, y + dy)

    def set_nudge_step(self, step: int) -> None:
        """Set the number of pixels a single nudge moves the crosshair."""
        self.settings.nudge_step = max(1, min(1000, int(step)))
        self.overlay.set_nudge_step(self.settings.nudge_step)
        self.save_settings()
        self.settings_changed.emit()

    def set_screen(self, screen: str) -> None:
        """Choose the screen the crosshair is drawn on."""
        profile = self._active
        if profile is None:
            return
        profile.screen = str(screen)
        self.overlay.apply_profile(profile, self.media)
        self._dirty = True
        self._save_timer.start()
        self.position_changed.emit()

    def _pick_initial_profile(self) -> Profile | None:
        if not self.profiles:
            return None
        active_id = self.settings.active_profile
        for profile in self.profiles:
            if profile.id == active_id:
                return profile
        return self.profiles[0]

    def _sync_media(self, profile: Profile) -> None:
        """Load the media referenced by the profile when it changed."""
        signature = (
            profile.image.type,
            profile.image.path,
            tuple(profile.image.frames),
            profile.image.frame_ms,
        )
        if profile.style.mode != "image" or not profile.image.has_content:
            if self.media.has_content:
                self.media.unload()
            self._media_signature = ()
            return
        if signature == self._media_signature:
            return
        if not self.media.load(profile.image):
            self.status_message.emit("The image for this profile could not be loaded.")
            self._media_signature = ()
            return
        self._media_signature = signature

    def _flush(self) -> None:
        self._save_timer.stop()
        if self._dirty and self._active is not None:
            save_profile(self._active)
            self._dirty = False

    def _on_hotkey(self, action: str) -> None:
        if action == "toggle":
            self.toggle_enabled()
        elif action == "panel":
            self.panel_toggle_requested.emit()
        elif action == "move_mode":
            self.toggle_move_mode()
        elif action == "profile_prev":
            self.step_profile(-1)
        elif action == "profile_next":
            self.step_profile(1)

    def _on_overlay_moved(self, index: int, x: float, y: float) -> None:
        if self._active is None:
            return
        self._active.position.x = x
        self._active.position.y = y
        self._active.screen = str(index)
        self._dirty = True
        self._save_timer.start()
        self.position_changed.emit()

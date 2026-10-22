"""Places overlay windows on the available screens and keeps them in sync."""

from __future__ import annotations

import contextlib

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QCursor, QGuiApplication, QScreen

from ..profile import Position, Profile, Style
from .media import MediaPlayer
from .overlay import OverlayWindow


class OverlayManager(QObject):
    """Owns one overlay window per targeted screen."""

    position_changed = Signal(int, float, float)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._windows: dict[int, OverlayWindow] = {}
        self._style = Style()
        self._media: MediaPlayer | None = None
        self._image_scale = 1.0
        self._position = Position()
        self._screen = "cursor"
        self._enabled = False
        self._move_mode = False
        self._always_on_top = True
        self._click_through = True
        self._show_on_all = False
        self._nudge_step = 1

        self._cursor_timer = QTimer(self)
        self._cursor_timer.setInterval(250)
        self._cursor_timer.timeout.connect(self._on_cursor_tick)
        self._cursor_timer.start()

    @property
    def position(self) -> Position:
        """Return the current normalized crosshair position."""
        return self._position

    @property
    def screen(self) -> str:
        """Return the screen selection, either a name or an index."""
        return self._screen

    @property
    def nudge_step(self) -> int:
        """Return the number of pixels a single nudge moves the crosshair."""
        return self._nudge_step

    def target_screen_size(self) -> tuple[int, int]:
        """Return the pixel size of the screen the crosshair is placed on."""
        screens = self._screens()
        index = self._resolve_screen_index()
        if index is None or index >= len(screens):
            return (0, 0)
        geometry = screens[index].geometry()
        return (geometry.width(), geometry.height())

    def window_for_index(self, index: int) -> OverlayWindow | None:
        """Return the overlay window that is drawn on the given screen."""
        return self._windows.get(index)

    def apply_profile(self, profile: Profile, media: MediaPlayer | None) -> None:
        """Push a profile and its media into the overlays."""
        if self._media is not None:
            with contextlib.suppress(RuntimeError, TypeError):
                self._media.frame_changed.disconnect(self._on_frame_changed)
        self._style = profile.style
        self._media = media
        if media is not None:
            media.frame_changed.connect(self._on_frame_changed)
        self._image_scale = profile.image.scale
        self._position = profile.position
        self._screen = profile.screen
        self.refresh()

    def set_enabled(self, enabled: bool) -> None:
        """Show or hide every overlay window."""
        self._enabled = enabled
        for window in self._windows.values():
            window.setVisible(enabled)

    def set_move_mode(self, enabled: bool) -> None:
        """Enable or disable dragging the crosshair."""
        self._move_mode = enabled
        for window in self._windows.values():
            window.set_move_mode(enabled)

    def set_always_on_top(self, enabled: bool) -> None:
        """Keep the overlays above other windows."""
        self._always_on_top = enabled
        for window in self._windows.values():
            window.set_always_on_top(enabled)

    def set_click_through(self, enabled: bool) -> None:
        """Let mouse input pass through to the windows underneath."""
        self._click_through = enabled
        for window in self._windows.values():
            window.set_click_through(enabled)

    def set_show_on_all_screens(self, enabled: bool) -> None:
        """Draw the crosshair on every connected screen."""
        self._show_on_all = enabled
        self.refresh()

    def set_nudge_step(self, step: int) -> None:
        """Set the number of pixels a single nudge moves the crosshair."""
        self._nudge_step = max(1, int(step))
        for window in self._windows.values():
            window.set_nudge_step(self._nudge_step)

    def refresh(self) -> None:
        """Recreate and reposition the overlay windows to match the current state."""
        targets = self._target_indices()
        for index in list(self._windows):
            if index not in targets:
                window = self._windows.pop(index)
                window.hide()
                window.deleteLater()

        for index in targets:
            window = self._windows.get(index)
            if window is None:
                window = OverlayWindow()
                window.dragged.connect(lambda index=index: self._on_dragged(index))
                self._windows[index] = window
            window.set_style(self._style)
            window.set_media(self._media)
            window.set_image_scale(self._image_scale)
            window.set_move_mode(self._move_mode)
            window.set_click_through(self._click_through)
            window.set_always_on_top(self._always_on_top)
            window.set_nudge_step(self._nudge_step)
            window.refresh()
            self._place(window, index)
            window.setVisible(self._enabled)

    def _screens(self) -> list[QScreen]:
        return list(QGuiApplication.screens())

    def _resolve_screen_index(self) -> int | None:
        screens = self._screens()
        if not screens:
            return None
        if self._screen == "primary":
            primary = QGuiApplication.primaryScreen()
            return screens.index(primary) if primary in screens else 0
        if self._screen == "cursor":
            cursor = QCursor.pos()
            for index, screen in enumerate(screens):
                if screen.geometry().contains(cursor):
                    return index
            return 0
        try:
            index = int(self._screen)
        except (TypeError, ValueError):
            index = 0
        return index if 0 <= index < len(screens) else 0

    def _target_indices(self) -> list[int]:
        screens = self._screens()
        if not screens:
            return []
        if self._show_on_all:
            return list(range(len(screens)))
        index = self._resolve_screen_index()
        return [index] if index is not None else []

    def _place(self, window: OverlayWindow, index: int) -> None:
        screens = self._screens()
        if index >= len(screens):
            return
        geometry = screens[index].geometry()
        size = window.size()
        x = geometry.x() + self._position.x * geometry.width() - size.width() / 2.0
        y = geometry.y() + self._position.y * geometry.height() - size.height() / 2.0
        window.move(round(x), round(y))

    def _on_dragged(self, index: int) -> None:
        screens = self._screens()
        window = self._windows.get(index)
        if window is None or index >= len(screens):
            return
        geometry = screens[index].geometry()
        center = window.geometry().center()
        x = (center.x() - geometry.x()) / max(1, geometry.width())
        y = (center.y() - geometry.y()) / max(1, geometry.height())
        self._position = Position(x=max(0.0, min(1.0, x)), y=max(0.0, min(1.0, y)))
        self._screen = index
        self.position_changed.emit(index, self._position.x, self._position.y)

    def _on_frame_changed(self) -> None:
        for window in self._windows.values():
            window.update()

    def _on_cursor_tick(self) -> None:
        if self._screen != "cursor" or self._show_on_all:
            return
        index = self._resolve_screen_index()
        if index is not None and index not in self._windows:
            self.refresh()

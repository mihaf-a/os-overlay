"""Frameless transparent window that renders the crosshair on screen."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget

from ..profile import Style
from .media import MediaPlayer
from .renderer import content_size, paint_crosshair

MARGIN = 2


class OverlayWindow(QWidget):
    """Small always-on-top window that draws the crosshair."""

    dragged = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_AlwaysStackOnTop, True)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        self._style = Style()
        self._media: MediaPlayer | None = None
        self._image_scale = 1.0
        self._move_mode = False
        self._click_through = True
        self._always_on_top = True
        self._nudge_step = 1
        self._drag_origin: QPoint | None = None
        self._window_origin = QPoint()
        self._apply_flags()

    def set_style(self, style: Style) -> None:
        """Apply a new crosshair style and repaint."""
        self._style = style
        self.update()

    def set_media(self, media: MediaPlayer | None) -> None:
        """Attach the media player used when the style selects an image."""
        self._media = media
        self.update()

    def set_image_scale(self, scale: float) -> None:
        """Set the scale applied to an imported image."""
        self._image_scale = max(0.05, scale)
        self.update()

    def preferred_size(self) -> QSize:
        """Return the window size needed to show the crosshair without clipping."""
        if self._style.mode == "image" and self._media is not None:
            natural = self._media.natural_size()
            if natural.isValid():
                return QSize(
                    round(natural.width() * self._image_scale) + 2 * MARGIN,
                    round(natural.height() * self._image_scale) + 2 * MARGIN,
                )
        size = content_size(self._style)
        return QSize(size.width() + 2 * MARGIN, size.height() + 2 * MARGIN)

    def set_move_mode(self, enabled: bool) -> None:
        """Enable or disable dragging the crosshair with the mouse."""
        self._move_mode = enabled
        self._apply_flags()

    def set_click_through(self, enabled: bool) -> None:
        """Let mouse input pass through to the windows underneath."""
        self._click_through = enabled
        self._apply_flags()

    def set_always_on_top(self, enabled: bool) -> None:
        """Keep the overlay above other windows when enabled."""
        self._always_on_top = enabled
        self._apply_flags()

    def set_nudge_step(self, step: int) -> None:
        """Set the number of pixels a single nudge moves the crosshair."""
        self._nudge_step = max(1, int(step))

    def refresh(self) -> None:
        """Resize the window to fit the crosshair and repaint it."""
        self.resize(self.preferred_size())
        self.update()

    def paintEvent(self, event) -> None:  # Qt naming convention.
        """Render the crosshair onto the transparent surface."""
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        pixmap = None
        if self._style.mode == "image" and self._media is not None:
            natural = self._media.natural_size()
            if natural.isValid():
                pixmap = self._media.scaled_pixmap(
                    round(natural.width() * self._image_scale),
                    round(natural.height() * self._image_scale),
                )
        paint_crosshair(painter, QRectF(self.rect()), self._style, pixmap)

    def mousePressEvent(self, event) -> None:  # Qt naming convention.
        """Start dragging the crosshair when move mode is active."""
        if self._move_mode and event.button() == Qt.LeftButton:
            self._drag_origin = event.globalPosition().toPoint()
            self._window_origin = self.pos()
            self.setCursor(Qt.ClosedHandCursor)
            self.setFocus(Qt.MouseFocusReason)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # Qt naming convention.
        """Move the window while the crosshair is being dragged."""
        if self._drag_origin is not None:
            delta = event.globalPosition().toPoint() - self._drag_origin
            self.move(self._window_origin + delta)
            self.dragged.emit()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # Qt naming convention.
        """Finish dragging the crosshair."""
        if self._drag_origin is not None:
            self._drag_origin = None
            self.setCursor(Qt.OpenHandCursor if self._move_mode else Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:  # Qt naming convention.
        """Nudge the crosshair with the arrow keys."""
        if self._move_mode and event.key() in (
            Qt.Key_Left,
            Qt.Key_Right,
            Qt.Key_Up,
            Qt.Key_Down,
        ):
            step = (
                self._nudge_step * 10 if event.modifiers() & Qt.ShiftModifier else self._nudge_step
            )
            offset = QPoint(0, 0)
            if event.key() == Qt.Key_Left:
                offset.setX(-step)
            elif event.key() == Qt.Key_Right:
                offset.setX(step)
            elif event.key() == Qt.Key_Up:
                offset.setY(-step)
            else:
                offset.setY(step)
            self.move(self.pos() + offset)
            self.dragged.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def _apply_flags(self) -> None:
        """Recompute the window flags and restore the visibility if needed."""
        visible = self.isVisible()
        flags = self.windowFlags()
        if self._always_on_top:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        if self._click_through and not self._move_mode:
            flags |= Qt.WindowTransparentForInput
        else:
            flags &= ~Qt.WindowTransparentForInput
        self.setWindowFlags(flags)
        self.setCursor(Qt.OpenHandCursor if self._move_mode else Qt.ArrowCursor)
        if visible:
            self.show()

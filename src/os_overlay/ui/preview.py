"""Live preview canvas that shows the crosshair over a mock game scene."""

from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QSizePolicy, QWidget

from ..core.media import MediaPlayer
from ..core.renderer import content_size, paint_crosshair
from ..profile import Profile

PREVIEW_TARGET = 150.0


class PreviewWidget(QWidget):
    """Draws a mock scene with the current crosshair rendered on top."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._profile: Profile | None = None
        self._media = MediaPlayer(self)
        self._media.frame_changed.connect(self.update)
        self.setMinimumHeight(176)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_profile(self, profile: Profile | None) -> None:
        """Show a different profile in the preview."""
        self._profile = profile
        self._load_media(profile)
        self.update()

    def _load_media(self, profile: Profile | None) -> None:
        if profile is None or profile.style.mode != "image" or not profile.image.has_content:
            self._media.unload()
            return
        self._media.load(profile.image)

    def paintEvent(self, event) -> None:  # Qt naming convention.
        """Render the mock scene and the crosshair."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        self._draw_scene(painter, self.rect())

        profile = self._profile
        if profile is None:
            return

        style = profile.style
        base = self._base_size(profile)
        if base.isEmpty():
            return

        zoom = max(1.0, min(6.0, PREVIEW_TARGET / max(base.width(), base.height())))
        target = QRectF(0.0, 0.0, base.width() * zoom, base.height() * zoom)
        target.moveCenter(self.rect().center())

        pixmap = None
        if style.mode == "image":
            pixmap = self._media.scaled_pixmap(int(target.width()), int(target.height()))
        paint_crosshair(painter, target, style, pixmap)

    def _base_size(self, profile: Profile) -> QSize:
        if profile.style.mode == "image":
            natural = self._media.natural_size()
            if not natural.isValid():
                return QSize()
            return QSize(
                round(natural.width() * profile.image.scale),
                round(natural.height() * profile.image.scale),
            )
        return content_size(profile.style)

    def _draw_scene(self, painter: QPainter, rect: QRectF) -> None:
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, QColor("#1e2833"))
        gradient.setColorAt(0.55, QColor("#141a22"))
        gradient.setColorAt(1.0, QColor("#0a0d12"))
        painter.fillRect(rect, QBrush(gradient))

        horizon = rect.top() + rect.height() * 0.56
        painter.setPen(QPen(QColor(255, 255, 255, 16), 1))
        painter.drawLine(rect.left(), horizon, rect.right(), horizon)

        painter.setPen(QPen(QColor(255, 255, 255, 10), 1))
        step = max(24.0, rect.width() / 12.0)
        x = rect.left() + step
        while x < rect.right():
            painter.drawLine(x, horizon, x, rect.bottom())
            x += step
        y = horizon + step
        while y < rect.bottom():
            painter.drawLine(rect.left(), y, rect.right(), y)
            y += step

        vignette = QRadialGradient(rect.center(), max(rect.width(), rect.height()) * 0.72)
        vignette.setColorAt(0.55, QColor(0, 0, 0, 0))
        vignette.setColorAt(1.0, QColor(0, 0, 0, 130))
        painter.fillRect(rect, QBrush(vignette))

        painter.setPen(Qt.NoPen)

"""Application icon drawn in code so no binary asset is required."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QLinearGradient, QPainter, QPen, QPixmap

from .core.renderer import paint_crosshair
from .profile import Style


def render_icon(size: int = 64) -> QPixmap:
    """Draw the application icon at the requested size."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setPen(Qt.NoPen)

    gradient = QLinearGradient(0.0, 0.0, float(size), float(size))
    gradient.setColorAt(0.0, QColor("#232733"))
    gradient.setColorAt(1.0, QColor("#14171d"))
    painter.setBrush(QBrush(gradient))
    painter.drawRoundedRect(QRectF(0, 0, size, size), size * 0.22, size * 0.22)

    style = Style(
        shape="cross",
        color="#4ade80",
        thickness=max(2, size // 14),
        length=max(4, size // 5),
        gap=max(2, size // 9),
        dot=True,
        dot_size=max(2, size // 16),
        outline=True,
        outline_color="#0b0d11",
        outline_width=max(1, size // 32),
    )
    painter.setPen(QPen(Qt.transparent, 0))
    paint_crosshair(painter, QRectF(0, 0, size, size), style)
    painter.end()
    return pixmap


def app_icon(size: int = 64) -> QIcon:
    """Return the application icon."""
    return QIcon(render_icon(size))

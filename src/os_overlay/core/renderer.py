"""Drawing routines for vector crosshairs and imported image crosshairs."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
    QTransform,
)

from ..profile import Style

STROKED_SHAPES = ("circle", "square")


def _rect_polygon(left: float, top: float, right: float, bottom: float) -> QPolygonF:
    """Return a polygon covering the given rectangle."""
    return QPolygonF(
        [
            QPointF(left, top),
            QPointF(right, top),
            QPointF(right, bottom),
            QPointF(left, bottom),
        ]
    )


def _arm_polygon(inner: float, outer: float, half_inner: float, half_outer: float) -> QPolygonF:
    """Return a tapered arm pointing along the positive x axis."""
    return QPolygonF(
        [
            QPointF(inner, -half_inner),
            QPointF(outer, -half_outer),
            QPointF(outer, half_outer),
            QPointF(inner, half_inner),
        ]
    )


def _rotate_polygon(polygon: QPolygonF, degrees: float) -> QPolygonF:
    """Return a copy of the polygon rotated around the origin."""
    return QTransform().rotate(degrees).map(polygon)


def shape_polygons(style: Style) -> list[QPolygonF]:
    """Return the filled polygons that make up a vector crosshair."""
    half = style.thickness / 2.0
    outer_half = max(0.5, half * (1.0 - style.taper))
    length = float(style.length)
    gap = float(style.gap)
    shape = style.shape
    polygons: list[QPolygonF] = []

    if shape in ("dot", *STROKED_SHAPES):
        return polygons

    if shape in ("cross", "gap-cross"):
        reach = gap * 2.0 if shape == "gap-cross" else gap
        arm = _arm_polygon(reach, reach + length, half, outer_half)
        for degrees in (0.0, 90.0, 180.0, 270.0):
            polygons.append(_rotate_polygon(arm, degrees))
    elif shape == "t-square":
        polygons.append(_rect_polygon(-length, -length, length, -length + style.thickness))
        polygons.append(_rect_polygon(-half, -length, half, length))
    elif shape == "bracket":
        reach = gap + length
        for sign_x in (-1.0, 1.0):
            for sign_y in (-1.0, 1.0):
                polygons.append(
                    _rect_polygon(
                        min(sign_x * gap, sign_x * reach),
                        sign_y * gap - half,
                        max(sign_x * gap, sign_x * reach),
                        sign_y * gap + half,
                    )
                )
                polygons.append(
                    _rect_polygon(
                        sign_x * gap - half,
                        min(sign_y * gap, sign_y * reach),
                        sign_x * gap + half,
                        max(sign_y * gap, sign_y * reach),
                    )
                )
    return polygons


def shape_path(style: Style) -> QPainterPath:
    """Return the outline path used by the circle and square shapes."""
    path = QPainterPath()
    length = float(style.length)
    if style.shape == "circle":
        path.addEllipse(QPointF(0.0, 0.0), length, length)
    elif style.shape == "square":
        path.addRect(QRectF(-length, -length, length * 2.0, length * 2.0))
    return path


def content_size(style: Style) -> QSize:
    """Return the pixel extent of the crosshair, outline included."""
    length = float(style.length)
    gap = float(style.gap)
    shape = style.shape

    if shape == "dot":
        extent = float(max(style.dot_size, style.thickness))
    elif shape in STROKED_SHAPES:
        extent = 2 * length + style.thickness
    elif shape == "gap-cross":
        extent = 2 * (gap * 2.0 + length) + style.thickness
    elif shape == "t-square":
        extent = 2 * length + style.thickness
    else:
        extent = 2 * (gap + length) + style.thickness

    if style.outline:
        extent += 2 * style.outline_width
    return QSize(round(extent), round(extent))


def _dot_radius(style: Style) -> float:
    """Return the radius used for the centre dot."""
    return max(style.dot_size, style.thickness) / 2.0


def _draw_dot(
    painter: QPainter, radius: float, color: QColor, outline: QColor, outline_width: int
) -> None:
    """Draw the centre dot with an optional outline."""
    painter.setPen(Qt.NoPen)
    if outline_width > 0:
        painter.setBrush(outline)
        painter.drawEllipse(QPointF(0.0, 0.0), radius + outline_width, radius + outline_width)
    painter.setBrush(color)
    painter.drawEllipse(QPointF(0.0, 0.0), radius, radius)


def paint_crosshair(
    painter: QPainter, rect: QRectF, style: Style, pixmap: QPixmap | None = None
) -> None:
    """Draw a crosshair centred inside the given rectangle."""
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)

    if pixmap is not None and not pixmap.isNull():
        width = float(pixmap.width())
        height = float(pixmap.height())
        target = QRectF(
            rect.center().x() - width / 2.0,
            rect.center().y() - height / 2.0,
            width,
            height,
        )
        painter.setOpacity(max(0.0, min(1.0, style.opacity)))
        painter.drawPixmap(target, pixmap)
        painter.restore()
        return

    color = QColor(style.color)
    if not color.isValid():
        color = QColor("#00ff66")
    color.setAlphaF(max(0.0, min(1.0, style.opacity)))
    outline_color = QColor(style.outline_color)
    if not outline_color.isValid():
        outline_color = QColor("#000000")
    outline_color.setAlphaF(color.alphaF())
    outline_width = style.outline_width if style.outline else 0

    painter.translate(rect.center())
    painter.rotate(style.rotation)

    if style.shape in STROKED_SHAPES:
        path = shape_path(style)
        if outline_width > 0:
            painter.setPen(QPen(outline_color, style.thickness + 2 * outline_width))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)
        painter.setPen(QPen(color, style.thickness))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)
    else:
        for polygon in shape_polygons(style):
            if outline_width > 0:
                pen = QPen(outline_color, 2 * outline_width)
                pen.setJoinStyle(Qt.MiterJoin)
                painter.setPen(pen)
            else:
                painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawPolygon(polygon)

    if style.shape == "dot" or style.dot:
        _draw_dot(painter, _dot_radius(style), color, outline_color, outline_width)

    painter.restore()

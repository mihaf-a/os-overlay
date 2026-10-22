"""Tests for the crosshair geometry and painting routines."""

from __future__ import annotations

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QImage, QPainter

from os_overlay.core.renderer import content_size, paint_crosshair, shape_polygons
from os_overlay.profile import SHAPES, Style


def test_content_size_matches_the_cross_geometry():
    style = Style(shape="cross", thickness=2, length=10, gap=5, outline=False)

    assert content_size(style).width() == 2 * (5 + 10) + 2


def test_content_size_includes_the_outline():
    plain = Style(shape="cross", thickness=2, length=10, gap=5, outline=False)
    outlined = Style(shape="cross", thickness=2, length=10, gap=5, outline=True)

    assert content_size(outlined).width() == content_size(plain).width() + 2


def test_gap_cross_is_larger_than_a_cross():
    cross = Style(shape="cross", gap=5, length=10)
    gap_cross = Style(shape="gap-cross", gap=5, length=10)

    assert content_size(gap_cross).width() > content_size(cross).width()


def test_dot_size_follows_the_dot_setting():
    style = Style(shape="dot", dot_size=7, thickness=2, outline=False)

    assert content_size(style).width() == 7


def test_stroked_shapes_use_the_length():
    for shape in ("circle", "square"):
        style = Style(shape=shape, length=12, thickness=3, outline=False)
        assert content_size(style).width() == 2 * 12 + 3


def test_polygon_counts_per_shape():
    expected = {
        "cross": 4,
        "gap-cross": 4,
        "t-square": 2,
        "bracket": 8,
        "dot": 0,
        "circle": 0,
        "square": 0,
    }

    for shape, count in expected.items():
        style = Style(shape=shape, length=10, gap=4)
        assert len(shape_polygons(style)) == count


def test_every_shape_has_a_positive_size():
    for shape in SHAPES:
        style = Style(shape=shape)
        size = content_size(style)
        assert size.width() > 0
        assert size.height() > 0


def test_paint_crosshair_draws_inside_the_content_box(qt_app):
    style = Style(shape="cross", color="#4ade80", thickness=2, length=10, gap=5, outline=False)
    size = content_size(style)
    image = QImage(size.width(), size.height(), QImage.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 0))

    painter = QPainter(image)
    paint_crosshair(painter, QRectF(0, 0, size.width(), size.height()), style)
    painter.end()

    assert any(
        image.pixelColor(x, y).alpha() > 0
        for y in range(size.height())
        for x in range(size.width())
    )


def test_paint_crosshair_honours_the_opacity(qt_app):
    style = Style(shape="cross", opacity=0.0, outline=False)
    size = content_size(style)
    image = QImage(size.width(), size.height(), QImage.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 0))

    painter = QPainter(image)
    paint_crosshair(painter, QRectF(0, 0, size.width(), size.height()), style)
    painter.end()

    assert not any(
        image.pixelColor(x, y).alpha() > 0
        for y in range(size.height())
        for x in range(size.width())
    )

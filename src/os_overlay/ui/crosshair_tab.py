"""Tab that edits the vector appearance of a crosshair."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..core.controller import Controller
from ..profile import SHAPES, Profile
from .controls import ColorButton, ValueSlider

SHAPE_LABELS: dict[str, str] = {
    "cross": "Cross",
    "dot": "Dot",
    "circle": "Circle",
    "square": "Square",
    "t-square": "T-Square",
    "gap-cross": "Gap cross",
    "bracket": "Brackets",
}


class CrosshairTab(QWidget):
    """Edits the shape, colour and proportions of the crosshair."""

    def __init__(self, controller: Controller, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._loading = False

        self.shape_combo = QComboBox(self)
        for key in SHAPES:
            self.shape_combo.addItem(SHAPE_LABELS.get(key, key.title()), key)

        self.color_button = ColorButton("#00ff66", self)
        self.outline_check = QCheckBox("Outline", self)
        self.outline_color_button = ColorButton("#000000", self)
        self.thickness_slider = ValueSlider(1, 12, 2, " px", self)
        self.length_slider = ValueSlider(0, 80, 9, " px", self)
        self.gap_slider = ValueSlider(0, 40, 4, " px", self)
        self.dot_check = QCheckBox("Centre dot", self)
        self.dot_size_slider = ValueSlider(0, 16, 2, " px", self)
        self.taper_slider = ValueSlider(0, 100, 0, " %", self)
        self.rotation_slider = ValueSlider(-180, 180, 0, " deg", self)
        self.opacity_slider = ValueSlider(0, 100, 100, " %", self)

        form = QFormLayout()
        form.setContentsMargins(14, 14, 14, 14)
        form.setVerticalSpacing(10)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.addRow("Shape", self.shape_combo)
        form.addRow("Colour", self.color_button)
        form.addRow("", self.outline_check)
        form.addRow("Outline colour", self.outline_color_button)
        form.addRow("Thickness", self.thickness_slider)
        form.addRow("Length", self.length_slider)
        form.addRow("Gap", self.gap_slider)
        form.addRow("", self.dot_check)
        form.addRow("Dot size", self.dot_size_slider)
        form.addRow("Taper", self.taper_slider)
        form.addRow("Rotation", self.rotation_slider)
        form.addRow("Opacity", self.opacity_slider)

        card = QFrame(self)
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.addLayout(form)
        self._card = card

        area = QScrollArea(self)
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        area.setWidget(card)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(area)

        self.shape_combo.currentIndexChanged.connect(self._on_shape)
        self.color_button.color_changed.connect(self._on_color)
        self.outline_check.toggled.connect(self._on_outline)
        self.outline_color_button.color_changed.connect(self._on_outline_color)
        self.thickness_slider.value_changed.connect(self._on_thickness)
        self.length_slider.value_changed.connect(self._on_length)
        self.gap_slider.value_changed.connect(self._on_gap)
        self.dot_check.toggled.connect(self._on_dot)
        self.dot_size_slider.value_changed.connect(self._on_dot_size)
        self.taper_slider.value_changed.connect(self._on_taper)
        self.rotation_slider.value_changed.connect(self._on_rotation)
        self.opacity_slider.value_changed.connect(self._on_opacity)

        self._controller.profile_changed.connect(self._reload_profile)
        self.load_profile(self._controller.active_profile)

    def _reload_profile(self) -> None:
        """Reload the active profile after the controller changed it."""
        self.load_profile(self._controller.active_profile)

    def load_profile(self, profile: Profile | None) -> None:
        """Show the values of a profile without triggering changes."""
        if profile is None:
            self._card.setEnabled(False)
            return
        self._loading = True
        self._card.setEnabled(profile.style.mode != "image")
        self.shape_combo.setCurrentIndex(self.shape_combo.findData(profile.style.shape))
        self.color_button.set_color(profile.style.color)
        self.outline_check.setChecked(profile.style.outline)
        self.outline_color_button.set_color(profile.style.outline_color)
        self.outline_color_button.setEnabled(profile.style.outline)
        self.thickness_slider.set_value(profile.style.thickness)
        self.length_slider.set_value(profile.style.length)
        self.gap_slider.set_value(profile.style.gap)
        self.dot_check.setChecked(profile.style.dot)
        self.dot_size_slider.set_value(profile.style.dot_size)
        self.dot_size_slider.setEnabled(profile.style.dot)
        self.taper_slider.set_value(round(profile.style.taper * 100))
        self.rotation_slider.set_value(round(profile.style.rotation))
        self.opacity_slider.set_value(round(profile.style.opacity * 100))
        self._loading = False

    def _style(self):
        profile = self._controller.active_profile
        return profile.style if profile is not None else None

    def _commit(self) -> None:
        if not self._loading:
            self._controller.commit_profile()

    def _on_shape(self, _index: int) -> None:
        style = self._style()
        if style is not None:
            style.shape = self.shape_combo.currentData()
            self._commit()

    def _on_color(self, color) -> None:
        style = self._style()
        if style is not None:
            style.color = color.name()
            self._commit()

    def _on_outline(self, checked: bool) -> None:
        style = self._style()
        if style is not None:
            style.outline = checked
            self.outline_color_button.setEnabled(checked)
            self._commit()

    def _on_outline_color(self, color) -> None:
        style = self._style()
        if style is not None:
            style.outline_color = color.name()
            self._commit()

    def _on_thickness(self, value: int) -> None:
        style = self._style()
        if style is not None:
            style.thickness = value
            self._commit()

    def _on_length(self, value: int) -> None:
        style = self._style()
        if style is not None:
            style.length = value
            self._commit()

    def _on_gap(self, value: int) -> None:
        style = self._style()
        if style is not None:
            style.gap = value
            self._commit()

    def _on_dot(self, checked: bool) -> None:
        style = self._style()
        if style is not None:
            style.dot = checked
            self.dot_size_slider.setEnabled(checked)
            self._commit()

    def _on_dot_size(self, value: int) -> None:
        style = self._style()
        if style is not None:
            style.dot_size = value
            self._commit()

    def _on_taper(self, value: int) -> None:
        style = self._style()
        if style is not None:
            style.taper = value / 100.0
            self._commit()

    def _on_rotation(self, value: int) -> None:
        style = self._style()
        if style is not None:
            style.rotation = float(value)
            self._commit()

    def _on_opacity(self, value: int) -> None:
        style = self._style()
        if style is not None:
            style.opacity = value / 100.0
            self._commit()

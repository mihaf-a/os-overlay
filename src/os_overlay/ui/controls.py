"""Small reusable widgets shared by the configuration tabs."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QWidget,
)


class ColorButton(QPushButton):
    """A button that shows a colour swatch and opens a colour picker."""

    color_changed = Signal(QColor)

    def __init__(self, color: str = "#ffffff", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = QColor(color)
        self.setFixedSize(64, 26)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self._pick_color)
        self._refresh()

    def color(self) -> QColor:
        """Return the currently selected colour."""
        return QColor(self._color)

    def set_color(self, color: str | QColor) -> None:
        """Set the colour without emitting the change signal."""
        value = QColor(color)
        if not value.isValid():
            return
        self._color = value
        self._refresh()

    def _pick_color(self) -> None:
        chosen = QColorDialog.getColor(self._color, self, "Select colour")
        if chosen.isValid():
            self._color = chosen
            self._refresh()
            self.color_changed.emit(QColor(self._color))

    def _refresh(self) -> None:
        self.setText("")
        self.setStyleSheet(
            "QPushButton {"
            f"background-color: {self._color.name()};"
            "border: 1px solid #2f3542;"
            "border-radius: 6px;"
            "}"
        )


class ValueSlider(QWidget):
    """A slider with a fixed width value readout next to it."""

    value_changed = Signal(int)

    def __init__(
        self,
        minimum: int,
        maximum: int,
        value: int,
        suffix: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._suffix = suffix
        self._slider = QSlider(Qt.Horizontal, self)
        self._slider.setRange(minimum, maximum)
        self._slider.setValue(value)
        self._label = QLabel(self._format(value), self)
        self._label.setFixedWidth(46)
        self._label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self._slider, 1)
        layout.addWidget(self._label, 0)

        self._slider.valueChanged.connect(self._on_change)

    def value(self) -> int:
        """Return the current slider value."""
        return self._slider.value()

    def set_value(self, value: int) -> None:
        """Set the slider value without emitting the change signal."""
        self._slider.blockSignals(True)
        self._slider.setValue(value)
        self._slider.blockSignals(False)
        self._label.setText(self._format(self._slider.value()))

    def _on_change(self, value: int) -> None:
        self._label.setText(self._format(value))
        self.value_changed.emit(value)

    def _format(self, value: int) -> str:
        return f"{value}{self._suffix}"

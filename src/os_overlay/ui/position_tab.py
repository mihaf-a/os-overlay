"""Tab that places the crosshair with exact numbers and arrow buttons."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..core.controller import Controller

CURSOR_SCREEN = "cursor"
PRIMARY_SCREEN = "primary"

MAX_OFFSET = 10000
MAX_STEP = 1000


def _screen_name(screen, index: int) -> str:
    """Return a readable name for a screen."""
    name = screen.name().replace("\\", "").replace(".", "").strip()
    if not name:
        name = f"Screen {index + 1}"
    return name


class PositionTab(QWidget):
    """Places the crosshair with a pixel offset, arrow buttons and a step size."""

    def __init__(self, controller: Controller, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._loading = False

        self.screen_combo = QComboBox(self)
        self.x_spin = QSpinBox(self)
        self.x_spin.setRange(-MAX_OFFSET, MAX_OFFSET)
        self.x_spin.setSuffix(" px")
        self.x_spin.setToolTip("Horizontal offset from the centre of the screen.")

        self.y_spin = QSpinBox(self)
        self.y_spin.setRange(-MAX_OFFSET, MAX_OFFSET)
        self.y_spin.setSuffix(" px")
        self.y_spin.setToolTip("Vertical offset from the centre of the screen.")

        self.step_spin = QSpinBox(self)
        self.step_spin.setRange(1, MAX_STEP)
        self.step_spin.setSuffix(" px")
        self.step_spin.setToolTip("Number of pixels moved by one arrow click.")

        self.up_button = self._arrow_button("↑", "Move the crosshair up")
        self.down_button = self._arrow_button("↓", "Move the crosshair down")
        self.left_button = self._arrow_button("←", "Move the crosshair left")
        self.right_button = self._arrow_button("→", "Move the crosshair right")

        self.centre_button = QPushButton("Centre", self)
        self.centre_button.setToolTip("Put the crosshair back in the middle of the screen.")

        form = QFormLayout()
        form.setContentsMargins(14, 14, 14, 14)
        form.setVerticalSpacing(10)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.addRow("Screen", self.screen_combo)
        form.addRow("Offset X", self.x_spin)
        form.addRow("Offset Y", self.y_spin)

        arrows = QGridLayout()
        arrows.setContentsMargins(0, 0, 0, 0)
        arrows.setSpacing(4)
        arrows.addWidget(self.up_button, 0, 1, Qt.AlignCenter)
        arrows.addWidget(self.left_button, 1, 0, Qt.AlignCenter)
        arrows.addWidget(self.down_button, 1, 1, Qt.AlignCenter)
        arrows.addWidget(self.right_button, 1, 2, Qt.AlignCenter)

        step_row = QHBoxLayout()
        step_row.setContentsMargins(0, 0, 0, 0)
        step_row.setSpacing(8)
        step_row.addWidget(self.step_spin, 1)
        step_row.addWidget(self.centre_button, 0)

        step_form = QFormLayout()
        step_form.setContentsMargins(14, 14, 14, 14)
        step_form.setVerticalSpacing(10)
        step_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        step_form.addRow("Step", step_row)

        card = QFrame(self)
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(4)
        card_layout.addLayout(form)
        card_layout.addLayout(arrows)
        card_layout.addLayout(step_form)
        self._card = card

        hint = QLabel(
            "The offset is measured in pixels from the centre of the screen. "
            "The arrow buttons move the crosshair by one step, and the arrow keys "
            "do the same while move mode is on.",
            self,
        )
        hint.setObjectName("Subtle")
        hint.setWordWrap(True)

        area = QScrollArea(self)
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        area.setWidget(card)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(area)
        outer.addWidget(hint)

        self.screen_combo.currentIndexChanged.connect(self._on_screen)
        self.x_spin.valueChanged.connect(self._on_offset)
        self.y_spin.valueChanged.connect(self._on_offset)
        self.step_spin.valueChanged.connect(self._on_step)
        self.up_button.clicked.connect(lambda: self._nudge(0, -1))
        self.down_button.clicked.connect(lambda: self._nudge(0, 1))
        self.left_button.clicked.connect(lambda: self._nudge(-1, 0))
        self.right_button.clicked.connect(lambda: self._nudge(1, 0))
        self.centre_button.clicked.connect(self._on_centre)

        self._controller.profile_changed.connect(self._reload_profile)
        self._controller.position_changed.connect(self._reload_position)
        self._controller.settings_changed.connect(self._reload_settings)
        self.reload()

    def _arrow_button(self, text: str, tip: str) -> QPushButton:
        """Create one of the arrow buttons."""
        button = QPushButton(text, self)
        button.setToolTip(tip)
        button.setFixedSize(44, 32)
        button.setFocusPolicy(Qt.StrongFocus)
        font = QFont(button.font())
        font.setFamilies(["Segoe UI", "Segoe UI Symbol", "DejaVu Sans", "Arial Unicode MS"])
        font.setPointSize(12)
        button.setFont(font)
        return button

    def reload(self) -> None:
        """Show the values of the active profile and the current settings."""
        self._loading = True
        profile = self._controller.active_profile
        self._card.setEnabled(profile is not None)
        if profile is not None:
            self._fill_screens(profile.screen)
            self.step_spin.setValue(self._controller.settings.nudge_step)
        self._loading = False
        self._reload_position()

    def _reload_profile(self) -> None:
        """Reload the active profile after the controller changed it."""
        self.reload()

    def _reload_position(self) -> None:
        """Show the current offset without triggering a change."""
        self._loading = True
        x, y = self._controller.position_pixels()
        self.x_spin.setValue(x)
        self.y_spin.setValue(y)
        self._loading = False

    def _reload_settings(self) -> None:
        """Show the stored settings without triggering a change."""
        self._loading = True
        self.step_spin.setValue(self._controller.settings.nudge_step)
        self._loading = False

    def _fill_screens(self, selected: str) -> None:
        """Fill the screen list and select the screen of the profile."""
        self.screen_combo.blockSignals(True)
        self.screen_combo.clear()
        self.screen_combo.addItem("Screen with the cursor", CURSOR_SCREEN)
        self.screen_combo.addItem("Primary screen", PRIMARY_SCREEN)
        for index, screen in enumerate(QGuiApplication.screens()):
            self.screen_combo.addItem(f"{index + 1}. {_screen_name(screen, index)}", str(index))
        index = self.screen_combo.findData(selected)
        if index < 0:
            index = 0
        self.screen_combo.setCurrentIndex(index)
        self.screen_combo.blockSignals(False)

    def _step(self) -> int:
        """Return the number of pixels a single nudge moves the crosshair."""
        return max(1, self.step_spin.value())

    def _nudge(self, direction_x: int, direction_y: int) -> None:
        """Move the crosshair by one step in the given direction."""
        step = self._step()
        self._controller.nudge_position(direction_x * step, direction_y * step)

    def _on_offset(self, _value: int) -> None:
        """Apply the offset that was typed into the fields."""
        if self._loading:
            return
        self._controller.set_position_pixels(self.x_spin.value(), self.y_spin.value())

    def _on_step(self, value: int) -> None:
        """Store the number of pixels a single nudge moves the crosshair."""
        if self._loading:
            return
        self._controller.set_nudge_step(value)

    def _on_screen(self, _index: int) -> None:
        """Apply the screen that was selected."""
        if self._loading:
            return
        data = self.screen_combo.currentData()
        if data:
            self._controller.set_screen(str(data))

    def _on_centre(self) -> None:
        """Put the crosshair back in the middle of the screen."""
        self._controller.set_position_pixels(0, 0)

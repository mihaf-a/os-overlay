"""Tab that binds the global shortcuts to actions."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..core.controller import Controller
from ..settings import HOTKEY_ACTIONS
from .hotkey_edit import HotkeyEdit


class HotkeysTab(QWidget):
    """Lists every action and lets the user record a shortcut for it."""

    def __init__(self, controller: Controller, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._edits: dict[str, HotkeyEdit] = {}
        self._status: dict[str, QLabel] = {}

        grid = QGridLayout()
        grid.setContentsMargins(14, 14, 14, 14)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)

        for row, (action, label) in enumerate(HOTKEY_ACTIONS):
            name = QLabel(label, self)
            edit = HotkeyEdit(self._controller.settings.hotkeys.get(action), self)
            status = QLabel("", self)
            status.setObjectName("Subtle")
            status.setWordWrap(True)
            grid.addWidget(name, row, 0)
            grid.addWidget(edit, row, 1)
            grid.addWidget(status, row, 2)
            self._edits[action] = edit
            self._status[action] = status
            edit.hotkey_changed.connect(
                lambda binding, action=action: self._on_changed(action, binding)
            )

        card = QFrame(self)
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.addLayout(grid)

        hint = QLabel(
            "Shortcuts are registered system wide. Click a field and press the keys "
            "you want to use, Escape cancels.",
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

        self._controller.hotkey_errors.connect(self._on_errors)
        self._controller.settings_changed.connect(self.load_bindings)
        self.load_bindings()
        # The registration runs before this tab exists, so the first errors are read.
        self._on_errors(self._controller.hotkey_error_map)

    def load_bindings(self) -> None:
        """Show the shortcuts that are currently configured."""
        hotkeys = self._controller.settings.hotkeys
        for action, edit in self._edits.items():
            edit.set_binding(hotkeys.get(action))

    def _on_changed(self, action: str, binding: str) -> None:
        self._controller.settings.hotkeys.set(action, binding)
        self._controller.apply_settings()
        self._controller.save_settings()
        self._report_duplicates()

    def _on_errors(self, errors: dict[str, str]) -> None:
        for action, label in self._status.items():
            message = errors.get(action, "")
            label.setText(message)
            label.setStyleSheet("color: #f87171;" if message else "")

    def _report_duplicates(self) -> None:
        hotkeys = self._controller.settings.hotkeys
        seen: dict[str, str] = {}
        for action, _ in HOTKEY_ACTIONS:
            binding = hotkeys.get(action)
            if binding in seen:
                self._status[action].setText("Used by another action as well.")
                self._status[action].setStyleSheet("color: #f87171;")
            else:
                seen[binding] = action

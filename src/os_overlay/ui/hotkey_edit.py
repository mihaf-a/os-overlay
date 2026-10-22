"""Click-to-record widget that captures a global shortcut."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QPushButton, QWidget

from ..core.hotkeys import format_binding

QT_KEY_NAMES: dict[int, str] = {
    Qt.Key_Space: "Space",
    Qt.Key_Enter: "Enter",
    Qt.Key_Escape: "Escape",
    Qt.Key_Backspace: "Backspace",
    Qt.Key_Delete: "Delete",
    Qt.Key_Insert: "Insert",
    Qt.Key_Home: "Home",
    Qt.Key_End: "End",
    Qt.Key_PageUp: "PageUp",
    Qt.Key_PageDown: "PageDown",
    Qt.Key_Up: "Up",
    Qt.Key_Down: "Down",
    Qt.Key_Left: "Left",
    Qt.Key_Right: "Right",
    Qt.Key_Print: "Print",
    Qt.Key_Pause: "Pause",
    Qt.Key_NumLock: "NumLock",
    Qt.Key_ScrollLock: "ScrollLock",
    Qt.Key_CapsLock: "CapsLock",
    Qt.Key_Plus: "+",
    Qt.Key_Minus: "-",
    Qt.Key_Equal: "=",
    Qt.Key_Comma: ",",
    Qt.Key_Period: ".",
    Qt.Key_Slash: "/",
    Qt.Key_Semicolon: ";",
    Qt.Key_Apostrophe: "'",
    Qt.Key_QuoteLeft: "`",
    Qt.Key_BracketLeft: "[",
    Qt.Key_BracketRight: "]",
    Qt.Key_Backslash: "\\",
}

MOUSE_KEY_NAMES: dict[int, str] = {
    Qt.MiddleButton: "Mouse3",
    Qt.BackButton: "Mouse4",
    Qt.ForwardButton: "Mouse5",
}


def qt_key_name(key: int) -> str | None:
    """Return the canonical name of a Qt key code, or None when it has none."""
    if key in QT_KEY_NAMES:
        return QT_KEY_NAMES[key]
    if Qt.Key_A <= key <= Qt.Key_Z:
        return chr(key)
    if Qt.Key_0 <= key <= Qt.Key_9:
        return chr(key)
    if Qt.Key_F1 <= key <= Qt.Key_F24:
        return f"F{key - Qt.Key_F1 + 1}"
    if Qt.Key_Num0 <= key <= Qt.Key_Num9:
        return f"Num{key - Qt.Key_Num0}"
    return None


class HotkeyEdit(QPushButton):
    """A button that records the next key combination the user presses."""

    hotkey_changed = Signal(str)

    def __init__(self, binding: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._binding = binding
        self.setObjectName("Record")
        self.setCheckable(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumWidth(130)
        self.toggled.connect(self._on_toggled)
        self._refresh()

    def binding(self) -> str:
        """Return the recorded shortcut."""
        return self._binding

    def set_binding(self, binding: str) -> None:
        """Show an existing shortcut without emitting a change."""
        self._binding = binding
        self._refresh()

    def _refresh(self) -> None:
        self.setText(self._binding or "Not set")

    def _on_toggled(self, checked: bool) -> None:
        if checked:
            self.setText("Press keys...")
            self.setToolTip("Press the key combination to use. Escape cancels.")
        else:
            self.setToolTip("Click to record a new shortcut.")
            self._refresh()

    def mousePressEvent(self, event) -> None:  # Qt naming convention.
        """Start or cancel recording when the button is clicked."""
        if event.button() == Qt.LeftButton:
            self.setChecked(not self.isChecked())
            if self.isChecked():
                self.setFocus(Qt.MouseFocusReason)
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # Qt naming convention.
        """Store the pressed key combination as the new shortcut."""
        if not self.isChecked():
            super().keyPressEvent(event)
            return

        if event.key() == Qt.Key_Escape and event.modifiers() == Qt.NoModifier:
            self.setChecked(False)
            event.accept()
            return

        name = qt_key_name(event.key())
        if name is None:
            event.accept()
            return

        modifiers = event.modifiers()
        parts: list[str] = []
        if modifiers & Qt.ControlModifier:
            parts.append("Ctrl")
        if modifiers & Qt.AltModifier:
            parts.append("Alt")
        if modifiers & Qt.ShiftModifier:
            parts.append("Shift")
        if modifiers & Qt.MetaModifier:
            parts.append("Win")

        self.setChecked(False)
        self.set_binding(format_binding(parts, name))
        self.hotkey_changed.emit(self._binding)
        event.accept()

"""Main control panel window of the application."""

from __future__ import annotations

from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSystemTrayIcon,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..core.controller import Controller
from ..settings import HOTKEY_ACTIONS
from .crosshair_tab import CrosshairTab
from .hotkeys_tab import HotkeysTab
from .image_tab import ImageTab
from .position_tab import PositionTab
from .preview import PreviewWidget
from .profiles_tab import ProfilesTab


class MainWindow(QMainWindow):
    """The configuration panel that drives the overlay."""

    def __init__(self, controller: Controller, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self.setWindowTitle("os-overlay")
        self.setMinimumWidth(440)
        # A tool window floats above other windows and stays out of the taskbar,
        # which also keeps window tiling managers from resizing the panel.
        self.setWindowFlags(Qt.Tool)

        self.title_label = QLabel("os-overlay", self)
        self.title_label.setObjectName("Title")
        self.hint_label = QLabel("", self)
        self.hint_label.setObjectName("Subtle")

        self.enable_button = QPushButton("Crosshair: On", self)
        self.enable_button.setObjectName("Primary")
        self.enable_button.setCheckable(True)
        self.move_button = QPushButton("Move", self)
        self.move_button.setCheckable(True)
        self.move_button.setToolTip("Drag the crosshair to reposition it")

        header = QHBoxLayout()
        header.setSpacing(8)
        header.addWidget(self.title_label)
        header.addWidget(self.hint_label)
        header.addStretch(1)
        header.addWidget(self.move_button)
        header.addWidget(self.enable_button)

        self.preview = PreviewWidget(self)

        preview_card = QFrame(self)
        preview_card.setObjectName("Card")
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(1, 1, 1, 1)
        preview_layout.addWidget(self.preview)

        self.tabs = QTabWidget(self)
        self.crosshair_tab = CrosshairTab(controller, self)
        self.image_tab = ImageTab(controller, self)
        self.position_tab = PositionTab(controller, self)
        self.hotkeys_tab = HotkeysTab(controller, self)
        self.profiles_tab = ProfilesTab(controller, self)
        self.tabs.addTab(self.crosshair_tab, "Crosshair")
        self.tabs.addTab(self.image_tab, "Image")
        self.tabs.addTab(self.position_tab, "Position")
        self.tabs.addTab(self.hotkeys_tab, "Hotkeys")
        self.tabs.addTab(self.profiles_tab, "Profiles")

        self.status_label = QLabel("", self)
        self.status_label.setObjectName("Status")
        self.status_label.setWordWrap(True)

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 10)
        layout.setSpacing(10)
        layout.addLayout(header)
        layout.addWidget(preview_card)
        layout.addWidget(self.tabs, 1)
        layout.addWidget(self.status_label)
        self.setCentralWidget(central)

        self.enable_button.clicked.connect(self._on_enable_clicked)
        self.move_button.clicked.connect(self._on_move_clicked)

        controller.profile_changed.connect(self._on_profile_changed)
        controller.enabled_changed.connect(self._on_enabled_changed)
        controller.move_mode_changed.connect(self._on_move_mode_changed)
        controller.status_message.connect(self._on_status)
        controller.active_profile_changed.connect(self._on_active_profile)

        self._geometry = self._stored_geometry()
        self._restore_geometry()
        self._on_enabled_changed(controller.enabled)
        self._on_move_mode_changed(controller.move_mode)
        self._on_active_profile(controller.active_profile)
        self._update_hint()

        # Window managers that tile every window keep resizing the panel.
        self._guard_timer = QTimer(self)
        self._guard_timer.setInterval(1000)
        self._guard_timer.timeout.connect(self._guard_geometry)
        self._guard_timer.start()

    def _restore_geometry(self) -> None:
        """Apply the preferred geometry to the panel."""
        self.setGeometry(self._geometry)

    def _stored_geometry(self) -> QRect:
        """Return the geometry the panel should keep, falling back to a default."""
        geometry = self._controller.settings.window_geometry
        if not geometry:
            return QRect(100, 100, 480, 680)
        return QRect(
            int(geometry.get("x", 100)),
            int(geometry.get("y", 100)),
            int(geometry.get("width", 480)),
            int(geometry.get("height", 680)),
        )

    def present(self) -> None:
        """Show the panel and restore the size it was given by the user."""
        self.show()
        self._restore_geometry()
        self.raise_()
        self.activateWindow()
        # A tiling manager can still resize the window while it appears.
        QTimer.singleShot(0, self._restore_geometry)

    def _guard_geometry(self) -> None:
        """Put the panel back when something else moved or resized it."""
        if QApplication.mouseButtons() != Qt.NoButton:
            return
        if self.geometry() != self._geometry:
            self.setGeometry(self._geometry)

    def resizeEvent(self, event) -> None:  # Qt naming convention.
        """Undo a resize that was not requested by the user."""
        if QApplication.mouseButtons() == Qt.NoButton:
            if event.size() != self._geometry.size():
                self._restore_geometry()
                return
        else:
            self._geometry.setSize(event.size())
        super().resizeEvent(event)

    def moveEvent(self, event) -> None:  # Qt naming convention.
        """Undo a move that was not requested by the user."""
        if QApplication.mouseButtons() == Qt.NoButton:
            if event.pos() != self._geometry.topLeft():
                self._restore_geometry()
                return
        else:
            self._geometry.moveTopLeft(event.pos())
        super().moveEvent(event)

    def _update_hint(self) -> None:
        toggle = self._controller.settings.hotkeys.get("toggle")
        move = self._controller.settings.hotkeys.get("move_mode")
        self.hint_label.setText(f"toggle {toggle}   move {move}")

    def show_and_raise(self) -> None:
        """Bring the panel to the front."""
        self.present()

    def closeEvent(self, event: QCloseEvent) -> None:  # Qt naming convention.
        """Hide to the system tray instead of quitting when possible."""
        geometry = self._geometry
        self._controller.settings.window_geometry = {
            "x": geometry.x(),
            "y": geometry.y(),
            "width": geometry.width(),
            "height": geometry.height(),
        }
        self._controller.save_settings()
        if QSystemTrayIcon.isSystemTrayAvailable():
            event.ignore()
            self.hide()
            return
        event.accept()

    def _on_enable_clicked(self) -> None:
        if self._controller.enabled != self.enable_button.isChecked():
            self._controller.toggle_enabled()

    def _on_move_clicked(self) -> None:
        if self._controller.move_mode != self.move_button.isChecked():
            self._controller.toggle_move_mode()

    def _on_profile_changed(self) -> None:
        self.preview.set_profile(self._controller.active_profile)

    def _on_active_profile(self, profile) -> None:
        self.preview.set_profile(profile)
        self.profiles_tab.reload()

    def _on_enabled_changed(self, enabled: bool) -> None:
        self.enable_button.setChecked(enabled)
        self.enable_button.setText("Crosshair: On" if enabled else "Crosshair: Off")
        self.preview.setVisible(True)

    def _on_move_mode_changed(self, enabled: bool) -> None:
        self.move_button.setChecked(enabled)

    def _on_status(self, message: str) -> None:
        self.status_label.setText(message)

    def refresh_hotkey_hint(self) -> None:
        """Update the shortcut shown in the header."""
        self._update_hint()


__all__ = ["HOTKEY_ACTIONS", "MainWindow"]

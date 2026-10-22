"""Application bootstrap: single instance guard, tray icon and main window."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QAction
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .core.controller import Controller
from .icon import app_icon
from .ui.main_window import MainWindow
from .ui.theme import build_stylesheet

SERVER_NAME = "os-overlay-single-instance"


class SingleInstance(QObject):
    """Guards against running a second copy of the application."""

    activated = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._server: QLocalServer | None = None
        self._connections: list[QLocalSocket] = []

    def claim(self) -> bool:
        """Return True when this process owns the single instance slot."""
        probe = QLocalSocket()
        probe.connectToServer(SERVER_NAME)
        if probe.waitForConnected(300):
            probe.write(b"show")
            probe.flush()
            probe.waitForBytesWritten(300)
            probe.disconnectFromServer()
            return False
        QLocalServer.removeServer(SERVER_NAME)
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._on_connection)
        self._server.listen(SERVER_NAME)
        return True

    @Slot()
    def _on_connection(self) -> None:
        if self._server is None:
            return
        connection = self._server.nextPendingConnection()
        if connection is None:
            return
        self._connections.append(connection)
        connection.readyRead.connect(self._on_message)
        connection.disconnected.connect(connection.deleteLater)

    @Slot()
    def _on_message(self) -> None:
        """Ask the running instance to show its panel."""
        self.activated.emit()


class OverlayApplication:
    """Wires the controller, the panel and the tray icon together."""

    def __init__(self, arguments: list[str], single_instance: bool = True) -> None:
        self.app = QApplication(arguments)
        self.app.setApplicationName("os-overlay")
        self.app.setApplicationDisplayName("os-overlay")
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setStyleSheet(build_stylesheet())
        self.app.setWindowIcon(app_icon())

        self.instance = SingleInstance(self.app)
        self.is_primary = self.instance.claim() if single_instance else True
        self.controller: Controller | None = None
        self.window: MainWindow | None = None
        self.tray: QSystemTrayIcon | None = None
        self._toggle_action: QAction | None = None
        self._move_action: QAction | None = None

        if not self.is_primary:
            return

        self.controller = Controller()
        self.window = MainWindow(self.controller)
        self.controller.panel_toggle_requested.connect(self.toggle_panel)
        self.controller.enabled_changed.connect(self._on_enabled_changed)
        self.controller.move_mode_changed.connect(self._on_move_mode_changed)

    def run(self) -> int:
        """Start the application and block until it exits."""
        if not self.is_primary or self.window is None:
            return 0
        self.instance.activated.connect(self.show_panel)
        self._build_tray()
        self.window.present()
        return self.app.exec()

    def self_test(self) -> int:
        """Build the panel once and return, used to verify a packaged build."""
        if self.window is None:
            return 0
        self.window.present()
        self.app.processEvents()
        self.window.hide()
        return 0

    def show_panel(self) -> None:
        """Show and focus the control panel."""
        if self.window is not None:
            self.window.show_and_raise()

    def toggle_panel(self) -> None:
        """Hide the panel when it is visible, show it otherwise."""
        if self.window is None:
            return
        if self.window.isVisible():
            self.window.hide()
        else:
            self.show_panel()

    def quit(self) -> None:
        """Stop the application."""
        if self.controller is not None:
            self.controller.save_settings()
            self.controller.hotkeys.unregister_all()
        self.app.quit()

    def _build_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(app_icon(), self.app)
        menu = QMenu()

        self._toggle_action = QAction("Crosshair enabled", menu)
        self._toggle_action.setCheckable(True)
        self._toggle_action.triggered.connect(self._on_tray_toggle)
        menu.addAction(self._toggle_action)

        self._move_action = QAction("Move mode", menu)
        self._move_action.setCheckable(True)
        self._move_action.triggered.connect(self._on_tray_move)
        menu.addAction(self._move_action)

        menu.addSeparator()
        show_action = QAction("Open panel", menu)
        show_action.triggered.connect(self.show_panel)
        menu.addAction(show_action)

        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self.quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()
        self._on_enabled_changed(self.controller.enabled)
        self._on_move_mode_changed(self.controller.move_mode)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_panel()

    def _on_tray_toggle(self, checked: bool) -> None:
        if checked != self.controller.enabled:
            self.controller.toggle_enabled()

    def _on_tray_move(self, checked: bool) -> None:
        if checked != self.controller.move_mode:
            self.controller.toggle_move_mode()

    def _on_enabled_changed(self, enabled: bool) -> None:
        if self._toggle_action is not None:
            self._toggle_action.blockSignals(True)
            self._toggle_action.setChecked(enabled)
            self._toggle_action.blockSignals(False)
        if self.tray is not None:
            self.tray.setToolTip(
                "os-overlay - crosshair is on" if enabled else "os-overlay - crosshair is off"
            )

    def _on_move_mode_changed(self, enabled: bool) -> None:
        if self._move_action is not None:
            self._move_action.blockSignals(True)
            self._move_action.setChecked(enabled)
            self._move_action.blockSignals(False)


__all__ = ["OverlayApplication", "SingleInstance"]

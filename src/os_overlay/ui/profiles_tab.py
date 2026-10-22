"""Tab that manages the saved crosshair profiles."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core.controller import Controller
from ..profile import Profile


class ProfilesTab(QWidget):
    """Lists the stored profiles and offers the usual profile actions."""

    def __init__(self, controller: Controller, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._loading = False

        self.list = QListWidget(self)
        self.list.setMinimumHeight(200)

        self.new_button = QPushButton("New", self)
        self.duplicate_button = QPushButton("Duplicate", self)
        self.rename_button = QPushButton("Rename", self)
        self.delete_button = QPushButton("Delete", self)
        self.import_button = QPushButton("Import...", self)
        self.export_button = QPushButton("Export...", self)
        self.include_assets_check = QCheckBox("Include image files", self)
        self.include_assets_check.setChecked(True)

        buttons = QHBoxLayout()
        buttons.setSpacing(6)
        for button in (
            self.new_button,
            self.duplicate_button,
            self.rename_button,
            self.delete_button,
        ):
            buttons.addWidget(button)
        buttons.addStretch(1)

        transfer = QHBoxLayout()
        transfer.setSpacing(6)
        transfer.addWidget(self.import_button)
        transfer.addWidget(self.export_button)
        transfer.addWidget(self.include_assets_check)
        transfer.addStretch(1)

        hint = QLabel(
            "Profiles are stored as JSON files and can be shared by exporting them.",
            self,
        )
        hint.setObjectName("Subtle")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.addWidget(self.list, 1)
        layout.addLayout(buttons)
        layout.addLayout(transfer)
        layout.addWidget(hint)

        self.list.currentItemChanged.connect(self._on_selection)
        self.list.itemDoubleClicked.connect(lambda _item: None)
        self.new_button.clicked.connect(self._on_new)
        self.duplicate_button.clicked.connect(self._on_duplicate)
        self.rename_button.clicked.connect(self._on_rename)
        self.delete_button.clicked.connect(self._on_delete)
        self.import_button.clicked.connect(self._on_import)
        self.export_button.clicked.connect(self._on_export)

        self._controller.profiles_changed.connect(self.reload)
        self._controller.active_profile_changed.connect(self._select_active)
        self.reload()

    def reload(self) -> None:
        """Rebuild the list from the controller."""
        self._loading = True
        active = self._controller.active_profile
        self.list.clear()
        for profile in self._controller.profiles:
            item = QListWidgetItem(profile.name)
            item.setData(Qt.UserRole, profile.id)
            if active is not None and profile.id == active.id:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            self.list.addItem(item)
        self._loading = False
        self._select_active(active)

    def _select_active(self, profile: Profile | None) -> None:
        if profile is None:
            return
        for index in range(self.list.count()):
            item = self.list.item(index)
            if item.data(Qt.UserRole) == profile.id:
                self._loading = True
                self.list.setCurrentRow(index)
                self._loading = False
                return

    def _selected_profile(self) -> Profile | None:
        item = self.list.currentItem()
        if item is None:
            return None
        wanted = item.data(Qt.UserRole)
        for profile in self._controller.profiles:
            if profile.id == wanted:
                return profile
        return None

    def _on_selection(self, current: QListWidgetItem | None, _previous: object) -> None:
        if self._loading or current is None:
            return
        profile = self._selected_profile()
        if profile is not None:
            self._controller.set_active_profile(profile)

    def _on_new(self) -> None:
        profile = Profile(name="New profile")
        self._controller.add_profile(profile)
        self._controller.set_active_profile(profile)
        self._controller.status_message.emit("Profile created.")

    def _on_duplicate(self) -> None:
        profile = self._selected_profile()
        if profile is None:
            return
        clone = self._controller.duplicate_profile(profile)
        self._controller.set_active_profile(clone)

    def _on_rename(self) -> None:
        profile = self._selected_profile()
        if profile is None:
            return
        name, accepted = QInputDialog.getText(self, "Rename profile", "Name:", text=profile.name)
        if accepted and name.strip():
            self._controller.rename_profile(profile, name)

    def _on_delete(self) -> None:
        profile = self._selected_profile()
        if profile is None:
            return
        answer = QMessageBox.question(
            self,
            "Delete profile",
            f"Delete the profile '{profile.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            self._controller.remove_profile(profile)

    def _on_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import profile", str(Path.home()), "Profiles (*.json);;All files (*)"
        )
        if not path:
            return
        profile = self._controller.import_profile(path)
        if profile is not None:
            self._controller.set_active_profile(profile)

    def _on_export(self) -> None:
        profile = self._selected_profile() or self._controller.active_profile
        if profile is None:
            return
        suggestion = str(Path.home() / f"{profile.name}.json")
        path, _ = QFileDialog.getSaveFileName(
            self, "Export profile", suggestion, "Profiles (*.json)"
        )
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        self._controller.export_profile(profile, path, self.include_assets_check.isChecked())

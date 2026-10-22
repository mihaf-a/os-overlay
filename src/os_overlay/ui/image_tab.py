"""Tab that imports GIFs or image sequences and uses them as the crosshair."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..core.controller import Controller
from ..core.library import import_asset
from ..profile import Profile
from .controls import ValueSlider

IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;All files (*)"
GIF_FILTER = "Animated images (*.gif);;Images (*.png *.jpg *.jpeg *.bmp *.webp);;All files (*)"


class ImageTab(QWidget):
    """Manages the imported media used by an image based profile."""

    def __init__(self, controller: Controller, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._loading = False

        self.use_image_check = QCheckBox("Use an image instead of vector shapes", self)
        self.source_combo = QComboBox(self)
        self.source_combo.addItem("Animated GIF", "gif")
        self.source_combo.addItem("Image sequence", "sequence")

        self.gif_path_label = QLabel("No GIF selected", self)
        self.gif_path_label.setObjectName("Subtle")
        self.gif_path_label.setWordWrap(True)
        self.choose_gif_button = QPushButton("Choose GIF...", self)
        self.clear_gif_button = QPushButton("Clear", self)

        self.frame_list = QListWidget(self)
        self.frame_list.setMinimumHeight(110)
        self.add_files_button = QPushButton("Add images...", self)
        self.add_folder_button = QPushButton("Add folder...", self)
        self.remove_button = QPushButton("Remove", self)
        self.up_button = QPushButton("Up", self)
        self.down_button = QPushButton("Down", self)
        self.clear_button = QPushButton("Clear all", self)

        self.duration_spin = QSpinBox(self)
        self.duration_spin.setRange(16, 2000)
        self.duration_spin.setSingleStep(10)
        self.duration_spin.setSuffix(" ms")
        self.scale_slider = ValueSlider(10, 400, 100, " %", self)
        self.loop_check = QCheckBox("Loop the animation", self)

        form = QFormLayout()
        form.setContentsMargins(14, 14, 14, 14)
        form.setVerticalSpacing(10)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.addRow(self.use_image_check)
        form.addRow("Source", self.source_combo)
        form.addRow("GIF", self.gif_path_label)
        form.addRow("", self._button_row(self.choose_gif_button, self.clear_gif_button))
        form.addRow("Frames", self.frame_list)
        form.addRow(
            "",
            self._button_row(
                self.add_files_button,
                self.add_folder_button,
                self.remove_button,
                self.up_button,
                self.down_button,
                self.clear_button,
            ),
        )
        form.addRow("Frame time", self.duration_spin)
        form.addRow("Scale", self.scale_slider)
        form.addRow("", self.loop_check)

        card = QFrame(self)
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.addLayout(form)

        area = QScrollArea(self)
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        area.setWidget(card)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(area)

        self.use_image_check.toggled.connect(self._on_use_image)
        self.source_combo.currentIndexChanged.connect(self._on_source)
        self.choose_gif_button.clicked.connect(self._on_choose_gif)
        self.clear_gif_button.clicked.connect(self._on_clear_gif)
        self.add_files_button.clicked.connect(self._on_add_files)
        self.add_folder_button.clicked.connect(self._on_add_folder)
        self.remove_button.clicked.connect(self._on_remove_frame)
        self.up_button.clicked.connect(lambda: self._on_move_frame(-1))
        self.down_button.clicked.connect(lambda: self._on_move_frame(1))
        self.clear_button.clicked.connect(self._on_clear_frames)
        self.duration_spin.valueChanged.connect(self._on_duration)
        self.scale_slider.value_changed.connect(self._on_scale)
        self.loop_check.toggled.connect(self._on_loop)

        self._controller.profile_changed.connect(self._reload_profile)
        self.load_profile(self._controller.active_profile)

    def _reload_profile(self) -> None:
        """Reload the active profile after the controller changed it."""
        self.load_profile(self._controller.active_profile)

    def _button_row(self, *buttons: QPushButton) -> QWidget:
        holder = QWidget(self)
        layout = QHBoxLayout(holder)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        for button in buttons:
            layout.addWidget(button)
        layout.addStretch(1)
        return holder

    def load_profile(self, profile: Profile | None) -> None:
        """Show the imported media of a profile."""
        if profile is None:
            return
        self._loading = True
        self.use_image_check.setChecked(profile.style.mode == "image")
        self.source_combo.setCurrentIndex(self.source_combo.findData(profile.image.type))
        self.gif_path_label.setText(profile.image.path or "No GIF selected")
        self.duration_spin.setValue(profile.image.frame_ms)
        self.scale_slider.set_value(round(profile.image.scale * 100))
        self.loop_check.setChecked(profile.image.loop)
        self.frame_list.clear()
        for reference in profile.image.frames:
            self.frame_list.addItem(Path(reference).name)
        self._loading = False
        self._update_enabled()

    def _update_enabled(self) -> None:
        is_gif = self.source_combo.currentData() == "gif"
        self.gif_path_label.setEnabled(is_gif)
        self.choose_gif_button.setEnabled(is_gif)
        self.clear_gif_button.setEnabled(is_gif)
        self.frame_list.setEnabled(not is_gif)
        for button in (
            self.add_files_button,
            self.add_folder_button,
            self.remove_button,
            self.up_button,
            self.down_button,
            self.clear_button,
        ):
            button.setEnabled(not is_gif)

    def _image(self):
        profile = self._controller.active_profile
        return profile.image if profile is not None else None

    def _commit(self) -> None:
        if not self._loading:
            self._controller.commit_profile()

    def _on_use_image(self, checked: bool) -> None:
        profile = self._controller.active_profile
        if profile is not None:
            profile.style.mode = "image" if checked else "shape"
            self._commit()

    def _on_source(self, _index: int) -> None:
        image = self._image()
        if image is not None:
            image.type = self.source_combo.currentData()
            self._update_enabled()
            self._commit()

    def _on_choose_gif(self) -> None:
        image = self._image()
        if image is None:
            return
        start = str(Path.home())
        path, _ = QFileDialog.getOpenFileName(self, "Choose a GIF", start, GIF_FILTER)
        if not path:
            return
        reference = import_asset(path)
        if not reference:
            self._controller.status_message.emit("That file could not be imported.")
            return
        image.type = "gif"
        image.path = reference
        self.source_combo.setCurrentIndex(self.source_combo.findData("gif"))
        self.gif_path_label.setText(reference)
        self._commit()

    def _on_clear_gif(self) -> None:
        image = self._image()
        if image is None:
            return
        image.path = ""
        self.gif_path_label.setText("No GIF selected")
        self._commit()

    def _on_add_files(self) -> None:
        image = self._image()
        if image is None:
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Choose images", str(Path.home()), IMAGE_FILTER
        )
        if not paths:
            return
        for path in paths:
            reference = import_asset(path)
            if reference:
                image.frames.append(reference)
        self._refresh_frames(image.frames)
        self._commit()

    def _on_add_folder(self) -> None:
        image = self._image()
        if image is None:
            return
        folder = QFileDialog.getExistingDirectory(self, "Choose a folder", str(Path.home()))
        if not folder:
            return
        paths = sorted(
            path
            for path in Path(folder).iterdir()
            if path.is_file() and path.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp", ".webp")
        )
        if not paths:
            self._controller.status_message.emit("That folder holds no usable images.")
            return
        for path in paths:
            reference = import_asset(path)
            if reference:
                image.frames.append(reference)
        self._refresh_frames(image.frames)
        self._commit()

    def _on_remove_frame(self) -> None:
        image = self._image()
        if image is None:
            return
        row = self.frame_list.currentRow()
        if row < 0 or row >= len(image.frames):
            return
        image.frames.pop(row)
        self._refresh_frames(image.frames)
        self._commit()

    def _on_move_frame(self, delta: int) -> None:
        image = self._image()
        if image is None:
            return
        row = self.frame_list.currentRow()
        target = row + delta
        if row < 0 or target < 0 or target >= len(image.frames):
            return
        image.frames[row], image.frames[target] = image.frames[target], image.frames[row]
        self._refresh_frames(image.frames)
        self.frame_list.setCurrentRow(target)
        self._commit()

    def _on_clear_frames(self) -> None:
        image = self._image()
        if image is None:
            return
        image.frames.clear()
        self._refresh_frames(image.frames)
        self._commit()

    def _on_duration(self, value: int) -> None:
        image = self._image()
        if image is not None:
            image.frame_ms = value
            self._commit()

    def _on_scale(self, value: int) -> None:
        image = self._image()
        if image is not None:
            image.scale = value / 100.0
            self._commit()

    def _on_loop(self, checked: bool) -> None:
        image = self._image()
        if image is not None:
            image.loop = checked
            self._commit()

    def _refresh_frames(self, frames: list[str]) -> None:
        self.frame_list.clear()
        for reference in frames:
            self.frame_list.addItem(Path(reference).name)

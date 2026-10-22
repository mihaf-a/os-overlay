"""Image and animation loading with a bounded cache of scaled pixmaps."""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

from PySide6.QtCore import QObject, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QImageReader, QMovie, QPixmap

from ..paths import resolve_asset_path
from ..profile import ImageConfig

CacheKey = tuple[str, str, int, int]


class MediaCache:
    """Small LRU cache that keeps decoded and scaled pixmaps around."""

    def __init__(self, capacity: int = 48) -> None:
        self._entries: OrderedDict[CacheKey, QPixmap] = OrderedDict()
        self._capacity = capacity

    def get(self, key: CacheKey) -> QPixmap | None:
        """Return a cached pixmap and mark it as recently used."""
        pixmap = self._entries.get(key)
        if pixmap is not None:
            self._entries.move_to_end(key)
        return pixmap

    def put(self, key: CacheKey, pixmap: QPixmap) -> None:
        """Store a pixmap, evicting the oldest entry when the cache is full."""
        self._entries[key] = pixmap
        self._entries.move_to_end(key)
        while len(self._entries) > self._capacity:
            self._entries.popitem(last=False)

    def clear(self) -> None:
        """Drop every cached pixmap."""
        self._entries.clear()


class MediaPlayer(QObject):
    """Plays a GIF or an ordered sequence of still images."""

    frame_changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._movie: QMovie | None = None
        self._frame_paths: list[str] = []
        self._index = 0
        self._source = ""
        self._cache = MediaCache()
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.PreciseTimer)
        self._timer.timeout.connect(self._advance)

    @property
    def has_content(self) -> bool:
        """Return True when a source is loaded."""
        return self._movie is not None or bool(self._frame_paths)

    @property
    def is_animated(self) -> bool:
        """Return True when the current source has more than one frame."""
        if self._movie is not None:
            return self._movie.frameCount() != 1
        return len(self._frame_paths) > 1

    def load(self, config: ImageConfig) -> bool:
        """Load the configured source, returning True when something was loaded."""
        self.unload()
        if config.type == "gif":
            return self._load_gif(config)
        return self._load_sequence(config)

    def unload(self) -> None:
        """Release the current source and stop any playback."""
        self._timer.stop()
        if self._movie is not None:
            self._movie.stop()
            self._movie.frameChanged.disconnect()
            self._movie.deleteLater()
            self._movie = None
        self._frame_paths = []
        self._index = 0
        self._source = ""
        self._cache.clear()

    def natural_size(self) -> QSize:
        """Return the pixel size of the source material."""
        if self._movie is not None:
            image = self._movie.currentImage()
            return image.size() if not image.isNull() else QSize()
        if self._frame_paths:
            reader = QImageReader(str(resolve_asset_path(self._frame_paths[0])))
            size = reader.size()
            if size.isValid():
                return size
        return QSize()

    def frame_key(self) -> str:
        """Return a unique identifier for the frame that is currently displayed."""
        if self._movie is not None:
            return f"{self._source}#{self._movie.currentFrameNumber()}"
        if self._frame_paths:
            return self._frame_paths[self._index]
        return ""

    def current_pixmap(self) -> QPixmap | None:
        """Return the frame that is currently displayed."""
        if self._movie is not None:
            pixmap = self._movie.currentPixmap()
            return None if pixmap.isNull() else pixmap
        if not self._frame_paths:
            return None
        path = self._frame_paths[self._index]
        key: CacheKey = ("raw", path, 0, 0)
        cached = self._cache.get(key)
        if cached is None:
            cached = QPixmap(str(resolve_asset_path(path)))
            self._cache.put(key, cached)
        return None if cached.isNull() else cached

    def scaled_pixmap(self, width: int, height: int) -> QPixmap | None:
        """Return the current frame scaled to fit the requested size."""
        if width <= 0 or height <= 0:
            return None
        key: CacheKey = ("scaled", self.frame_key(), width, height)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        original = self.current_pixmap()
        if original is None:
            return None
        scaled = original.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        if scaled.isNull():
            return None
        self._cache.put(key, scaled)
        return scaled

    def _load_gif(self, config: ImageConfig) -> bool:
        path = resolve_asset_path(config.path)
        if not Path(path).is_file():
            return False
        movie = QMovie(str(path))
        if not movie.isValid():
            return False
        movie.setCacheMode(QMovie.CacheNone)
        movie.jumpToFrame(0)
        movie.frameChanged.connect(self._on_frame_changed)
        self._movie = movie
        self._source = config.path
        movie.start()
        return True

    def _load_sequence(self, config: ImageConfig) -> bool:
        paths = [reference for reference in config.frames if reference]
        if not paths:
            return False
        self._frame_paths = paths
        self._index = 0
        self._source = paths[0]
        self._timer.start(max(16, config.frame_ms))
        return True

    def _on_frame_changed(self, _frame: int) -> None:
        self.frame_changed.emit()

    def _advance(self) -> None:
        if not self._frame_paths:
            return
        self._index = (self._index + 1) % len(self._frame_paths)
        self.frame_changed.emit()

"""Crosshair profile model, JSON serialization and profile storage."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paths import profiles_dir
from .storage import read_json, write_json

SCHEMA = "os-overlay/profile@1"

SHAPES: tuple[str, ...] = (
    "cross",
    "dot",
    "circle",
    "square",
    "t-square",
    "gap-cross",
    "bracket",
)
IMAGE_TYPES: tuple[str, ...] = ("gif", "sequence")


def now_iso() -> str:
    """Return the current UTC timestamp in ISO 8601 form."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _number(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _clamp(value: Any, low: float, high: float, fallback: float) -> float:
    return max(low, min(high, _number(value, fallback)))


def _int(value: Any, fallback: int) -> int:
    try:
        return round(float(value))
    except (TypeError, ValueError):
        return fallback


def _color(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    if not text.startswith("#") or len(text) not in (4, 7, 9):
        return fallback
    try:
        int(text[1:], 16)
    except ValueError:
        return fallback
    return text


def _screen_name(value: Any, fallback: str = "cursor") -> str:
    """Return a screen reference as text, keeping the index zero intact."""
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


@dataclass
class Style:
    """Vector appearance of a crosshair drawn from primitives."""

    mode: str = "shape"
    shape: str = "cross"
    color: str = "#00ff66"
    opacity: float = 1.0
    thickness: int = 2
    length: int = 9
    gap: int = 4
    dot: bool = True
    dot_size: int = 2
    outline: bool = True
    outline_color: str = "#000000"
    outline_width: int = 1
    taper: float = 0.0
    rotation: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Return the JSON representation of this style."""
        return {
            "mode": self.mode,
            "shape": self.shape,
            "color": self.color,
            "opacity": round(self.opacity, 3),
            "thickness": self.thickness,
            "length": self.length,
            "gap": self.gap,
            "dot": self.dot,
            "dot_size": self.dot_size,
            "outline": self.outline,
            "outline_color": self.outline_color,
            "outline_width": self.outline_width,
            "taper": round(self.taper, 3),
            "rotation": round(self.rotation, 2),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Style:
        """Build a style from JSON data, falling back to defaults for unknown keys."""
        defaults = cls()
        shape = str(data.get("shape", defaults.shape))
        mode = str(data.get("mode", defaults.mode))
        return cls(
            mode=mode if mode in ("shape", "image") else defaults.mode,
            shape=shape if shape in SHAPES else defaults.shape,
            color=_color(data.get("color"), defaults.color),
            opacity=_clamp(data.get("opacity"), 0.0, 1.0, defaults.opacity),
            thickness=max(1, _int(data.get("thickness"), defaults.thickness)),
            length=max(0, _int(data.get("length"), defaults.length)),
            gap=max(0, _int(data.get("gap"), defaults.gap)),
            dot=bool(data.get("dot", defaults.dot)),
            dot_size=max(0, _int(data.get("dot_size"), defaults.dot_size)),
            outline=bool(data.get("outline", defaults.outline)),
            outline_color=_color(data.get("outline_color"), defaults.outline_color),
            outline_width=max(0, _int(data.get("outline_width"), defaults.outline_width)),
            taper=_clamp(data.get("taper"), 0.0, 1.0, defaults.taper),
            rotation=_clamp(data.get("rotation"), -180.0, 180.0, defaults.rotation),
        )


@dataclass
class ImageConfig:
    """Reference to an imported GIF or an ordered sequence of still images."""

    type: str = "gif"
    path: str = ""
    frames: list[str] = field(default_factory=list)
    frame_ms: int = 60
    scale: float = 1.0
    loop: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Return the JSON representation of this image configuration."""
        return {
            "type": self.type,
            "path": self.path,
            "frames": list(self.frames),
            "frame_ms": self.frame_ms,
            "scale": round(self.scale, 3),
            "loop": self.loop,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ImageConfig:
        """Build an image configuration from JSON data."""
        defaults = cls()
        frames = data.get("frames") or []
        if not isinstance(frames, list):
            frames = []
        kind = str(data.get("type", defaults.type))
        return cls(
            type=kind if kind in IMAGE_TYPES else defaults.type,
            path=str(data.get("path", "")),
            frames=[str(item) for item in frames],
            frame_ms=max(16, _int(data.get("frame_ms"), defaults.frame_ms)),
            scale=_clamp(data.get("scale"), 0.05, 20.0, defaults.scale),
            loop=bool(data.get("loop", defaults.loop)),
        )

    @property
    def has_content(self) -> bool:
        """Return True when at least one source image is referenced."""
        if self.type == "sequence":
            return bool(self.frames)
        return bool(self.path)


@dataclass
class Position:
    """Normalized crosshair position inside its screen, where 0.5 is the center."""

    x: float = 0.5
    y: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        """Return the JSON representation of this position."""
        return {"x": round(self.x, 5), "y": round(self.y, 5)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Position:
        """Build a position from JSON data."""
        defaults = cls()
        return cls(
            x=_clamp(data.get("x"), 0.0, 1.0, defaults.x),
            y=_clamp(data.get("y"), 0.0, 1.0, defaults.y),
        )


@dataclass
class Profile:
    """A complete, savable crosshair configuration."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    name: str = "Untitled"
    style: Style = field(default_factory=Style)
    image: ImageConfig = field(default_factory=ImageConfig)
    position: Position = field(default_factory=Position)
    screen: str = "cursor"
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def to_dict(self) -> dict[str, Any]:
        """Return the JSON representation of this profile."""
        return {
            "schema": SCHEMA,
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "style": self.style.to_dict(),
            "image": self.image.to_dict(),
            "position": self.position.to_dict(),
            "screen": self.screen,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Profile:
        """Build a profile from JSON data, ignoring unknown keys."""
        defaults = cls()
        style = data.get("style")
        image = data.get("image")
        position = data.get("position")
        return cls(
            id=str(data.get("id") or uuid.uuid4().hex),
            name=str(data.get("name") or defaults.name),
            style=Style.from_dict(style if isinstance(style, dict) else {}),
            image=ImageConfig.from_dict(image if isinstance(image, dict) else {}),
            position=Position.from_dict(position if isinstance(position, dict) else {}),
            screen=_screen_name(data.get("screen"), defaults.screen),
            created_at=str(data.get("created_at") or defaults.created_at),
            updated_at=str(data.get("updated_at") or defaults.updated_at),
        )

    def duplicate(self, name: str | None = None) -> Profile:
        """Return an independent copy of this profile with a new identity."""
        clone = Profile.from_dict(self.to_dict())
        clone.id = uuid.uuid4().hex
        clone.name = name or f"{self.name} copy"
        clone.created_at = now_iso()
        clone.updated_at = clone.created_at
        return clone

    def touch(self) -> None:
        """Refresh the modification timestamp."""
        self.updated_at = now_iso()


def profile_path(profile_id: str) -> Path:
    """Return the file path used to store a profile."""
    safe = "".join(char for char in profile_id if char.isalnum() or char in "-_")
    return profiles_dir() / f"{safe or 'profile'}.json"


def load_profile(path: Path) -> Profile | None:
    """Load a profile from disk, returning None when the file is unusable."""
    data = read_json(path)
    if not isinstance(data, dict):
        return None
    try:
        return Profile.from_dict(data)
    except (TypeError, ValueError):
        return None


def save_profile(profile: Profile) -> Path:
    """Write a profile to disk atomically."""
    path = profile_path(profile.id)
    profile.touch()
    write_json(path, profile.to_dict())
    return path


def list_profiles() -> list[Profile]:
    """Return every stored profile, sorted by name."""
    directory = profiles_dir()
    if not directory.is_dir():
        return []
    found: list[Profile] = []
    for path in sorted(directory.glob("*.json")):
        profile = load_profile(path)
        if profile is not None:
            found.append(profile)
    return sorted(found, key=lambda item: item.name.lower())


def delete_profile(profile: Profile) -> None:
    """Remove a profile from disk."""
    profile_path(profile.id).unlink(missing_ok=True)

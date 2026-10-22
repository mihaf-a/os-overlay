"""Import and export of profiles and image assets."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from pathlib import Path

from ..paths import assets_dir, relative_asset_path, resolve_asset_path
from ..profile import Profile
from ..storage import read_json, write_json

IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".svg")


def import_asset(source: str | Path) -> str:
    """Copy an image into the asset folder and return its stored reference."""
    origin = Path(source)
    if not origin.is_file():
        return ""
    assets_dir().mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(str(origin.resolve()).encode("utf-8")).hexdigest()[:12]
    suffix = origin.suffix.lower()
    if suffix not in IMAGE_SUFFIXES:
        suffix = ".png"
    target = assets_dir() / f"{digest}{suffix}"
    if not target.exists():
        shutil.copy2(origin, target)
    return relative_asset_path(target)


def _relocate(reference: str, base_dir: Path) -> str:
    """Copy a referenced asset into the asset folder, preferring nearby files."""
    if not reference:
        return reference
    candidate = Path(reference)
    if candidate.is_absolute():
        return import_asset(candidate) or reference
    nearby = base_dir / candidate
    if nearby.is_file():
        return import_asset(nearby) or reference
    stored = resolve_asset_path(candidate)
    if stored.is_file():
        return import_asset(stored) or reference
    return reference


def import_profile_file(path: str | Path) -> Profile | None:
    """Read a profile from disk and pull its assets into the asset folder."""
    source = Path(path)
    data = read_json(source)
    if not isinstance(data, dict):
        return None
    try:
        profile = Profile.from_dict(data)
    except (TypeError, ValueError):
        return None

    profile.id = uuid.uuid4().hex
    if profile.image.type == "gif":
        profile.image.path = _relocate(profile.image.path, source.parent)
    else:
        profile.image.frames = [
            _relocate(reference, source.parent) for reference in profile.image.frames
        ]
    return profile


def export_profile_file(profile: Profile, path: str | Path, include_assets: bool = True) -> None:
    """Write a profile to disk, optionally copying the images it references."""
    target = Path(path)
    data = profile.to_dict()
    image = data["image"]

    if include_assets and profile.image.has_content:
        references = (
            [profile.image.path] if profile.image.type == "gif" else list(profile.image.frames)
        )
        relocated: list[str] = []
        for reference in references:
            absolute = resolve_asset_path(reference)
            if absolute.is_file():
                destination = target.parent / absolute.name
                if not destination.exists():
                    shutil.copy2(absolute, destination)
                relocated.append(absolute.name)
            else:
                relocated.append(reference)
        if profile.image.type == "gif":
            image["path"] = relocated[0] if relocated else ""
        else:
            image["frames"] = relocated

    write_json(target, data)

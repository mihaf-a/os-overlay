"""Small helpers for reading and writing JSON documents safely."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any = None) -> Any:
    """Read a JSON document, returning ``default`` when the file is missing or broken."""
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return default


def write_json(path: Path, payload: Any) -> None:
    """Write a JSON document atomically so a crash cannot truncate the file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    name = ""
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=str(path.parent),
            prefix=path.name,
            suffix=".tmp",
            delete=False,
        ) as temporary:
            name = temporary.name
            json.dump(payload, temporary, indent=2, ensure_ascii=False)
            temporary.write("\n")
        os.replace(name, path)
    except BaseException:
        if name:
            Path(name).unlink(missing_ok=True)
        raise

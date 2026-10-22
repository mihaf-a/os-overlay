"""Interface implemented by platform specific global hotkey providers."""

from __future__ import annotations

from typing import Callable, Protocol

HotkeyCallback = Callable[[], None]


class HotkeyBackend(Protocol):
    """Registers system-wide hotkeys for the running session."""

    def register(self, modifiers: frozenset[str], key: str, callback: HotkeyCallback) -> str | None:
        """Register a hotkey, returning an error message or None when successful."""
        ...

    def unregister_all(self) -> None:
        """Remove every hotkey registered through this backend."""
        ...

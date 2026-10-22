"""Fallback hotkey backend used on platforms without a native implementation."""

from __future__ import annotations

from typing import Callable

MESSAGE = "Global hotkeys are only supported on Windows."


class NullHotkeyBackend:
    """Accepts registrations but never fires, keeping the rest of the app usable."""

    def register(
        self, modifiers: frozenset[str], key: str, callback: Callable[[], None]
    ) -> str | None:
        """Report that hotkeys are unavailable on this platform."""
        return MESSAGE

    def unregister_all(self) -> None:
        """Do nothing, there is nothing to unregister."""
        return None

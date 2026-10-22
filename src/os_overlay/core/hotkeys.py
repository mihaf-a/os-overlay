"""Global hotkey bindings: parsing, formatting and session registration."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal

from ..backends.base import HotkeyBackend

MODIFIER_ORDER: tuple[str, ...] = ("Ctrl", "Alt", "Shift", "Win")

MODIFIER_ALIASES: dict[str, str] = {
    "ctrl": "Ctrl",
    "control": "Ctrl",
    "alt": "Alt",
    "option": "Alt",
    "shift": "Shift",
    "win": "Win",
    "meta": "Win",
    "super": "Win",
    "windows": "Win",
}

KEY_ALIASES: dict[str, str] = {
    "space": "Space",
    "spacebar": "Space",
    "enter": "Enter",
    "return": "Enter",
    "esc": "Escape",
    "escape": "Escape",
    "backspace": "Backspace",
    "del": "Delete",
    "delete": "Delete",
    "ins": "Insert",
    "insert": "Insert",
    "home": "Home",
    "end": "End",
    "pageup": "PageUp",
    "pgup": "PageUp",
    "pagedown": "PageDown",
    "pgdn": "PageDown",
    "up": "Up",
    "down": "Down",
    "left": "Left",
    "right": "Right",
    "print": "Print",
    "printscreen": "Print",
    "prtsc": "Print",
    "pause": "Pause",
    "numlock": "NumLock",
    "scrolllock": "ScrollLock",
    "capslock": "CapsLock",
    "apps": "Apps",
    "sleep": "Sleep",
    "plus": "+",
    "minus": "-",
    "equal": "=",
    "comma": ",",
    "period": ".",
    "slash": "/",
    "backslash": "\\",
    "semicolon": ";",
    "apostrophe": "'",
    "grave": "`",
    "bracketleft": "[",
    "bracketright": "]",
    "mouse1": "Mouse1",
    "mouse2": "Mouse2",
    "mouse3": "Mouse3",
    "mouse4": "Mouse4",
    "mouse5": "Mouse5",
    "mbutton": "Mouse3",
    "xbutton1": "Mouse4",
    "xbutton2": "Mouse5",
}


@dataclass(frozen=True)
class HotkeyBinding:
    """A modifier set combined with a single non-modifier key."""

    modifiers: frozenset[str]
    key: str

    def __str__(self) -> str:
        return format_binding(self.modifiers, self.key)


def normalize_key(name: str) -> str | None:
    """Return the canonical name of a key, or None when it is not supported."""
    text = str(name or "").strip()
    if not text:
        return None
    lowered = text.lower()
    if lowered in KEY_ALIASES:
        return KEY_ALIASES[lowered]
    if len(text) == 1 and (text.isalpha() or text.isdigit()):
        return text.upper()
    upper = text.upper()
    if upper.startswith("F") and upper[1:].isdigit() and 1 <= int(upper[1:]) <= 24:
        return upper
    if upper.startswith("NUM") and upper[3:].isdigit() and 0 <= int(upper[3:]) <= 9:
        return f"Num{upper[3:]}"
    if upper in {"MUL", "MULTIPLY"}:
        return "NumMultiply"
    if upper in {"ADD"}:
        return "NumAdd"
    if upper in {"SUB", "SUBTRACT"}:
        return "NumSubtract"
    if upper in {"DEC", "DECIMAL"}:
        return "NumDecimal"
    if upper in {"DIV", "DIVIDE"}:
        return "NumDivide"
    if text in {
        ";",
        "=",
        ",",
        "-",
        ".",
        "/",
        "`",
        "[",
        "\\",
        "]",
        "'",
        "+",
    }:
        return text
    return None


def format_binding(modifiers: Iterable[str], key: str) -> str:
    """Render a modifier set and key as a human readable shortcut string."""
    chosen = {str(item) for item in modifiers}
    parts = [name for name in MODIFIER_ORDER if name in chosen]
    parts.append(str(key))
    return "+".join(parts)


def parse_binding(text: str) -> HotkeyBinding | None:
    """Parse a shortcut string such as ``Ctrl+Alt+H`` into a binding."""
    raw = str(text or "").strip()
    if not raw:
        return None
    parts = [part.strip() for part in raw.split("+")]
    if len(parts) > 1 and parts[-1] == "":
        parts = parts[:-1]
        while parts and parts[-1] == "":
            parts.pop()
        parts.append("+")
    if not parts:
        return None

    modifiers: set[str] = set()
    key: str | None = None
    for part in parts:
        if not part:
            return None
        modifier = MODIFIER_ALIASES.get(part.lower())
        if modifier is not None and key is None:
            modifiers.add(modifier)
            continue
        if key is not None:
            return None
        key = normalize_key(part)
    if key is None:
        return None
    return HotkeyBinding(frozenset(modifiers), key)


class HotkeyManager(QObject):
    """Registers the application's global shortcuts and reports activations."""

    activated = Signal(str)

    def __init__(self, backend: HotkeyBackend, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._backend = backend
        self._bindings: dict[str, str] = {}

    @property
    def bindings(self) -> dict[str, str]:
        """Return the currently registered bindings keyed by action."""
        return dict(self._bindings)

    def apply(self, bindings: dict[str, str]) -> dict[str, str]:
        """Register every binding, returning a mapping of action to error message."""
        self._backend.unregister_all()
        self._bindings = {}
        errors: dict[str, str] = {}
        for action, text in bindings.items():
            parsed = parse_binding(text)
            if parsed is None:
                errors[action] = "This shortcut is not valid."
                continue
            error = self._backend.register(
                parsed.modifiers,
                parsed.key,
                lambda action=action: self.activated.emit(action),
            )
            if error:
                errors[action] = error
                continue
            self._bindings[action] = str(text)
        return errors

    def unregister_all(self) -> None:
        """Remove every registered shortcut."""
        self._backend.unregister_all()
        self._bindings = {}

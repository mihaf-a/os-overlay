"""Dark theme colours and the application stylesheet."""

BACKGROUND = "#15171c"
SURFACE = "#1c1f26"
SURFACE_ALT = "#232732"
BORDER = "#2f3542"
TEXT = "#e7e9ef"
MUTED = "#8d95a8"
ACCENT = "#4ade80"
ACCENT_DARK = "#2f9e5c"
DANGER = "#f87171"

STYLESHEET = """
QWidget {
    background-color: BACKGROUND;
    color: TEXT;
    font-size: 12px;
}

QToolTip {
    background-color: SURFACE_ALT;
    color: TEXT;
    border: 1px solid BORDER;
    padding: 4px;
}

QFrame#Card {
    background-color: SURFACE;
    border: 1px solid BORDER;
    border-radius: 8px;
}

QLabel#Title {
    font-size: 15px;
    font-weight: 600;
    color: TEXT;
}

QLabel#Subtle {
    color: MUTED;
}

QLabel#Status {
    color: MUTED;
    padding: 2px 4px;
}

QPushButton {
    background-color: SURFACE_ALT;
    border: 1px solid BORDER;
    border-radius: 6px;
    padding: 6px 12px;
    color: TEXT;
}

QPushButton:hover {
    border-color: ACCENT_DARK;
    background-color: SURFACE_ALT;
}

QPushButton:pressed {
    background-color: BORDER;
}

QPushButton:disabled {
    color: MUTED;
    border-color: BORDER;
}

QPushButton#Primary {
    background-color: ACCENT;
    border: 1px solid ACCENT;
    color: #10130f;
    font-weight: 600;
}

QPushButton#Primary:hover {
    background-color: #63e894;
}

QPushButton#Danger:hover {
    border-color: DANGER;
    color: DANGER;
}

QPushButton#Record {
    background-color: SURFACE_ALT;
    border: 1px solid BORDER;
    border-radius: 6px;
    padding: 4px 10px;
    font-family: "Consolas", monospace;
}

QPushButton#Record:checked {
    border-color: ACCENT;
    color: ACCENT;
}

QComboBox, QSpinBox, QLineEdit {
    background-color: SURFACE_ALT;
    border: 1px solid BORDER;
    border-radius: 6px;
    padding: 4px 8px;
    color: TEXT;
    selection-background-color: ACCENT_DARK;
}

QComboBox:hover, QSpinBox:hover, QLineEdit:hover {
    border-color: ACCENT_DARK;
}

QComboBox::drop-down {
    border: none;
    width: 18px;
}

QComboBox QAbstractItemView {
    background-color: SURFACE_ALT;
    border: 1px solid BORDER;
    selection-background-color: ACCENT_DARK;
    outline: none;
}

QCheckBox, QRadioButton {
    spacing: 8px;
    color: TEXT;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 15px;
    height: 15px;
    border: 1px solid BORDER;
    border-radius: 4px;
    background-color: SURFACE_ALT;
}

QRadioButton::indicator {
    border-radius: 8px;
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: ACCENT;
    border-color: ACCENT;
}

QSlider::groove:horizontal {
    height: 4px;
    background: BORDER;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: ACCENT;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: TEXT;
    width: 12px;
    margin: -5px 0;
    border-radius: 6px;
}

QTabWidget::pane {
    border: 1px solid BORDER;
    border-radius: 8px;
    background-color: SURFACE;
    top: -1px;
}

QTabBar::tab {
    background: transparent;
    color: MUTED;
    padding: 7px 14px;
    margin-right: 2px;
    border: 1px solid transparent;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    color: TEXT;
    background-color: SURFACE;
    border-color: BORDER;
    border-bottom-color: SURFACE;
}

QTabBar::tab:hover {
    color: TEXT;
}

QListWidget {
    background-color: SURFACE_ALT;
    border: 1px solid BORDER;
    border-radius: 6px;
    outline: none;
    padding: 4px;
}

QListWidget::item {
    padding: 6px;
    border-radius: 4px;
}

QListWidget::item:selected {
    background-color: ACCENT_DARK;
    color: TEXT;
}

QListWidget::item:hover {
    background-color: BORDER;
}

QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: BORDER;
    border-radius: 5px;
    min-height: 24px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}
"""


def build_stylesheet() -> str:
    """Return the stylesheet with the palette applied."""
    replacements = {
        "BACKGROUND": BACKGROUND,
        "SURFACE_ALT": SURFACE_ALT,
        "SURFACE": SURFACE,
        "BORDER": BORDER,
        "TEXT": TEXT,
        "MUTED": MUTED,
        "ACCENT": ACCENT,
        "ACCENT_DARK": ACCENT_DARK,
        "DANGER": DANGER,
    }
    sheet = STYLESHEET
    for key, value in replacements.items():
        sheet = sheet.replace(key, value)
    return sheet

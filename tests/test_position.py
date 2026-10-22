"""Tests for the precise positioning of the crosshair."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import QKeyEvent

from os_overlay.core.controller import Controller
from os_overlay.core.overlay import OverlayWindow
from os_overlay.ui.position_tab import PositionTab


def _controller(qt_app, data_home) -> Controller:
    """Return a controller with a loaded profile."""
    controller = Controller()
    qt_app.processEvents()
    return controller


def test_the_crosshair_starts_in_the_centre_of_the_screen(qt_app, data_home):
    controller = _controller(qt_app, data_home)

    assert controller.position_pixels() == (0, 0)


def test_a_pixel_offset_moves_the_crosshair(qt_app, data_home):
    controller = _controller(qt_app, data_home)

    controller.set_position_pixels(40, -25)

    assert controller.position_pixels() == (40, -25)


def test_a_pixel_offset_is_stored_in_the_profile(qt_app, data_home):
    controller = _controller(qt_app, data_home)
    width, height = controller.overlay.target_screen_size()

    controller.set_position_pixels(40, -25)

    profile = controller.active_profile
    assert profile is not None
    assert profile.position.x == 0.5 + 40 / width
    assert profile.position.y == 0.5 - 25 / height


def test_the_offset_is_limited_to_the_screen(qt_app, data_home):
    controller = _controller(qt_app, data_home)
    width, height = controller.overlay.target_screen_size()

    controller.set_position_pixels(width * 10, height * 10)

    profile = controller.active_profile
    assert profile is not None
    assert profile.position.x == 1.0
    assert profile.position.y == 1.0


def test_nudging_moves_the_crosshair_by_one_pixel(qt_app, data_home):
    controller = _controller(qt_app, data_home)

    controller.nudge_position(1, -1)

    assert controller.position_pixels() == (1, -1)


def test_the_nudge_step_is_stored_and_applied(qt_app, data_home):
    controller = _controller(qt_app, data_home)

    controller.set_nudge_step(5)

    assert controller.settings.nudge_step == 5
    assert controller.overlay.nudge_step == 5


def test_the_nudge_step_is_kept_between_sessions(qt_app, data_home):
    controller = _controller(qt_app, data_home)
    controller.set_nudge_step(7)

    second = Controller()

    assert second.settings.nudge_step == 7


def test_the_tab_shows_the_current_offset(qt_app, data_home):
    controller = _controller(qt_app, data_home)
    controller.set_position_pixels(12, -34)

    tab = PositionTab(controller)

    assert tab.x_spin.value() == 12
    assert tab.y_spin.value() == -34


def test_the_arrow_buttons_move_the_crosshair(qt_app, data_home):
    controller = _controller(qt_app, data_home)
    tab = PositionTab(controller)

    tab.right_button.click()
    tab.down_button.click()

    assert controller.position_pixels() == (1, 1)


def test_the_arrow_buttons_use_the_chosen_step(qt_app, data_home):
    controller = _controller(qt_app, data_home)
    tab = PositionTab(controller)
    tab.step_spin.setValue(10)

    tab.right_button.click()
    tab.up_button.click()

    assert controller.position_pixels() == (10, -10)


def test_the_centre_button_returns_to_the_middle(qt_app, data_home):
    controller = _controller(qt_app, data_home)
    tab = PositionTab(controller)
    tab.right_button.click()

    tab.centre_button.click()

    assert controller.position_pixels() == (0, 0)


def test_typing_an_offset_moves_the_crosshair(qt_app, data_home):
    controller = _controller(qt_app, data_home)
    tab = PositionTab(controller)

    tab.x_spin.setValue(75)
    tab.y_spin.setValue(-60)

    assert controller.position_pixels() == (75, -60)


def test_the_screen_can_be_changed(qt_app, data_home):
    controller = _controller(qt_app, data_home)
    tab = PositionTab(controller)

    tab.screen_combo.setCurrentIndex(tab.screen_combo.findData("0"))

    profile = controller.active_profile
    assert profile is not None
    assert profile.screen == "0"


def test_the_arrow_keys_move_the_crosshair_by_the_step(qt_app, data_home):
    window = OverlayWindow()
    window.set_move_mode(True)
    window.set_nudge_step(8)
    window.show()
    expected = window.pos() + QPoint(8, 0)

    window.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Right, Qt.NoModifier))

    assert window.pos() == expected


def test_the_arrow_keys_move_the_crosshair_faster_with_shift(qt_app, data_home):
    window = OverlayWindow()
    window.set_move_mode(True)
    window.set_nudge_step(8)
    window.show()
    expected = window.pos() + QPoint(0, -80)

    window.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Up, Qt.ShiftModifier))

    assert window.pos() == expected


def test_the_arrow_buttons_move_the_overlay_on_screen(qt_app, data_home):
    controller = _controller(qt_app, data_home)
    controller.set_screen("0")
    tab = PositionTab(controller)
    tab.step_spin.setValue(10)
    window = controller.overlay.window_for_index(0)
    assert window is not None
    before = window.geometry().center()

    tab.right_button.click()

    after = window.geometry().center()
    assert after.x() - before.x() == 10
    assert after.y() == before.y()

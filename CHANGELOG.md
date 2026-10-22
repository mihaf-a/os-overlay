# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Nothing yet.

## [0.2.0] - 2026-10-22

### Added

- A Position tab that places the crosshair with an exact pixel offset from the centre
  of the screen, with arrow buttons for single steps and a configurable step size.
- A configurable nudge step, used by the arrow buttons, the arrow keys in move mode and
  the overlay windows.
- The panel is a floating utility window, so tiling window managers leave it alone.

### Fixed

- The global hotkeys now reach the application again, because the native event filter
  that receives the `WM_HOTKEY` messages is installed on the application object.
- A shortcut that is already taken by another program is reported in the Hotkeys tab
  instead of being dropped during startup.
- A second launch of the application no longer claims the global hotkeys, it only
  hands over to the running instance.
- The panel keeps its size and position when a tiling window manager tries to stretch
  it over the screen.

## [0.1.0] - 2026-10-22

### Added

- Vector crosshairs with the shapes cross, dot, circle, square, t-square, gap-cross
  and bracket.
- Controls for color, opacity, thickness, length, gap, centre dot, outline, taper and
  rotation.
- Import of GIF animations and of ordered image sequences as crosshairs.
- Global hotkeys for toggling the crosshair, opening the panel, entering move mode and
  switching profiles, implemented with the Win32 RegisterHotKey API.
- A live preview panel with a mock background.
- Named profiles with create, duplicate, rename, delete, import and export.
- Multi-monitor support with an option to show the crosshair on every screen.
- Move mode with mouse dragging and arrow key nudging.
- A system tray icon that keeps the application running in the background.
- A portable data directory selected with the `OS_OVERLAY_HOME` environment variable.
- PyInstaller builds as a folder and as a single executable.

[Unreleased]: https://github.com/mihaf-a/os-overlay/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/mihaf-a/os-overlay/releases/tag/v0.2.0
[0.1.0]: https://github.com/mihaf-a/os-overlay/releases

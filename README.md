# os-overlay

A lightweight, highly customizable crosshair overlay for Windows.

os-overlay draws a crosshair on top of your desktop, on top of games and on top of
fullscreen applications. It is built with PySide6, uses the Win32 hotkey API for
system-wide shortcuts and keeps its memory footprint small by drawing into a small
transparent window instead of a fullscreen layer.

## Features

- Vector crosshairs built from seven shapes: cross, dot, circle, square, t-square,
  gap-cross and bracket.
- Full control over color, opacity, thickness, length, gap, dot, outline, taper and
  rotation.
- Import your own crosshair as a GIF animation or as an ordered sequence of images.
- Global hotkeys to toggle the crosshair, open the panel, enter move mode and switch
  profiles without leaving the game.
- A live preview that shows the crosshair on a mock background.
- Named profiles that can be created, duplicated, renamed, imported and exported.
- Multiple monitors, with an option to show the crosshair on every screen at once.
- Precise positioning: type the exact pixel offset from the centre of the screen or
  move the crosshair with the arrow buttons.
- Move mode, where the crosshair can be dragged or nudged with the arrow keys.
- A system tray icon that keeps the application running in the background.
- The panel is a floating utility window, so tiling window managers leave it alone.
- Portable data directory, so the whole configuration can live on a USB stick.

## Requirements

- Windows 10 or Windows 11.
- Python 3.9 or newer when running from source.
- PySide6, installed automatically by pip.

No administrator rights are required. The global hotkeys are registered through the
Win32 `RegisterHotKey` API, which works in the current user session.

## Installation

### From source

```bash
git clone https://github.com/mihaf-a/os-overlay.git
cd os-overlay
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m os_overlay
```

### From a release

Download the archive for your architecture and extract it. The folder build contains
`os-overlay.exe` and all its dependencies, the single file build contains only
`os-overlay.exe`.

## Usage

Start the application and the control panel opens. Closing the panel hides it into the
system tray instead of quitting. Use the tray menu to show the panel, toggle the
crosshair, switch move mode on or off, or quit the application.

The panel behaves like a floating utility window. It keeps the size it was given, stays
out of the taskbar and is ignored by tiling window managers, so it never gets stretched
to fill the screen. Resizing or moving the panel by hand is still possible and the
result is remembered.

### Default hotkeys

| Action | Shortcut |
| --- | --- |
| Toggle the crosshair | `Ctrl+Alt+H` |
| Show or hide the panel | `Ctrl+Alt+O` |
| Move mode | `Ctrl+Alt+M` |
| Previous profile | `Ctrl+Alt+[` |
| Next profile | `Ctrl+Alt+]` |

Every shortcut can be changed in the Hotkeys tab. Click a shortcut field and press the
new combination. A shortcut that is already taken by another program is reported and
the previous binding is kept.

### Move mode

Move mode makes the crosshair draggable with the mouse. Click the crosshair and drag
it to a new position, or select the overlay and use the arrow keys for precise
adjustments. The position is stored per profile as a normalized offset, so it keeps its
place on every screen resolution.

### Positioning

The Position tab places the crosshair exactly where it is needed.

| Control | What it does |
| --- | --- |
| Screen | Picks the screen with the cursor, the primary screen or a specific screen |
| Offset X and Offset Y | Move the crosshair in pixels from the centre of that screen |
| Arrow buttons | Move the crosshair by one step, also available as the arrow keys in move mode |
| Step | Sets the number of pixels a single arrow click moves the crosshair |
| Centre | Puts the crosshair back in the middle of the screen |

The offset is measured from the centre of the screen, so a value of zero places the
crosshair exactly in the middle. Holding shift while using the arrow keys in move mode
moves the crosshair ten steps at once.

## Configuration

Settings, profiles and imported images are stored in the application data directory:

```
%APPDATA%\os-overlay
├── assets
│   └── <hash>.gif
├── profiles
│   └── <profile id>.json
└── settings.json
```

Set the environment variable `OS_OVERLAY_HOME` to use a different directory. Pointing it
at a folder next to the executable turns the application into a portable installation
that keeps all of its data in one place.

Profiles are plain JSON documents and can be edited with any text editor. They can also
be exported and imported from the Profiles tab, which copies the referenced images
along with the profile.

## Building the executable

The build script creates a virtual environment, installs the dependencies and runs
PyInstaller.

```bash
python build.py
```

This produces a folder build in `dist\os-overlay-onedir`. Add `--archive` to also
create a zip file in the `release` folder.

```bash
python build.py --onefile
```

This produces a single `os-overlay.exe` in `dist\os-overlay-onefile`. The single file
build starts a little slower because the resources are extracted to a temporary folder
at launch.

Both builds are configured in `os_overlay.spec`. The unused Qt modules are excluded so
the final size stays small.

## Development

```bash
pip install -r requirements-dev.txt
python -m pytest
python -m ruff check .
python -m ruff format .
```

The source lives in `src\os_overlay`:

| Package | Purpose |
| --- | --- |
| `os_overlay` | Settings, profiles, presets and the data directory layout |
| `os_overlay.core` | Rendering, the overlay windows, media playback and the controller |
| `os_overlay.backends` | Platform specific global hotkey registration |
| `os_overlay.ui` | The control panel widgets |

`os_overlay.core.controller.Controller` is the single source of truth. The widgets read
from it and write through it, and it emits the signals the rest of the application
listens to.

## Known limitations

- Global hotkeys are implemented for Windows only. On other platforms the application
  runs without global shortcuts.
- The crosshair is a topmost window. A few games that draw above other topmost windows
  need the game to run in borderless windowed mode.
- The crosshair follows the cursor when the profile is set to the `cursor` screen. A
  fixed screen can be selected instead.

## License

os-overlay is released under the MIT license. See [LICENSE](LICENSE) for the full text.

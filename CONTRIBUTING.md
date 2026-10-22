# Contributing to os-overlay

Thanks for taking the time to contribute. This document explains how to set up a
development environment, what the project expects from a change, and how to submit it.

## Getting started

```bash
git clone https://github.com/mihaf-a/os-overlay.git
cd os-overlay
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
python -m os_overlay
```

The application needs a Windows session to test the global hotkeys and the overlay.
Everything else, including the renderer and the data layer, is tested headless.

## Running the checks

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

Please run all three before opening a pull request. `ruff format` is the source of
truth for the code style, so run it instead of formatting by hand.

## Code style

- Every file starts with a short docstring that explains what the file is for.
- Public functions and classes have a docstring that starts with a verb and ends with a
  period.
- Comments are rare. Explain why something is done, not what the code already says.
- Type hints are required for public functions.
- The data layer stays free of Qt imports so it can be tested without a display.

## Project layout

| Path | Contents |
| --- | --- |
| `src\os_overlay` | Entry point, settings, profiles, presets and paths |
| `src\os_overlay\core` | Controller, renderer, overlay windows, media and hotkeys |
| `src\os_overlay\backends` | Platform specific global hotkey registration |
| `src\os_overlay\ui` | Widgets of the control panel |
| `tests` | Headless pytest suite |
| `os_overlay.spec` | PyInstaller build configuration |

## Adding a feature

1. Open an issue first for anything larger than a bug fix, so the design can be
   discussed before the code is written.
2. Create a branch from `main`.
3. Add or update the tests that cover the change.
4. Update `README.md` when the user visible behaviour changes, and add an entry to
   `CHANGELOG.md` under the unreleased section.
5. Open a pull request that explains what changed and why.

## Adding a crosshair shape

Shapes live in `src\os_overlay\profile.py` in the `SHAPES` tuple and are drawn in
`src\os_overlay\core\renderer.py`. A shape needs:

- a name in `SHAPES`,
- a branch in `shape_polygons` or `shape_path` that produces the geometry,
- a branch in `content_size` that reports the pixel extent of the shape.

The renderer is shared by the overlay, the preview and the window icon, so a new shape
appears in all three at once.

## Reporting bugs

Please include the Windows version, the application version, the steps that reproduce
the problem, and what you expected to happen. A screenshot of the crosshair in the
preview panel is very helpful for shape and color problems.

## License

By contributing you agree that your work is licensed under the MIT license.

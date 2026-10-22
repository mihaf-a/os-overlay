"""Command line entry point for the os-overlay application."""

from __future__ import annotations

import sys

from . import __version__


def main(argv: list[str] | None = None) -> int:
    """Start the application and return the process exit code."""
    from .app import OverlayApplication

    arguments = list(sys.argv if argv is None else argv)
    if "--version" in arguments:
        print(f"os-overlay {__version__}")
        return 0

    self_test = "--self-test" in arguments
    # The self test ignores the single instance guard so it always builds the panel.
    application = OverlayApplication(arguments, single_instance=not self_test)
    if self_test:
        return application.self_test()
    return application.run()


if __name__ == "__main__":
    raise SystemExit(main())

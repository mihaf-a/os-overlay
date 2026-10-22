"""Entry script used by the PyInstaller build to start os-overlay."""

import sys

from os_overlay.__main__ import main

if __name__ == "__main__":
    sys.exit(main())

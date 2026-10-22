"""Build helper that prepares an environment and runs PyInstaller."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
DIST = ROOT / "dist"
RELEASE = ROOT / "release"


def run(command: list[str], **kwargs) -> None:
    """Run a command and stop the build when it fails."""
    print(">", " ".join(command))
    subprocess.run(command, check=True, **kwargs)


def venv_python() -> Path:
    """Return the interpreter of the build environment, creating it when needed."""
    if os.name == "nt":
        binary = VENV_DIR / "Scripts" / "python.exe"
    else:
        binary = VENV_DIR / "bin" / "python"
    if not binary.exists():
        print("Creating the build environment")
        venv.EnvBuilder(with_pip=True, clear=False).create(VENV_DIR)
    return binary


def install_requirements(python: Path) -> None:
    """Install the runtime and development dependencies."""
    run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(python), "-m", "pip", "install", "-r", "requirements-dev.txt"])


def build(python: Path, onefile: bool, clean: bool) -> Path:
    """Run PyInstaller and return the path of the produced artefact."""
    environment = os.environ.copy()
    environment["OS_OVERLAY_ONEFILE"] = "1" if onefile else "0"
    command = [str(python), "-m", "PyInstaller", "--noconfirm"]
    if clean:
        command.append("--clean")
    command.append(str(ROOT / "os_overlay.spec"))
    run(command, cwd=str(ROOT), env=environment)
    name = "os-overlay-onefile" if onefile else "os-overlay-onedir"
    return DIST / name


def archive(folder: Path) -> Path:
    """Zip a built folder and return the archive path."""
    RELEASE.mkdir(parents=True, exist_ok=True)
    target = RELEASE / f"{folder.name}.zip"
    if target.exists():
        target.unlink()
    shutil.make_archive(str(target.with_suffix("")), "zip", root_dir=str(folder))
    print(f"Created {target}")
    return target


def archive_executable(executable: Path) -> Path:
    """Zip a single executable and return the archive path."""
    RELEASE.mkdir(parents=True, exist_ok=True)
    target = RELEASE / f"{executable.parent.name}.zip"
    if target.exists():
        target.unlink()
    shutil.make_archive(
        str(target.with_suffix("")),
        "zip",
        root_dir=str(executable.parent),
        base_dir=executable.name,
    )
    print(f"Created {target}")
    return target


def main(argv: list[str] | None = None) -> int:
    """Parse the command line and run the requested build."""
    parser = argparse.ArgumentParser(description="Build the os-overlay executable.")
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="build a single executable instead of a folder",
    )
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="skip installing the dependencies",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="remove the PyInstaller cache before building",
    )
    parser.add_argument(
        "--archive",
        action="store_true",
        help="zip the folder build into the release directory",
    )
    arguments = parser.parse_args(argv)

    python = venv_python()
    if not arguments.no_install:
        install_requirements(python)
    output = build(python, arguments.onefile, arguments.clean)
    print(f"Build finished: {output}")
    if arguments.archive:
        if arguments.onefile:
            archive_executable(output / "os-overlay.exe")
        else:
            archive(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
"""
Photo Organizer Development and Testing Script

This script provides convenient commands for development and testing.
"""

import subprocess
import sys
import tempfile
from pathlib import Path


def run_tests():
    """Run the test suite."""
    print("Running tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "photo_organizer/tests/", "-v"],
        cwd=Path(__file__).parent,
        check=False,
    )
    return result.returncode == 0


def lint_code():
    """Run code linting (if flake8 is available)."""
    print("Running code linting...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", "photo_organizer/", "gui/"],
            cwd=Path(__file__).parent,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        print("flake8 not installed, skipping linting")
        return True


def create_test_data():
    """Create sample test data for GUI testing."""
    test_dir = Path(tempfile.gettempdir()) / "photo_organizer_test"
    origin_dir = test_dir / "origin"
    dest_dir = test_dir / "destination"

    origin_dir.mkdir(parents=True, exist_ok=True)
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Create some dummy files for testing
    test_files = [
        "test_photo.jpg",
        "test_video.mov",
        "test_image.png",
        "Thumbs.db",  # This should be deleted
    ]

    for filename in test_files:
        (origin_dir / filename).write_text("dummy test data")

    print("Test data created at:")
    print(f"Origin: {origin_dir}")
    print(f"Destination: {dest_dir}")

    return str(origin_dir), str(dest_dir)


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python dev.py [command]")
        print("Commands:")
        print("  test     - Run tests")
        print("  lint     - Run code linting")
        print("  testdata - Create test data")
        print("  gui      - Launch GUI")
        print("  cli      - Run CLI with test data")
        return

    command = sys.argv[1]

    if command == "test":
        success = run_tests()
        sys.exit(0 if success else 1)

    elif command == "lint":
        success = lint_code()
        sys.exit(0 if success else 1)

    elif command == "testdata":
        origin, dest = create_test_data()
        print("\nYou can now test with:")
        print(f"python run.py -o '{origin}' -d '{dest}'")

    elif command == "gui":
        from gui.photo_organizer_gui import run_gui

        run_gui()

    elif command == "cli":
        origin, dest = create_test_data()
        print("Running CLI with test data...")
        subprocess.run([sys.executable, "run.py", "-o", origin, "-d", dest], check=True)

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()

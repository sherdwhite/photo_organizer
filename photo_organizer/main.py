#!/usr/bin/python3.7
import argparse
import logging
import sys

from photo_organizer import __version__
from photo_organizer.log import setup_logging
from photo_organizer.organize_photos import organize

# Set up basic logging first (will be reconfigured in organize() if needed)
setup_logging("photo_organizer", level="INFO", console_level="INFO")
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the photo organizer application."""
    parser = argparse.ArgumentParser(
        description="Organize photos by EXIF data using CLI or GUI"
    )
    parser.add_argument("--gui", action="store_true", help="Launch GUI interface")
    parser.add_argument(
        "-o",
        "--origin",
        type=str,
        help="Path to the origin directory containing photos",
    )
    parser.add_argument(
        "-d",
        "--destination",
        type=str,
        help="Path to the destination directory where photos will be organized",
    )
    parser.add_argument(
        "--version", action="version", version=f"Photo Organizer {__version__}"
    )

    args = parser.parse_args()

    if args.gui:
        logger.info("Starting photo_organizer GUI. Version %s", __version__)
        try:
            from gui.photo_organizer_gui import run_gui

            return run_gui()
        except ImportError as e:
            logger.error("Failed to import GUI components: %s", e)
            print(
                "Error: GUI components not available. "
                "Please install PyQt6: pip install PyQt6"
            )
            return 1
    else:
        # Command line mode
        logger.info("Starting photo_organizer CLI. Version %s", __version__)
        organize(args.origin, args.destination)
        return 0


def run():
    """Legacy function for backward compatibility."""
    # Check if GUI should be launched (no command line args)
    if len(sys.argv) == 1:
        try:
            from gui.photo_organizer_gui import run_gui

            return run_gui()
        except ImportError:
            # Fall back to CLI if GUI not available
            pass

    logger.info("Starting photo_organizer. Version %s", __version__)
    organize()


if __name__ == "__main__":
    sys.exit(main())

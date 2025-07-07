import argparse
import logging
import os
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


def get_default_pictures_directory() -> str:
    """Get the default Pictures directory for the current user."""
    try:
        # Use the Windows Pictures directory
        pictures_dir = Path.home() / "Pictures"
        return str(pictures_dir)
    except Exception:
        # Fallback to current directory if Pictures directory is not available
        return os.getcwd()


def parse_args() -> Dict[str, str]:
    default_pictures = get_default_pictures_directory()

    parser = argparse.ArgumentParser(description="Organize photos by EXIF data.")
    parser.add_argument(
        "-o",
        "--origin",
        type=str,
        default=os.path.join(default_pictures, "Unsorted"),
        help="Path to the origin directory containing photos.",
    )
    parser.add_argument(
        "-d",
        "--destination",
        type=str,
        default=os.path.join(default_pictures, "Organized"),
        help="Path to the destination directory where photos will be organized.",
    )

    args = parser.parse_args()

    return {"origin_dir": args.origin, "destination_dir": args.destination}

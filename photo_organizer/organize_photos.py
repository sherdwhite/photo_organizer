import logging
import os
import shutil
from datetime import datetime
from struct import error as UnpackError
from typing import Any, Dict, Optional

from photo_organizer.error_handling import log_and_handle_error
from photo_organizer.exif import extract_exif_data
from photo_organizer.file_types.avi import extract_avi_creation_date
from photo_organizer.file_types.gif import extract_gif_creation_date
from photo_organizer.file_types.m4v import extract_m4v_creation_date
from photo_organizer.file_types.mov import extract_mov_creation_date
from photo_organizer.file_types.mp4 import extract_mp4_creation_date
from photo_organizer.file_types.png import extract_png_creation_date
from photo_organizer.file_types.threegp import extract_3gp_creation_date
from photo_organizer.utils import parse_args

logger = logging.getLogger(__name__)

# File type to extraction function mapping
FILE_TYPE_EXTRACTORS = {
    ".mov": extract_mov_creation_date,
    ".png": extract_png_creation_date,
    ".avi": extract_avi_creation_date,
    ".mp4": extract_mp4_creation_date,
    ".3gp": extract_3gp_creation_date,
    ".gif": extract_gif_creation_date,
    ".m4v": extract_m4v_creation_date,
}

# Files to be deleted automatically
FILES_TO_DELETE = {"thumbs.db", "desktop"}


def get_file_creation_date(file_path: str) -> Optional[str]:
    """
    Extract creation date from file based on its extension.

    Args:
        file_path: Full path to the file

    Returns:
        Creation date string in format "YYYY:MM:DD HH:MM:SS" or None
    """
    file_ext = os.path.splitext(file_path)[1].lower()

    # Try specific file type extractors first
    if file_ext == ".mov":
        return extract_mov_creation_date(file_path)
    elif file_ext == ".png":
        return extract_png_creation_date(file_path)
    elif file_ext == ".avi":
        return extract_avi_creation_date(file_path)
    elif file_ext == ".mp4":
        return extract_mp4_creation_date(file_path)
    elif file_ext == ".3gp":
        return extract_3gp_creation_date(file_path)
    elif file_ext == ".gif":
        return extract_gif_creation_date(file_path)
    elif file_ext == ".m4v":
        return extract_m4v_creation_date(file_path)
    else:
        # Fall back to EXIF data for other image types
        try:
            with open(file_path, "rb") as image_file:
                return extract_exif_data(image_file)
        except (OSError, IOError) as e:
            logger.warning("Could not read file %s: %s", file_path, e)
            return None


def should_skip_file(filename: str) -> bool:
    """Check if file should be skipped (deleted or ignored)."""
    return filename.lower() in FILES_TO_DELETE


def create_destination_path(creation_date: str, destination_dir: str) -> str:
    """
    Create destination folder path based on creation date.

    Args:
        creation_date: Date string in format "YYYY:MM:DD HH:MM:SS"
        destination_dir: Base destination directory

    Returns:
        Full path to destination folder
    """
    date = datetime.strptime(creation_date, "%Y:%m:%d %H:%M:%S")
    year = date.year
    month = str(date.month).zfill(2)
    return os.path.join(destination_dir, str(year), month)


def move_file_safely(source_path: str, dest_path: str, filename: str) -> bool:
    """
    Safely move file to destination, handling duplicates.

    Args:
        source_path: Source file path
        dest_path: Destination directory path
        filename: Name of the file

    Returns:
        True if successful, False otherwise
    """
    os.makedirs(dest_path, exist_ok=True)
    file_destination = os.path.join(dest_path, filename)

    try:
        if not os.path.exists(file_destination):
            logger.debug("Moving file %s to %s", filename, file_destination)
            shutil.move(source_path, file_destination)
        else:
            logger.info(
                "File %s already exists at destination, removing source", filename
            )
            os.remove(source_path)
        return True
    except (OSError, IOError, PermissionError) as e:
        logger.error("Failed to move file %s: %s", source_path, e)
        return False


def organize(
    origin_dir: Optional[str] = None, destination_dir: Optional[str] = None
) -> None:
    """
    Organizes photos by moving them into directories based on their creation date.

    This function scans a specified origin directory for photo and video files,
    reads their EXIF data if available or retrieves the creation dates from the
    file metadata for specific file types, such as MOV, PNG, AVI, MP4, 3GP, GIF,
    and M4V. It then moves them into subdirectories within a specified destination
    directory. The subdirectories are named after the year and month the photo or
    video was taken. If a file does not have EXIF data or its creation date
    cannot be determined, an error is logged and the file is moved to an
    `Unknown` directory.

    Parameters:
    origin_dir (Optional[str]): The directory to scan for photos and videos.
    destination_dir (Optional[str]): The directory to move organized photos
                                   and videos to.
    """
    dirs: Dict[str, Any] = parse_args()
    origin_dir = origin_dir or dirs.get("origin_dir")
    destination_dir = destination_dir or dirs.get("destination_dir")
    logger.info("Origin Directory: %s", origin_dir)
    logger.info("Destination Directory: %s", destination_dir)

    # Collect all files first to avoid modification during iteration
    files_to_process = []
    empty_dirs = []

    for root, _, files in os.walk(origin_dir):
        if not files:
            empty_dirs.append(root)
        else:
            for file in files:
                file_path = os.path.join(root, file)
                files_to_process.append((file_path, file))

    # Remove empty directories
    for empty_dir in empty_dirs:
        try:
            os.rmdir(empty_dir)
            logger.info("Removed empty directory: %s", empty_dir)
        except OSError as e:
            logger.warning("Could not remove directory %s: %s", empty_dir, e)

    # Process files
    for file_path, filename in files_to_process:
        # Skip files that should be deleted
        if should_skip_file(filename):
            try:
                os.remove(file_path)
                logger.info("Deleted unwanted file: %s", filename)
            except OSError as e:
                logger.error("Could not delete file %s: %s", file_path, e)
            continue

        logger.info("Processing file: %s", file_path)

        try:
            creation_date = get_file_creation_date(file_path)

            if creation_date:
                dest_folder = create_destination_path(creation_date, destination_dir)

                if move_file_safely(file_path, dest_folder, filename):
                    logger.info("Successfully moved %s to %s", filename, dest_folder)
                else:
                    # Check if file still exists (move_file_safely handles most errors)
                    if os.path.exists(file_path):
                        log_and_handle_error(
                            destination_dir,
                            filename,
                            file_path,
                            f"Failed to move file {filename}",
                        )
            else:
                log_and_handle_error(
                    destination_dir,
                    filename,
                    file_path,
                    f"File {filename} has no extractable creation date.",
                )

        except (ValueError, UnpackError) as ex:
            log_and_handle_error(
                destination_dir,
                filename,
                file_path,
                f"File {filename} has invalid metadata. Error: {ex}",
            )
        except (OSError, IOError, PermissionError) as ex:
            logger.error("Error processing file %s: %s", file_path, ex)

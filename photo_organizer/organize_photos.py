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


def organize(
    origin_dir: Optional[str] = None, destination_dir: Optional[str] = None
) -> None:
    """
    Organizes photos by moving them into directories based on their creation date.

    This function scans a specified origin directory for photo and video files, reads their EXIF
    data if available or retrieves the creation dates from the file metadata for specific file
    types, such as MOV, PNG, AVI, MP4, 3GP, GIF, and M4V. It then moves them into subdirectories
    within a specified destination directory. The subdirectories are named after the year and month
    the photo or video was taken. If a file does not have EXIF data or its creation date cannot be
    determined, an error is logged and the file is moved to an `Unknown` directory.

    Parameters:
    origin_dir (Optional[str]): The directory to scan for photos and videos.
    destination_dir (Optional[str]): The directory to move organized photos and videos to.
    """
    dirs: Dict[str, Any] = parse_args()
    origin_dir = origin_dir or dirs.get("origin_dir")
    destination_dir = destination_dir or dirs.get("destination_dir")
    logger.info("Origin Directory: %s", origin_dir)
    logger.info("Destination Directory: %s", destination_dir)

    for root, subdirs, files in os.walk(origin_dir):
        if not os.listdir(root):
            os.rmdir(root)
            print(f"Removing directory {root}")
        for file in files:
            file_dir = os.path.join(root, file)
            if file in {"Thumbs.db", "desktop"}:
                os.remove(file_dir)
                continue
            print(f"At file: {file_dir}")
            try:
                datetime_original: Optional[str] = None
                if file.lower().endswith(".mov"):
                    datetime_original = extract_mov_creation_date(file_dir)
                elif file.lower().endswith(".png"):
                    datetime_original = extract_png_creation_date(file_dir)
                elif file.lower().endswith(".avi"):
                    datetime_original = extract_avi_creation_date(file_dir)
                elif file.lower().endswith(".mp4"):
                    datetime_original = extract_mp4_creation_date(file_dir)
                elif file.lower().endswith(".3gp"):
                    datetime_original = extract_3gp_creation_date(file_dir)
                elif file.lower().endswith(".gif"):
                    datetime_original = extract_gif_creation_date(file_dir)
                elif file.lower().endswith(".m4v"):
                    datetime_original = extract_m4v_creation_date(file_dir)
                else:
                    with open(file_dir, "rb") as image_file:
                        datetime_original = extract_exif_data(image_file)

                if datetime_original:
                    date: datetime = datetime.strptime(
                        datetime_original, "%Y:%m:%d %H:%M:%S"
                    )
                    year: int = date.year
                    month: str = str(date.month).zfill(2)
                    folder_destination: str = os.path.join(
                        destination_dir, str(year), month
                    )
                    file_destination: str = os.path.join(folder_destination, file)
                    if not os.path.exists(folder_destination):
                        os.makedirs(folder_destination)
                    if not os.path.exists(file_destination):
                        logger.debug("Moving file %s to %s", file, file_destination)
                        shutil.copy(file_dir, file_destination)
                        os.remove(file_dir)
                    else:
                        os.remove(file_dir)
                else:
                    log_and_handle_error(
                        destination_dir,
                        file,
                        file_dir,
                        f"File {file} at location {file_dir} has no exif data.",
                    )
            except (ValueError, UnpackError) as ex:
                log_and_handle_error(
                    destination_dir,
                    file,
                    file_dir,
                    f"File {file} at location {file_dir} has possible bad exif data. Error: {ex}",
                )
            except PermissionError as pe:
                logger.error(
                    "PermissionError: Could not remove file %s at location %s. Error: %s",
                    file,
                    file_dir,
                    pe,
                )
                # Additional debugging information
                logger.debug("Checking if file is closed properly.")
                try:
                    with open(file_dir, "rb") as f:
                        pass
                except Exception as e:
                    logger.error("Error while checking file: %s", e)

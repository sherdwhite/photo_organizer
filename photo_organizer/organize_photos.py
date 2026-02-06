import logging
import os
import re
import shutil
from datetime import datetime
from struct import error as UnpackError
from typing import Optional

from photo_organizer.date_utils import (
    extract_xmp_date,
    get_filesystem_date,
    validate_date,
)
from photo_organizer.error_handling import log_and_handle_error
from photo_organizer.exif import extract_exif_data, extract_exif_via_pillow
from photo_organizer.file_types import ALL_EXTRACTORS
from photo_organizer.file_types.video_extractors import VIDEO_EXTRACTORS
from photo_organizer.log import setup_logging
from photo_organizer.utils import get_default_pictures_directory

logger = logging.getLogger(__name__)

# Use the consolidated extractors registry
FILE_TYPE_EXTRACTORS = ALL_EXTRACTORS

# Extensions where EXIF / Pillow fallbacks are pointless (video files)
_VIDEO_EXTENSIONS = frozenset(VIDEO_EXTRACTORS.keys())

# Files to be deleted automatically
FILES_TO_DELETE = {"thumbs.db", "desktop"}


def extract_date_from_filename(filename: str) -> Optional[str]:
    """
    Extract date from filename patterns.

    Supports patterns from many camera/phone/app naming conventions:
    - IMG_YYYYMMDD_HHMMSS (generic Android)
    - YYYYMMDD_HHMMSS (Samsung, bare date)
    - IMG-YYYYMMDD-HHMMSS (WhatsApp)
    - PXL_YYYYMMDD_HHMMSS (Google Pixel)
    - Screenshot_YYYYMMDD-HHMMSS (Android screenshots)
    - Screenshot YYYY-MM-DD at HH.MM.SS (macOS screenshots)
    - signal-YYYY-MM-DD-HHMMSS (Signal app)
    - YYYY-MM-DD_HH-MM-SS (ISO-ish)
    - YYYYMMDD (date-only fallback)

    Args:
        filename: Name of the file (not the full path)

    Returns:
        Validated creation date string or None
    """
    name_without_ext = os.path.splitext(filename)[0]

    # Pattern 1: Full datetime — YYYYMMDD_HHMMSS or YYYYMMDD-HHMMSS
    # Covers: IMG_20250808_090022, PXL_20250115_103045123,
    #         Screenshot_20250115-103045, 20250115_103045
    pattern1 = r"(\d{4})(\d{2})(\d{2})[_-](\d{2})(\d{2})(\d{2})"
    match = re.search(pattern1, name_without_ext)
    if match:
        year, month, day, hour, minute, second = match.groups()
        dt = _try_build_datetime(year, month, day, hour, minute, second)
        if dt:
            result = dt.strftime("%Y:%m:%d %H:%M:%S")
            logger.debug(
                "Extracted date from filename %s: %s",
                filename,
                result,
            )
            return validate_date(result)

    # Pattern 2: ISO-like — YYYY-MM-DD HH.MM.SS or YYYY-MM-DD-HH-MM-SS
    # Covers: Screenshot 2025-01-15 at 10.30.45,
    #         signal-2025-01-15-103045
    pattern2 = (
        r"(\d{4})-(\d{2})-(\d{2})" r"[\s_at-]*" r"(\d{2})[.\-:](\d{2})[.\-:](\d{2})"
    )
    match = re.search(pattern2, name_without_ext)
    if match:
        year, month, day, hour, minute, second = match.groups()
        dt = _try_build_datetime(year, month, day, hour, minute, second)
        if dt:
            result = dt.strftime("%Y:%m:%d %H:%M:%S")
            logger.debug(
                "Extracted date from filename %s: %s",
                filename,
                result,
            )
            return validate_date(result)

    # Pattern 3: Date only — YYYY-MM-DD or YYYYMMDD
    # (set time to noon as a reasonable default)
    pattern3 = r"(\d{4})[_-]?(\d{2})[_-]?(\d{2})"
    match = re.search(pattern3, name_without_ext)
    if match:
        year, month, day = match.groups()
        dt = _try_build_datetime(year, month, day, "12", "0", "0")
        if dt:
            result = dt.strftime("%Y:%m:%d %H:%M:%S")
            logger.debug(
                "Extracted date from filename %s: %s",
                filename,
                result,
            )
            return validate_date(result)

    return None


def _try_build_datetime(
    year: str,
    month: str,
    day: str,
    hour: str,
    minute: str,
    second: str,
) -> Optional[datetime]:
    """
    Try to construct a datetime, returning None on failure.

    Args:
        year, month, day, hour, minute, second: String components

    Returns:
        datetime object or None if values are invalid
    """
    try:
        return datetime(
            int(year),
            int(month),
            int(day),
            int(hour),
            int(minute),
            int(second),
        )
    except ValueError:
        return None


def get_file_creation_date(file_path: str) -> Optional[str]:
    """
    Extract creation date from file using a multi-level fallback chain.

    The chain tries these sources in order, stopping at the first
    valid result:
      1. Registered file-type extractor (format-specific metadata)
      2. Generic EXIF via the exif library
      3. Pillow EXIF fallback (different parser, catches edge cases)
      4. XMP metadata scan (XML embedded in file)
      5. Filename pattern parsing
      6. File system timestamps (st_birthtime / st_mtime)

    When both metadata and filename yield dates, prefers metadata
    but logs a warning if they disagree by more than a day.

    Args:
        file_path: Full path to the file

    Returns:
        Validated creation date string or None
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    filename = os.path.basename(file_path)
    metadata_date = None

    # --- Step 1: Registered file-type extractor ---
    if file_ext in FILE_TYPE_EXTRACTORS:
        extractor_func = FILE_TYPE_EXTRACTORS[file_ext]
        date = extractor_func(file_path)
        if date:
            metadata_date = date

    # Steps 2–3 only apply to image files; video files have no
    # EXIF/Pillow-readable data, so we skip them to avoid slow I/O.
    is_video = file_ext in _VIDEO_EXTENSIONS

    # --- Step 2: Generic EXIF via exif library ---
    if not metadata_date and not is_video:
        try:
            with open(file_path, "rb") as image_file:
                date = extract_exif_data(image_file)
                if date:
                    metadata_date = date
        except (OSError, IOError, ValueError) as e:
            logger.debug("Could not read EXIF from %s: %s", file_path, e)

    # --- Step 3: Pillow EXIF fallback ---
    if not metadata_date and not is_video:
        date = extract_exif_via_pillow(file_path)
        if date:
            metadata_date = date

    # --- Step 4: XMP metadata ---
    if not metadata_date:
        date = extract_xmp_date(file_path)
        if date:
            metadata_date = date

    # --- Step 5: Filename pattern parsing ---
    filename_date = extract_date_from_filename(filename)

    # Cross-reference: if both metadata and filename have dates,
    # prefer metadata but warn if they disagree significantly
    if metadata_date and filename_date:
        _cross_reference_dates(filename, metadata_date, filename_date)
        return metadata_date

    if metadata_date:
        return metadata_date

    if filename_date:
        logger.info(
            "Using date from filename for %s: %s",
            filename,
            filename_date,
        )
        return filename_date

    # --- Step 6: Filesystem timestamps (last resort) ---
    fs_date = get_filesystem_date(file_path)
    if fs_date:
        logger.info(
            "Using filesystem date for %s: %s",
            filename,
            fs_date,
        )
        return fs_date

    return None


def _cross_reference_dates(
    filename: str,
    metadata_date: str,
    filename_date: str,
) -> None:
    """
    Log a warning if metadata and filename dates disagree.

    A disagreement of more than 1 day often means the file was
    renamed by a messaging app or cloud service, or the metadata
    was reset. The log helps users audit questionable files.

    Args:
        filename: Name of the file
        metadata_date: Date from metadata
        filename_date: Date parsed from filename
    """
    try:
        fmt = "%Y:%m:%d %H:%M:%S"
        dt_meta = datetime.strptime(metadata_date, fmt)
        dt_file = datetime.strptime(filename_date, fmt)
        delta = abs((dt_meta - dt_file).total_seconds())
        if delta > 86400:  # more than 1 day apart
            logger.warning(
                "Date mismatch for %s: metadata=%s, "
                "filename=%s (%.0f hours apart). "
                "Using metadata date.",
                filename,
                metadata_date,
                filename_date,
                delta / 3600,
            )
    except (ValueError, TypeError):
        pass  # Can't compare — not worth logging


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
    origin_dir: Optional[str] = None,
    destination_dir: Optional[str] = None,
    progress_callback=None,
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
    progress_callback (Optional[callable]): Callback function for progress updates.
    """
    # Use default directories if not provided
    if origin_dir is None or destination_dir is None:
        default_pictures = get_default_pictures_directory()
        origin_dir = origin_dir or os.path.join(default_pictures, "Unsorted")
        destination_dir = destination_dir or os.path.join(default_pictures, "Organized")

    # Set up dynamic logging to destination directory if available
    if destination_dir:
        setup_logging("photo_organizer", log_dir=destination_dir)
        logger.info("Logging configured to destination directory: %s", destination_dir)

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

    total_files = len(files_to_process)
    logger.info("Found %d files to process", total_files)
    if progress_callback:
        progress_callback(f"Found {total_files} files to process")

    # Remove empty directories
    for empty_dir in empty_dirs:
        try:
            os.rmdir(empty_dir)
            logger.info("Removed empty directory: %s", empty_dir)
        except OSError as e:
            logger.warning("Could not remove directory %s: %s", empty_dir, e)

    # Process files
    processed_count = 0
    moved_count = 0
    error_count = 0

    for file_path, filename in files_to_process:
        processed_count += 1

        # Skip files that should be deleted
        if should_skip_file(filename):
            try:
                os.remove(file_path)
                logger.info("Deleted unwanted file: %s", filename)
            except OSError as e:
                logger.error("Could not delete file %s: %s", file_path, e)
            continue

        # Only log every 50th file to reduce log spam
        if processed_count % 50 == 0 or processed_count == total_files:
            logger.info(
                "Processing file %d/%d: %s", processed_count, total_files, filename
            )

        # Always update the GUI progress (lightweight status bar update)
        if progress_callback:
            progress_callback(
                f"Processing file {processed_count}/{total_files}: {filename}"
            )

        try:
            creation_date = get_file_creation_date(file_path)

            if creation_date:
                dest_folder = create_destination_path(creation_date, destination_dir)

                if move_file_safely(file_path, dest_folder, filename):
                    moved_count += 1
                    # Only log successful moves occasionally
                    if moved_count % 100 == 0:
                        logger.info("Successfully moved %d files so far", moved_count)
                else:
                    # Check if file still exists (move_file_safely handles most errors)
                    if os.path.exists(file_path):
                        error_count += 1
                        log_and_handle_error(
                            destination_dir,
                            filename,
                            file_path,
                            f"Failed to move file {filename}",
                        )
            else:
                error_count += 1
                log_and_handle_error(
                    destination_dir,
                    filename,
                    file_path,
                    f"File {filename} has no extractable creation date.",
                )

        except (ValueError, UnpackError) as ex:
            error_count += 1
            log_and_handle_error(
                destination_dir,
                filename,
                file_path,
                f"File {filename} has invalid metadata. Error: {ex}",
            )
        except (OSError, IOError, PermissionError) as ex:
            error_count += 1
            logger.error("Error processing file %s: %s", file_path, ex)

    # Final summary
    logger.info(
        "Organization complete: %d files processed, %d moved, %d errors",
        processed_count,
        moved_count,
        error_count,
    )
    if progress_callback:
        progress_callback(
            f"Complete: {processed_count} processed, "
            f"{moved_count} moved, {error_count} errors"
        )

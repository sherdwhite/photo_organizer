"""
File operation utilities for photo organizer.

This module handles all file system operations including safe moves,
directory creation, duplicate handling, and cleanup operations.
"""

import logging
import os
import shutil

logger = logging.getLogger(__name__)


class FileOperationError(Exception):
    """Custom exception for file operation errors."""

    pass


def create_destination_path(creation_date: str, destination_dir: str) -> str:
    """
    Create destination folder path based on creation date.

    Args:
        creation_date: Date string in format "YYYY:MM:DD HH:MM:SS"
        destination_dir: Base destination directory

    Returns:
        Full path to destination folder
    """
    try:
        year, month, _ = creation_date.split(":")[:3]
        return os.path.join(destination_dir, year, month)
    except (ValueError, IndexError) as e:
        logger.error("Invalid date format '%s': %s", creation_date, e)
        return os.path.join(destination_dir, "Unknown")


def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory_path: Path to directory

    Raises:
        FileOperationError: If directory cannot be created
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        logger.debug("Ensured directory exists: %s", directory_path)
    except OSError as e:
        raise FileOperationError(f"Cannot create directory {directory_path}: {e}")


def move_file_safely(source_path: str, dest_path: str, filename: str) -> bool:
    """
    Safely move a file, handling duplicates and errors.

    Args:
        source_path: Source file path
        dest_path: Destination file path
        filename: Original filename for logging

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure destination directory exists
        dest_dir = os.path.dirname(dest_path)
        ensure_directory_exists(dest_dir)

        # Handle duplicate files
        if os.path.exists(dest_path):
            dest_path = _get_unique_filename(dest_path)
            logger.info(
                "File already exists, renamed to: %s", os.path.basename(dest_path)
            )

        # Perform the move
        shutil.move(source_path, dest_path)
        logger.info("Moved file: %s -> %s", filename, dest_path)
        return True

    except (OSError, IOError, shutil.Error) as e:
        logger.error("Error moving file %s: %s", filename, e)
        return False


def _get_unique_filename(file_path: str) -> str:
    """
    Generate a unique filename by appending a counter.

    Args:
        file_path: Original file path

    Returns:
        Unique file path
    """
    base, ext = os.path.splitext(file_path)
    counter = 1

    while os.path.exists(file_path):
        file_path = f"{base}_{counter}{ext}"
        counter += 1

    return file_path


def cleanup_empty_directories(directory_path: str) -> int:
    """
    Remove empty directories recursively.

    Args:
        directory_path: Root directory to clean

    Returns:
        Number of directories removed
    """
    removed_count = 0

    try:
        for root, dirs, files in os.walk(directory_path, topdown=False):
            if not files and not dirs:
                try:
                    os.rmdir(root)
                    logger.info("Removed empty directory: %s", root)
                    removed_count += 1
                except OSError as e:
                    logger.warning("Could not remove directory %s: %s", root, e)

    except OSError as e:
        logger.error("Error during directory cleanup: %s", e)

    return removed_count


def should_skip_file(filename: str, skip_patterns: set) -> bool:
    """
    Check if file should be skipped based on patterns.

    Args:
        filename: File name to check
        skip_patterns: Set of patterns to skip

    Returns:
        True if file should be skipped
    """
    return filename.lower() in skip_patterns


def delete_unwanted_files(directory_path: str, patterns: set) -> int:
    """
    Delete files matching unwanted patterns.

    Args:
        directory_path: Directory to scan
        patterns: Set of filename patterns to delete

    Returns:
        Number of files deleted
    """
    deleted_count = 0

    try:
        for root, _, files in os.walk(directory_path):
            for file in files:
                if should_skip_file(file, patterns):
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        logger.info("Deleted unwanted file: %s", file)
                        deleted_count += 1
                    except OSError as e:
                        logger.error("Could not delete file %s: %s", file, e)

    except OSError as e:
        logger.error("Error during file deletion: %s", e)

    return deleted_count

"""
Video metadata extractors using hachoir library.

This module consolidates all video file type extractors that use the hachoir library
for metadata extraction, reducing code duplication and improving maintainability.
"""

import logging
from datetime import datetime
from typing import Optional

from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

logger = logging.getLogger(__name__)


def _extract_hachoir_creation_date(file_path: str, file_type: str) -> Optional[str]:
    """
    Generic function to extract creation date using hachoir.

    Args:
        file_path: Path to the video file
        file_type: File type for logging (e.g., "MP4", "MOV")

    Returns:
        Creation date string in format "YYYY:MM:DD HH:MM:SS" or None
    """
    try:
        parser = createParser(file_path)
        if not parser:
            logger.warning(
                "Could not create parser for %s file: %s", file_type, file_path
            )
            return None

        with parser:
            metadata = extractMetadata(parser)

        if metadata and metadata.has("creation_date"):
            creation_date: Optional[datetime] = metadata.get("creation_date")
            if creation_date:
                return creation_date.strftime("%Y:%m:%d %H:%M:%S")

        logger.debug("No creation date found in %s file: %s", file_type, file_path)
        return None

    except (OSError, IOError, ValueError) as e:
        logger.error(
            "Error extracting %s creation date from %s: %s", file_type, file_path, e
        )
        return None


def extract_mov_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from MOV file using hachoir."""
    return _extract_hachoir_creation_date(file_path, "MOV")


def extract_mp4_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from MP4 file using hachoir."""
    return _extract_hachoir_creation_date(file_path, "MP4")


def extract_avi_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from AVI file using hachoir."""
    return _extract_hachoir_creation_date(file_path, "AVI")


def extract_m4v_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from M4V file using hachoir."""
    return _extract_hachoir_creation_date(file_path, "M4V")


def extract_3gp_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from 3GP file using hachoir."""
    return _extract_hachoir_creation_date(file_path, "3GP")


# Registry for video extractors
VIDEO_EXTRACTORS = {
    ".mov": extract_mov_creation_date,
    ".mp4": extract_mp4_creation_date,
    ".avi": extract_avi_creation_date,
    ".m4v": extract_m4v_creation_date,
    ".3gp": extract_3gp_creation_date,
}

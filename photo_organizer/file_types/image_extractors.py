"""
Image metadata extractors using PIL library.

This module consolidates all image file type extractors that use the PIL library
for metadata extraction, reducing code duplication and improving maintainability.
"""

import logging
from typing import Optional

from PIL import Image as PILImage

logger = logging.getLogger(__name__)


def _extract_pil_creation_date(
    file_path: str, file_type: str, date_fields: list
) -> Optional[str]:
    """
    Generic function to extract creation date using PIL.

    Args:
        file_path: Path to the image file
        file_type: File type for logging (e.g., "PNG", "GIF")
        date_fields: List of metadata fields to check for date information

    Returns:
        Creation date string in format "YYYY:MM:DD HH:MM:SS" or None
    """
    try:
        with PILImage.open(file_path) as img:
            info = img.info

            # Try different possible date fields
            for date_field in date_fields:
                if date_field in info:
                    date_value = info[date_field]
                    if date_value:
                        logger.debug(
                            "Found %s date in field %s: %s",
                            file_type,
                            date_field,
                            date_value,
                        )
                        return date_value

        logger.debug("No creation date found in %s file: %s", file_type, file_path)
        return None

    except (OSError, IOError, ValueError) as e:
        logger.error(
            "Error extracting %s creation date from %s: %s", file_type, file_path, e
        )
        return None


def extract_png_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from PNG file using PIL."""
    date_fields = ["creation_time", "date:create", "date:modify"]
    return _extract_pil_creation_date(file_path, "PNG", date_fields)


def extract_gif_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from GIF file using PIL."""
    date_fields = ["date:create", "date:modify", "creation_time"]
    return _extract_pil_creation_date(file_path, "GIF", date_fields)


# Registry for image extractors
IMAGE_EXTRACTORS = {
    ".png": extract_png_creation_date,
    ".gif": extract_gif_creation_date,
}

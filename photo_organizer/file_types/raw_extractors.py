"""
RAW image metadata extractors using exifread library.

This module handles all camera RAW file formats, which share the same
TIFF-based EXIF structure and can all be read by exifread.

Supported formats:
- DNG (Adobe Digital Negative)
- CR2 / CR3 (Canon RAW)
- NEF (Nikon RAW)
- ARW (Sony RAW)
- ORF (Olympus RAW)
- RW2 (Panasonic RAW)
- RAF (Fujifilm RAW)
"""

import logging
from typing import Optional

from photo_organizer.date_utils import validate_date

logger = logging.getLogger(__name__)


def _extract_raw_creation_date(file_path: str, file_type: str) -> Optional[str]:
    """
    Extract creation date from a RAW image file using exifread.

    Args:
        file_path: Path to the RAW image file
        file_type: File type for logging (e.g., "CR2", "NEF")

    Returns:
        Validated creation date string, or None
    """
    try:
        import exifread

        with open(file_path, "rb") as f:
            tags = exifread.process_file(f, stop_tag="DateTimeOriginal", details=False)

        # Try date tags in priority order
        date_tag_names = [
            "EXIF DateTimeOriginal",
            "EXIF DateTimeDigitized",
            "Image DateTime",
        ]

        for tag_name in date_tag_names:
            if tag_name in tags:
                date_value = str(tags[tag_name])
                validated = validate_date(date_value)
                if validated:
                    logger.debug(
                        "Found %s date via exifread [%s]: %s",
                        file_type,
                        tag_name,
                        validated,
                    )
                    return validated

        logger.debug(
            "No creation date found in %s file: %s",
            file_type,
            file_path,
        )
        return None

    except ImportError:
        logger.warning(
            "exifread not installed — cannot extract %s metadata. "
            "Install with: pip install exifread",
            file_type,
        )
        return None
    except (OSError, IOError, ValueError) as e:
        logger.error(
            "Error extracting %s creation date from %s: %s",
            file_type,
            file_path,
            e,
        )
        return None
    except Exception as e:
        logger.debug(
            "Unexpected error reading %s file %s: %s",
            file_type,
            file_path,
            e,
        )
        return None


def extract_dng_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from DNG file."""
    return _extract_raw_creation_date(file_path, "DNG")


def extract_cr2_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from Canon CR2 file."""
    return _extract_raw_creation_date(file_path, "CR2")


def extract_cr3_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from Canon CR3 file."""
    return _extract_raw_creation_date(file_path, "CR3")


def extract_nef_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from Nikon NEF file."""
    return _extract_raw_creation_date(file_path, "NEF")


def extract_arw_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from Sony ARW file."""
    return _extract_raw_creation_date(file_path, "ARW")


def extract_orf_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from Olympus ORF file."""
    return _extract_raw_creation_date(file_path, "ORF")


def extract_rw2_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from Panasonic RW2 file."""
    return _extract_raw_creation_date(file_path, "RW2")


def extract_raf_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from Fujifilm RAF file."""
    return _extract_raw_creation_date(file_path, "RAF")


# Registry for RAW extractors
RAW_EXTRACTORS = {
    ".dng": extract_dng_creation_date,
    ".cr2": extract_cr2_creation_date,
    ".cr3": extract_cr3_creation_date,
    ".nef": extract_nef_creation_date,
    ".arw": extract_arw_creation_date,
    ".orf": extract_orf_creation_date,
    ".rw2": extract_rw2_creation_date,
    ".raf": extract_raf_creation_date,
}

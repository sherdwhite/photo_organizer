"""
HEIC/HEIF image metadata extractor using pillow-heif.

HEIC (High Efficiency Image Container) is the default photo format
on iPhones since iOS 11. This is the single most common format
missing from many photo organizer tools.

pillow-heif registers itself as a Pillow plugin, allowing standard
PIL operations on HEIC/HEIF files.
"""

import logging
from typing import Optional

from photo_organizer.date_utils import validate_date

logger = logging.getLogger(__name__)

_heif_registered = False


def _ensure_heif_support():
    """Register pillow-heif plugin with Pillow (once)."""
    global _heif_registered
    if _heif_registered:
        return True
    try:
        import pillow_heif

        pillow_heif.register_heif_opener()
        _heif_registered = True
        return True
    except ImportError:
        logger.warning(
            "pillow-heif not installed — cannot read HEIC/HEIF. "
            "Install with: pip install pillow-heif"
        )
        return False


def extract_heif_creation_date(
    file_path: str,
) -> Optional[str]:
    """
    Extract creation date from HEIC/HEIF file.

    Uses pillow-heif to register HEIF support with Pillow, then
    reads EXIF data via Pillow's standard EXIF interface.

    Args:
        file_path: Path to the HEIC/HEIF file

    Returns:
        Validated creation date string, or None
    """
    if not _ensure_heif_support():
        return None

    try:
        from PIL import Image as PILImage
        from PIL.ExifTags import Base as ExifBase

        with PILImage.open(file_path) as img:
            exif_data = img.getexif()
            if not exif_data:
                logger.debug("No EXIF data in HEIF file: %s", file_path)
                return None

            # Check date tags in priority order
            date_tag_ids = [
                ExifBase.DateTimeOriginal,
                ExifBase.DateTimeDigitized,
                ExifBase.DateTime,
            ]

            for tag_id in date_tag_ids:
                date_value = exif_data.get(tag_id)
                if date_value:
                    validated = validate_date(str(date_value))
                    if validated:
                        logger.debug(
                            "Found HEIF date (tag %s): %s",
                            tag_id,
                            validated,
                        )
                        return validated

        logger.debug("No creation date in HEIF EXIF: %s", file_path)
        return None

    except (OSError, IOError, ValueError) as e:
        logger.error(
            "Error extracting HEIF date from %s: %s",
            file_path,
            e,
        )
        return None
    except Exception as e:
        logger.debug(
            "Unexpected error reading HEIF file %s: %s",
            file_path,
            e,
        )
        return None


# Registry for HEIF extractors
HEIF_EXTRACTORS = {
    ".heic": extract_heif_creation_date,
    ".heif": extract_heif_creation_date,
}

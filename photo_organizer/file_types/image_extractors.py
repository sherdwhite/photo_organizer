"""
Image metadata extractors using PIL library.

This module consolidates all image file type extractors that use the
PIL library for metadata extraction, reducing code duplication and
improving maintainability.

Supported formats: PNG, GIF, WebP, TIFF, BMP, JPEG 2000, MPO, AVIF
"""

import logging
from typing import Optional

from PIL import Image as PILImage
from PIL.ExifTags import Base as ExifBase

from photo_organizer.date_utils import validate_date

logger = logging.getLogger(__name__)


def _extract_pil_creation_date(
    file_path: str, file_type: str, date_fields: list
) -> Optional[str]:
    """
    Generic function to extract creation date using PIL metadata.

    Args:
        file_path: Path to the image file
        file_type: File type for logging (e.g., "PNG", "GIF")
        date_fields: List of metadata fields to check for date

    Returns:
        Validated creation date string, or None
    """
    try:
        with PILImage.open(file_path) as img:
            info = img.info

            # Try text/info metadata fields
            for date_field in date_fields:
                if date_field in info:
                    date_value = info[date_field]
                    if date_value:
                        validated = validate_date(str(date_value))
                        if validated:
                            logger.debug(
                                "Found %s date in field %s: %s",
                                file_type,
                                date_field,
                                validated,
                            )
                            return validated

        logger.debug(
            "No creation date in %s metadata: %s",
            file_type,
            file_path,
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


def _extract_pil_exif_date(file_path: str, file_type: str) -> Optional[str]:
    """
    Extract creation date from EXIF data via Pillow.

    Used for formats that embed standard EXIF (TIFF, WebP, MPO, etc.)

    Args:
        file_path: Path to the image file
        file_type: File type for logging

    Returns:
        Validated creation date string, or None
    """
    try:
        with PILImage.open(file_path) as img:
            exif_data = img.getexif()
            if not exif_data:
                return None

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
                            "Found %s EXIF date (tag %s): %s",
                            file_type,
                            tag_id,
                            validated,
                        )
                        return validated

        return None

    except (OSError, IOError, ValueError) as e:
        logger.error(
            "Error extracting %s EXIF from %s: %s",
            file_type,
            file_path,
            e,
        )
        return None


def extract_png_creation_date(
    file_path: str,
) -> Optional[str]:
    """Extract creation date from PNG file using PIL."""
    date_fields = [
        "creation_time",
        "date:create",
        "date:modify",
    ]
    return _extract_pil_creation_date(file_path, "PNG", date_fields)


def extract_gif_creation_date(
    file_path: str,
) -> Optional[str]:
    """Extract creation date from GIF file using PIL."""
    date_fields = [
        "date:create",
        "date:modify",
        "creation_time",
    ]
    return _extract_pil_creation_date(file_path, "GIF", date_fields)


def extract_webp_creation_date(
    file_path: str,
) -> Optional[str]:
    """
    Extract creation date from WebP file.

    WebP files can contain EXIF data (same as JPEG).
    """
    return _extract_pil_exif_date(file_path, "WebP")


def extract_tiff_creation_date(
    file_path: str,
) -> Optional[str]:
    """
    Extract creation date from TIFF file.

    TIFF files have rich EXIF support — they're the basis of the
    EXIF standard itself.
    """
    return _extract_pil_exif_date(file_path, "TIFF")


def extract_bmp_creation_date(
    file_path: str,
) -> Optional[str]:
    """
    Extract creation date from BMP file.

    BMP has no native metadata; we return None so the fallback
    chain (XMP, filename, filesystem) handles it.
    """
    logger.debug("BMP has no metadata support, skipping: %s", file_path)
    return None


def extract_jpeg2000_creation_date(
    file_path: str,
) -> Optional[str]:
    """Extract creation date from JPEG 2000 file via EXIF."""
    return _extract_pil_exif_date(file_path, "JPEG2000")


def extract_mpo_creation_date(
    file_path: str,
) -> Optional[str]:
    """
    Extract creation date from MPO (Multi-Picture Object) file.

    MPO files are multi-frame JPEGs used for 3D stereo photos.
    They contain standard EXIF data.
    """
    return _extract_pil_exif_date(file_path, "MPO")


def extract_avif_creation_date(
    file_path: str,
) -> Optional[str]:
    """
    Extract creation date from AVIF file.

    AVIF is a next-gen image format based on AV1. Pillow supports
    reading AVIF with the pillow-avif-plugin or Pillow >= 10.1.
    """
    return _extract_pil_exif_date(file_path, "AVIF")


# Registry for image extractors
IMAGE_EXTRACTORS = {
    ".png": extract_png_creation_date,
    ".gif": extract_gif_creation_date,
    ".webp": extract_webp_creation_date,
    ".tiff": extract_tiff_creation_date,
    ".tif": extract_tiff_creation_date,
    ".bmp": extract_bmp_creation_date,
    ".jp2": extract_jpeg2000_creation_date,
    ".j2k": extract_jpeg2000_creation_date,
    ".mpo": extract_mpo_creation_date,
    ".avif": extract_avif_creation_date,
}

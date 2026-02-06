import logging
import warnings
from typing import BinaryIO, Optional

from exif import Image

from photo_organizer.date_utils import validate_date

# Suppress RuntimeWarnings from the exif library (corrupted EXIF data)
warnings.filterwarnings("ignore", category=RuntimeWarning, module="exif")

logger = logging.getLogger(__name__)


def extract_exif_data(image_file: BinaryIO) -> Optional[str]:
    """
    Extract EXIF creation date from image file using the exif library.

    Args:
        image_file: Binary file object of the image

    Returns:
        Validated creation date string in "YYYY:MM:DD HH:MM:SS" or None
    """
    try:
        my_image = Image(image_file)

        if not my_image.has_exif:
            logger.debug("Image has no EXIF data")
            return None

        # Try EXIF date fields in order of preference
        date_fields = [
            "datetime_original",
            "media_created",
            "datetime_digitized",
            "datetime",
            "gps_datestamp",
        ]

        for field in date_fields:
            date_value = my_image.get(field)
            if date_value:
                validated = validate_date(str(date_value))
                if validated:
                    logger.debug(
                        "Found EXIF date in field %s: %s",
                        field,
                        validated,
                    )
                    return validated

        logger.debug("No creation date found in EXIF data")
        return None

    except ValueError as e:
        # Handle corrupted EXIF data (e.g., invalid TIFF byte order)
        logger.debug("File has corrupted or invalid EXIF data: %s", str(e))
        return None
    except (KeyError, AttributeError) as e:
        logger.error("Error extracting EXIF data: %s", e)
        return None
    except Exception as e:
        # Catch any other unexpected errors from the exif library
        logger.warning("Unexpected error reading EXIF data: %s", str(e))
        return None


def extract_exif_via_pillow(file_path: str) -> Optional[str]:
    """
    Extract EXIF creation date using Pillow as a secondary fallback.

    The exif library sometimes fails on non-standard or partially
    corrupted EXIF data. Pillow's EXIF reader uses a different parser
    and can succeed where the exif library fails.

    Args:
        file_path: Path to the image file

    Returns:
        Validated creation date string, or None
    """
    try:
        from PIL import Image as PILImage
        from PIL.ExifTags import Base as ExifBase

        with PILImage.open(file_path) as img:
            exif_data = img.getexif()
            if not exif_data:
                return None

            # EXIF tag IDs for date fields
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
                            "Pillow EXIF fallback found date " "(tag %s): %s",
                            tag_id,
                            validated,
                        )
                        return validated

        return None

    except Exception as e:
        logger.debug("Pillow EXIF fallback failed for %s: %s", file_path, e)
        return None

import logging
import warnings
from typing import BinaryIO, Optional

from exif import Image

# Suppress RuntimeWarnings from the exif library (corrupted EXIF data)
warnings.filterwarnings("ignore", category=RuntimeWarning, module="exif")

logger = logging.getLogger(__name__)


def extract_exif_data(image_file: BinaryIO) -> Optional[str]:
    """
    Extract EXIF creation date from image file.

    Args:
        image_file: Binary file object of the image

    Returns:
        Creation date string in format "YYYY:MM:DD HH:MM:SS" or None
    """
    try:
        my_image = Image(image_file)

        if not my_image.has_exif:
            logger.debug("Image has no EXIF data")
            return None

        # Try different EXIF date fields in order of preference
        date_fields = ["datetime_original", "media_created", "datetime_digitized"]

        for field in date_fields:
            date_value = my_image.get(field)
            if date_value:
                logger.debug("Found EXIF date in field %s: %s", field, date_value)
                return date_value

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

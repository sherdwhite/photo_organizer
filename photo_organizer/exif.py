import logging
from typing import BinaryIO, Optional

from exif import Image

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

    except (ValueError, KeyError, AttributeError) as e:
        logger.error("Error extracting EXIF data: %s", e)
        return None

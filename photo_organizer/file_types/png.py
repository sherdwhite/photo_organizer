import logging
from typing import Optional

from PIL import Image as PILImage

logger = logging.getLogger(__name__)


def extract_png_creation_date(file_path: str) -> Optional[str]:
    """
    Extract creation date from PNG file using PIL.

    Args:
        file_path: Path to the PNG file

    Returns:
        Creation date string in format "YYYY:MM:DD HH:MM:SS" or None
    """
    try:
        with PILImage.open(file_path) as img:
            info = img.info

            # Try different possible date fields
            for date_field in ["creation_time", "date:create", "date:modify"]:
                if date_field in info:
                    date_value = info[date_field]
                    if date_value:
                        logger.debug(
                            "Found PNG date in field %s: %s", date_field, date_value
                        )
                        return date_value

        logger.debug("No creation date found in PNG file: %s", file_path)
        return None

    except (OSError, IOError, ValueError) as e:
        logger.error("Error extracting PNG creation date from %s: %s", file_path, e)
        return None

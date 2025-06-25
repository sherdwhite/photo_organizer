import logging
from typing import Optional

from PIL import Image as PILImage

logger = logging.getLogger(__name__)


def extract_gif_creation_date(file_path: str) -> Optional[str]:
    """
    Extract creation date from GIF file using PIL.

    Args:
        file_path: Path to the GIF file

    Returns:
        Creation date string in format "YYYY:MM:DD HH:MM:SS" or None
    """
    try:
        with PILImage.open(file_path) as img:
            info = img.info

            # Try different possible date fields
            for date_field in ["date:create", "date:modify", "creation_time"]:
                if date_field in info:
                    date_value = info[date_field]
                    if date_value:
                        logger.debug(
                            "Found GIF date in field %s: %s", date_field, date_value
                        )
                        return date_value

        logger.debug("No creation date found in GIF file: %s", file_path)
        return None

    except (OSError, IOError, ValueError) as e:
        logger.error("Error extracting GIF creation date from %s: %s", file_path, e)
        return None

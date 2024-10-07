from PIL import Image as PILImage

import logging

logger = logging.getLogger(__name__)


def extract_gif_creation_date(file_path):
    try:
        img = PILImage.open(file_path)
        info = img.info
        if "date:create" in info:
            return info["date:create"]
        elif "date:modify" in info:
            return info["date:modify"]
    except Exception as e:
        logger.error(f"Error extracting GIF creation date: {e}")
    return None

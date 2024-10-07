import logging

from PIL import Image as PILImage

logger = logging.getLogger(__name__)


def extract_png_creation_date(file_path):
    try:
        img = PILImage.open(file_path)
        info = img.info
        if "creation_time" in info:
            return info["creation_time"]
        elif "date:create" in info:
            return info["date:create"]
    except Exception as e:
        logger.error(f"Error extracting PNG creation date: {e}")
    return None

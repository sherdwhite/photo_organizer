import logging
from typing import Optional

from PIL import Image as PILImage

logger = logging.getLogger(__name__)


def extract_gif_creation_date(file_path: str) -> Optional[str]:
    try:
        img = PILImage.open(file_path)
        info = img.info
        if "date:create" in info:
            return info["date:create"]
        elif "date:modify" in info:
            return info["date:modify"]
    except Exception as e:
        logger.error("Error extracting GIF creation date: %s", e)
    return None

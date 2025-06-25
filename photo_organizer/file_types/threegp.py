import logging
from datetime import datetime
from typing import Optional

from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

logger = logging.getLogger(__name__)


def extract_3gp_creation_date(file_path: str) -> Optional[str]:
    """
    Extract creation date from 3GP file using hachoir.

    Args:
        file_path: Path to the 3GP file

    Returns:
        Creation date string in format "YYYY:MM:DD HH:MM:SS" or None
    """
    try:
        parser = createParser(file_path)
        if not parser:
            logger.warning("Could not create parser for 3GP file: %s", file_path)
            return None

        with parser:
            metadata = extractMetadata(parser)

        if metadata and metadata.has("creation_date"):
            creation_date: Optional[datetime] = metadata.get("creation_date")
            if creation_date:
                return creation_date.strftime("%Y:%m:%d %H:%M:%S")

        logger.debug("No creation date found in 3GP file: %s", file_path)
        return None

    except (OSError, IOError, ValueError) as e:
        logger.error("Error extracting 3GP creation date from %s: %s", file_path, e)
        return None

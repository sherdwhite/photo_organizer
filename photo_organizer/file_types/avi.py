from datetime import datetime
from typing import Optional

from hachoir.metadata import extractMetadata
from hachoir.parser import createParser


def extract_avi_creation_date(file_path: str) -> Optional[str]:
    parser = createParser(file_path)
    if not parser:
        return None
    with parser:
        metadata = extractMetadata(parser)
    if metadata and metadata.has("creation_date"):
        creation_date: Optional[datetime] = metadata.get("creation_date")
        if creation_date:
            return creation_date.strftime("%Y:%m:%d %H:%M:%S")
    return None

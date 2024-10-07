from hachoir.metadata import extractMetadata
from hachoir.parser import createParser


def extract_mov_creation_date(file_path):
    parser = createParser(file_path)
    if not parser:
        return None
    with parser:
        metadata = extractMetadata(parser)
    if metadata and metadata.has("creation_date"):
        return metadata.get("creation_date").strftime("%Y:%m:%d %H:%M:%S")
    return None

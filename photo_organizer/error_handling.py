import logging
import os
import shutil

logger = logging.getLogger(__name__)


def log_and_handle_error(
    destination_dir: str, file: str, file_dir: str, error_message: str
) -> None:
    logger.error(error_message)
    handle_error_cases(destination_dir, file, file_dir)


def handle_error_cases(destination_dir: str, file: str, file_dir: str) -> None:
    file_destination: str = os.path.join(destination_dir, "Unknown", file)
    folder_destination: str = os.path.join(destination_dir, "Unknown")
    if not os.path.exists(folder_destination):
        os.makedirs(folder_destination)
    if not os.path.exists(file_destination):
        logger.debug("Moving file %s to %s", file, file_destination)
        shutil.copy(file_dir, file_destination)
        os.remove(file_dir)
    else:
        os.remove(file_dir)

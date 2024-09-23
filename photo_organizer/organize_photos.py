import logging
import os
import shutil
from datetime import datetime
from struct import error as UnpackError

from exif import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image as PILImage

from photo_organizer.utils import parse_args

logger = logging.getLogger(__name__)


def log_and_handle_error(destination_dir, file, file_dir, error_message):
    logger.error(error_message)
    handle_error_cases(destination_dir, file, file_dir)


def extract_exif_data(image_file):
    my_image = Image(image_file)
    if my_image.has_exif:
        datetime_original = (
            my_image.get("datetime_original")
            or my_image.get("media_created")
            or my_image.get("datetime_digitized")
        )
        return datetime_original
    return None


def extract_mov_creation_date(file_path):
    parser = createParser(file_path)
    if not parser:
        return None
    with parser:
        metadata = extractMetadata(parser)
    if metadata and metadata.has("creation_date"):
        return metadata.get("creation_date").strftime("%Y:%m:%d %H:%M:%S")
    return None


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


def extract_avi_creation_date(file_path):
    parser = createParser(file_path)
    if not parser:
        return None
    with parser:
        metadata = extractMetadata(parser)
    if metadata and metadata.has("creation_date"):
        return metadata.get("creation_date").strftime("%Y:%m:%d %H:%M:%S")
    return None


def extract_mp4_creation_date(file_path):
    parser = createParser(file_path)
    if not parser:
        return None
    with parser:
        metadata = extractMetadata(parser)
    if metadata and metadata.has("creation_date"):
        return metadata.get("creation_date").strftime("%Y:%m:%d %H:%M:%S")
    return None


def extract_3gp_creation_date(file_path):
    parser = createParser(file_path)
    if not parser:
        return None
    with parser:
        metadata = extractMetadata(parser)
    if metadata and metadata.has("creation_date"):
        return metadata.get("creation_date").strftime("%Y:%m:%d %H:%M:%S")
    return None


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


def extract_m4v_creation_date(file_path):
    parser = createParser(file_path)
    if not parser:
        return None
    with parser:
        metadata = extractMetadata(parser)
    if metadata and metadata.has("creation_date"):
        return metadata.get("creation_date").strftime("%Y:%m:%d %H:%M:%S")
    return None


def handle_error_cases(destination_dir, file, file_dir):
    file_destination = os.path.join(destination_dir, "Unknown", file)
    folder_destination = os.path.join(destination_dir, "Unknown")
    if not os.path.exists(folder_destination):
        os.makedirs(folder_destination)
    if not os.path.exists(file_destination):
        logger.debug("Moving file {0} to {1}".format(file, file_destination))
        shutil.copy(file_dir, file_destination)
        os.remove(file_dir)
    else:
        os.remove(file_dir)


def organize():
    dirs = parse_args()
    origin_dir = dirs.get("origin_dir")
    destination_dir = dirs.get("destination_dir")
    logger.info("Origin Directory: %s", origin_dir)
    logger.info("Destination Directory: %s", destination_dir)

    for root, subdirs, files in os.walk(origin_dir):
        if not os.listdir(root):
            os.rmdir(root)
            print("Removing directory {}".format(root))
        for file in files:
            file_dir = os.path.join(root, file)
            if file in {"Thumbs.db", "desktop"}:
                os.remove(file_dir)
                continue
            print("At file: {}".format(file_dir))
            try:
                datetime_original = None
                if file.lower().endswith(".mov"):
                    datetime_original = extract_mov_creation_date(file_dir)
                elif file.lower().endswith(".png"):
                    datetime_original = extract_png_creation_date(file_dir)
                elif file.lower().endswith(".avi"):
                    datetime_original = extract_avi_creation_date(file_dir)
                elif file.lower().endswith(".mp4"):
                    datetime_original = extract_mp4_creation_date(file_dir)
                elif file.lower().endswith(".3gp"):
                    datetime_original = extract_3gp_creation_date(file_dir)
                elif file.lower().endswith(".gif"):
                    datetime_original = extract_gif_creation_date(file_dir)
                elif file.lower().endswith(".m4v"):
                    datetime_original = extract_m4v_creation_date(file_dir)
                else:
                    with open(file_dir, "rb") as image_file:
                        datetime_original = extract_exif_data(image_file)

                if datetime_original:
                    date = datetime.strptime(datetime_original, "%Y:%m:%d %H:%M:%S")
                    year = date.year
                    month = str(date.month).zfill(2)
                    folder_destination = os.path.join(destination_dir, str(year), month)
                    file_destination = os.path.join(folder_destination, file)
                    if not os.path.exists(folder_destination):
                        os.makedirs(folder_destination)
                    if not os.path.exists(file_destination):
                        logger.debug("Moving file %s to %s", file, file_destination)
                        shutil.copy(file_dir, file_destination)
                        os.remove(file_dir)
                    else:
                        os.remove(file_dir)
                else:
                    log_and_handle_error(
                        destination_dir,
                        file,
                        file_dir,
                        "File {0} at location {1} has no exif data.".format(
                            file, file_dir
                        ),
                    )
            except (ValueError, UnpackError) as ex:
                log_and_handle_error(
                    destination_dir,
                    file,
                    file_dir,
                    "File {0} at location {1} has possible bad exif data. Error: {2}".format(
                        file, file_dir, ex
                    ),
                )
            except PermissionError as pe:
                logger.error(
                    "PermissionError: Could not remove file {0} at location {1}. Error: {2}".format(
                        file, file_dir, pe
                    )
                )
                # Additional debugging information
                logger.debug("Checking if file is closed properly.")
                try:
                    with open(file_dir, "rb") as f:
                        pass
                except Exception as e:
                    logger.error("Error while checking file: {0}".format(e))

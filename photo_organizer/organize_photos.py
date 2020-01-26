import logging
import os

from photo_organizer.utils import parse_args

logger = logging.getLogger(__name__)


def organize():
    dirs = parse_args()
    origin_dir = dirs.get('origin_dir')
    destination_dir = dirs.get('destination_dir')
    logger.info("Origin Directory: {}".format(origin_dir))
    logger.info("Destination Directory: {}".format(destination_dir))

    for root, subdirs, files in os.walk(path):
        for file in files:

            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
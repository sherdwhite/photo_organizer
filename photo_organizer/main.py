#!/usr/bin/python3.7
import logging

from photo_organizer import log, __version__
from photo_organizer.organize_photos import organize

logger = logging.getLogger(__name__)
log.setup_logging(name="photo_organizer", level="INFO")


def run():
    logger.info("Starting photo_organizer. Version {}".format(__version__))
    organize()


if __name__ == "__main__":
    run()

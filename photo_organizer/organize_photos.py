import logging
import os
import shutil

import exif

from datetime import datetime
from photo_organizer.utils import parse_args

logger = logging.getLogger(__name__)


def organize():
    dirs = parse_args()
    origin_dir = dirs.get('origin_dir')
    destination_dir = dirs.get('destination_dir')
    logger.info("Origin Directory: {}".format(origin_dir))
    logger.info("Destination Directory: {}".format(destination_dir))

    for root, subdirs, files in os.walk(origin_dir):
        for file in files:
            file_dir = '{0}/{1}'.format(root, file)
            try:
                with open(file_dir, 'rb') as image_file:
                    my_image = exif.Image(image_file)
                    if my_image.has_exif:
                        datetime_original = my_image.get('datetime_original')
                        date = datetime.strptime(datetime_original, '%Y:%m:%d %H:%M:%S')
                        year = date.year
                        month = str(date.month).zfill(2)
                        folder_destination = ('{0}/{1}/{2}'.format(destination_dir, year, month))
                        file_destination = ('{0}/{1}/{2}/{3}'.format(destination_dir, year, month, file))
                        if not os.path.exists(folder_destination):
                            os.makedirs(folder_destination)
                        if not os.path.exists(file_destination):
                            logger.info('Moving file {0} to {1}'.format(file, file_destination))
                            shutil.copy(file_dir, file_destination)
            except (AssertionError, AttributeError) as ex:
                logger.error('File {0} at location {1} could not be moved.'.format(file, file_destination))
                continue
            except TypeError:
                logger.error('File {0} at location {1} could not be moved due to missing datetime.'.format(file, file_destination))
                continue

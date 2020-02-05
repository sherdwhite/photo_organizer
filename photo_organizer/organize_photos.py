import logging
import os
import shutil

import exif

from datetime import datetime

from exif import Image

from photo_organizer.utils import parse_args

logger = logging.getLogger(__name__)


def organize():
    dirs = parse_args()
    origin_dir = dirs.get('origin_dir')
    destination_dir = dirs.get('destination_dir')
    logger.info("Origin Directory: {}".format(origin_dir))
    logger.info("Destination Directory: {}".format(destination_dir))

    for root, subdirs, files in os.walk(origin_dir):
        if not os.listdir(root):
            os.rmdir(root)
            print('Removing directory {}'.format(root))
        for file in files:
            file_dir = '{0}/{1}'.format(root, file)
            if file in {'Thumbs.db', 'desktop.ini'}:
                os.remove(file_dir)
                continue
            print('At file: {}'.format(file_dir))
            try:
                with open(file_dir, 'rb') as image_file:
                    my_image = exif.Image(image_file)
                    print(dir(my_image))
                    if my_image.has_exif:
                        datetime_original = my_image.get('datetime_original')
                        if not datetime_original:
                            print(my_image.get('media_created'))
                            datetime_original = my_image.get('media_created')
                        if not datetime_original:
                            print(my_image.get('datetime_digitized'))
                            datetime_original = my_image.get('datetime_digitized')
                        date = datetime.strptime(datetime_original, '%Y:%m:%d %H:%M:%S')
                        year = date.year
                        month = str(date.month).zfill(2)
                        folder_destination = ('{0}/{1}/{2}'.format(destination_dir, year, month))
                        file_destination = ('{0}/{1}/{2}/{3}'.format(destination_dir, year, month, file))
                        if not os.path.exists(folder_destination):
                            os.makedirs(folder_destination)
                        if not os.path.exists(file_destination):
                            logger.debug('Moving file {0} to {1}'.format(file, file_destination))
                            shutil.copy(file_dir, file_destination)
                            image_file.close()
                            os.remove(file_dir)
                        else:
                            image_file.close()
                            os.remove(file_dir)
                    else:
                        logger.error(
                            'File {0} at location {1} has no exif data.'.format(file, file_dir))
                        handle_error_cases(destination_dir, file, image_file, file_dir)
                    image_file.close()
            except (AssertionError, AttributeError) as ex:
                logger.error('File {0} at location {1} could not be moved. Error: {2}'.format(file, file_dir, ex))
                handle_error_cases(destination_dir, file, image_file, file_dir)
                continue
            except TypeError as ex:
                logger.error('File {0} at location {1} could not be moved, missing datetime. '
                             'Error: {2}'.format(file, file_dir, ex))
                handle_error_cases(destination_dir, file, image_file, file_dir)
                continue
            except ValueError as ex:
                logger.error('File {0} at location {1} has possible bad exif data. Error: {2}'
                             'Error: {2}'.format(file, file_dir, ex))
                handle_error_cases(destination_dir, file, image_file, file_dir)
                continue


def handle_error_cases(destination_dir, file, image_file, file_dir):
    file_destination = ('{0}/{1}/{2}'.format(destination_dir, 'Unknown', file))
    folder_destination = ('{0}/{1}'.format(destination_dir, 'Unknown'))
    if not os.path.exists(folder_destination):
        os.makedirs(folder_destination)
    if not os.path.exists(file_destination):
        logger.debug('Moving file {0} to {1}'.format(file, file_destination))
        shutil.copy(file_dir, file_destination)
        image_file.close()
        os.remove(file_dir)
    else:
        image_file.close()
        os.remove(file_dir)

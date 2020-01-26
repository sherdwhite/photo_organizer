import getopt
import logging
import sys

logger = logging.getLogger(__name__)


def parse_args():
    cmd_arguments = sys.argv[1:]
    origin_dir = r'D:/Pictures'
    destination_dir = r'D:/Sorted_Pictures'

    try:
        arguments, values = getopt.getopt(cmd_arguments, 'o:d:', ['origin=', 'destination='])
        for argument, value in arguments:
            if argument in ("-o", "--origin"):
                origin_dir = value
            elif argument in ("-d", "--destination"):
                destination_dir = value
            else:
                logger.error("Invalid argument: {0} with value {1} passed.".format(argument, value))
    except getopt.error as err:
        # output error, and return with an error code
        logger.error(str(err))

    return {'origin_dir': origin_dir,
            'destination_dir': destination_dir,
            }

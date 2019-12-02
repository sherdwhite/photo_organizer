import getopt
import os
import sys


def parse_args():
    cmd_arguments = sys.argv[1:]
    path = os.getcwd()

    try:
        arguments, values = getopt.getopt(cmd_arguments, 'p:', ['path='])
        for argument, value in arguments:
            if argument in ("-p", "--path"):
                path = value
            else:
                print("Invalid argument: {0} with value {1} passed.".format(argument, value))
    except getopt.error as err:
        # output error, and return with an error code
        print(str(err))

    return path

#!/usr/bin/python3.7

import os

from utils import parse_args


def main():
    path = parse_args()

    print("Path to files: {}".format(path))

    for root, subdirs, files in os.walk(path):
        for file in files:
            print(file)


if __name__ == "__main__":
    main()

import argparse
import logging

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Organize photos by EXIF data.")
    parser.add_argument(
        "-o",
        "--origin",
        type=str,
        default=r"C:/Users/sherd/Documents/Unsorted_Pics",
        help="Path to the origin directory containing photos.",
    )
    parser.add_argument(
        "-d",
        "--destination",
        type=str,
        default=r"C:/Users/sherd/Documents/Sorted_Pics",
        help="Path to the destination directory where photos will be organized.",
    )

    args = parser.parse_args()

    return {"origin_dir": args.origin, "destination_dir": args.destination}

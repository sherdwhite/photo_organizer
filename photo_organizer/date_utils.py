"""
Date validation and XMP metadata extraction utilities.

This module provides:
- Date validation (reject garbage, future, pre-digital-camera, and epoch dates)
- XMP metadata parsing for creation dates
- Filesystem timestamp extraction as a last-resort fallback
"""

import logging
import os
import re
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Earliest plausible date for consumer digital photos
EARLIEST_VALID_YEAR = 1990

# Patterns for common garbage/placeholder dates
GARBAGE_DATE_PATTERNS = [
    "0000:00:00",
    "    :  :  ",
    "0000-00-00",
    "1970:01:01 00:00:00",
    "1970-01-01 00:00:00",
    "1970-01-01T00:00:00",
]


def validate_date(date_string: Optional[str]) -> Optional[str]:
    """
    Validate an extracted date string, rejecting known-bad values.

    Checks for:
    - None or empty strings
    - Known garbage/placeholder patterns
    - Dates before 1990 (pre-consumer digital cameras)
    - Dates in the future
    - Unparseable strings

    Args:
        date_string: Date string in format "YYYY:MM:DD HH:MM:SS" (or similar)

    Returns:
        The validated date string in "YYYY:MM:DD HH:MM:SS" format, or None
    """
    if not date_string or not date_string.strip():
        return None

    date_string = date_string.strip()

    # Reject known garbage patterns
    for pattern in GARBAGE_DATE_PATTERNS:
        if date_string.startswith(pattern):
            logger.debug("Rejected garbage date: %s", date_string)
            return None

    # Try to parse the date
    parsed_dt = _parse_date_flexible(date_string)
    if parsed_dt is None:
        logger.debug("Could not parse date string: %s", date_string)
        return None

    # Reject dates before consumer digital cameras
    if parsed_dt.year < EARLIEST_VALID_YEAR:
        logger.debug(
            "Rejected pre-digital date: %s (year %d)",
            date_string,
            parsed_dt.year,
        )
        return None

    # Reject dates in the future (with 1-day grace for timezone differences)
    from datetime import timedelta

    if parsed_dt > datetime.now() + timedelta(days=1):
        logger.debug("Rejected future date: %s", date_string)
        return None

    # Return in canonical format
    return parsed_dt.strftime("%Y:%m:%d %H:%M:%S")


def _parse_date_flexible(date_string: str) -> Optional[datetime]:
    """
    Try multiple date formats to parse a date string.

    Args:
        date_string: Date string in various possible formats

    Returns:
        Parsed datetime object, or None
    """
    # Common date formats found in EXIF, XMP, and file metadata
    formats = [
        "%Y:%m:%d %H:%M:%S",  # EXIF standard
        "%Y-%m-%d %H:%M:%S",  # ISO-ish
        "%Y-%m-%dT%H:%M:%S",  # ISO 8601
        "%Y-%m-%dT%H:%M:%S%z",  # ISO 8601 with timezone
        "%Y-%m-%dT%H:%M:%S.%f",  # ISO 8601 with fractional seconds
        "%Y-%m-%dT%H:%M:%S.%f%z",  # ISO 8601 with fractional seconds and tz
        "%Y:%m:%d %H:%M:%S%z",  # EXIF with timezone offset
        "%Y-%m-%d",  # Date only
        "%Y:%m:%d",  # EXIF date only
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_string.strip(), fmt)
            # Convert timezone-aware to naive (local concept)
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt
        except ValueError:
            continue

    # Try stripping trailing timezone info like "+05:30" or "Z"
    cleaned = re.sub(r"[+-]\d{2}:\d{2}$", "", date_string.strip())
    cleaned = cleaned.rstrip("Z")
    if cleaned != date_string.strip():
        return _parse_date_flexible(cleaned)

    return None


def extract_xmp_date(file_path: str) -> Optional[str]:
    """
    Extract creation date from XMP metadata embedded in a file.

    XMP (Extensible Metadata Platform) stores dates in XML format inside
    image files. Many modern cameras, phones, and editors write XMP data
    even when EXIF is stripped.

    Looks for tags:
    - xmp:CreateDate
    - photoshop:DateCreated
    - exif:DateTimeOriginal
    - xmp:ModifyDate (lower priority)

    Args:
        file_path: Path to the file

    Returns:
        Validated creation date string, or None
    """
    try:
        # Read a chunk of the file to find XMP data
        # XMP is typically in the first few MB
        with open(file_path, "rb") as f:
            data = f.read(3 * 1024 * 1024)  # Read up to 3MB

        # Look for XMP packet boundaries
        xmp_start = data.find(b"<x:xmpmeta")
        if xmp_start == -1:
            xmp_start = data.find(b"<rdf:RDF")
        if xmp_start == -1:
            return None

        xmp_end = data.find(b"</x:xmpmeta>", xmp_start)
        if xmp_end == -1:
            xmp_end = data.find(b"</rdf:RDF>", xmp_start)
        if xmp_end == -1:
            # Try a reasonable chunk after xmp_start
            xmp_data = data[xmp_start : xmp_start + 65536]
        else:
            xmp_data = data[xmp_start : xmp_end + 20]

        xmp_text = xmp_data.decode("utf-8", errors="ignore")

        # Search for date tags in priority order
        _dt = r"\d{4}[-:]\d{2}[-:]\d{2}[T ]\d{2}:\d{2}:\d{2}"
        _cap = r'[>\s"]*(' + _dt + r'[^\s<"]*)'
        date_patterns = [
            r"exif:DateTimeOriginal" + _cap,
            r"photoshop:DateCreated" + _cap,
            r"xmp:CreateDate" + _cap,
            r"xmp:ModifyDate" + _cap,
        ]

        for pattern in date_patterns:
            match = re.search(pattern, xmp_text)
            if match:
                raw_date = match.group(1)
                validated = validate_date(raw_date)
                if validated:
                    logger.debug("Found XMP date in %s: %s", file_path, validated)
                    return validated

        return None

    except (OSError, IOError) as e:
        logger.debug("Could not read XMP from %s: %s", file_path, e)
        return None
    except Exception as e:
        logger.debug("Unexpected error reading XMP from %s: %s", file_path, e)
        return None


def get_filesystem_date(file_path: str) -> Optional[str]:
    """
    Extract the best available filesystem date as a last-resort fallback.

    Prefers birth time (creation time) on platforms that support it,
    otherwise falls back to modification time.

    Args:
        file_path: Path to the file

    Returns:
        Validated date string, or None
    """
    try:
        stat_result = os.stat(file_path)

        # Prefer birth time (st_birthtime) if available (macOS, some Windows)
        timestamp = None
        if hasattr(stat_result, "st_birthtime"):
            timestamp = stat_result.st_birthtime
        else:
            # Fall back to modification time
            timestamp = stat_result.st_mtime

        if timestamp and timestamp > 0:
            dt = datetime.fromtimestamp(timestamp)
            date_str = dt.strftime("%Y:%m:%d %H:%M:%S")
            validated = validate_date(date_str)
            if validated:
                logger.debug("Using filesystem date for %s: %s", file_path, validated)
                return validated

    except (OSError, IOError, OverflowError, ValueError) as e:
        logger.debug("Could not get filesystem date for %s: %s", file_path, e)

    return None

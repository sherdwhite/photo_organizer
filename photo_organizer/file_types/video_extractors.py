"""
Video metadata extractors.

Uses ffprobe (FFmpeg) as the primary extractor for speed — it reads
only the container header and returns in milliseconds even on multi-GB
files. Falls back to hachoir if ffprobe is not installed.

Supported formats: MOV, MP4, AVI, M4V, 3GP, MKV, WebM
"""

import json
import logging
import shutil
import subprocess
from datetime import datetime
from typing import Optional

from photo_organizer.date_utils import validate_date

logger = logging.getLogger(__name__)

# Detect ffprobe once at import time
_FFPROBE_BIN = shutil.which("ffprobe")

if _FFPROBE_BIN:
    logger.debug("ffprobe found at %s", _FFPROBE_BIN)
else:
    logger.info(
        "ffprobe not found — falling back to hachoir for video "
        "metadata (slower). Install FFmpeg for faster processing."
    )


# ── ffprobe (fast path) ─────────────────────────────────────────────


def _extract_ffprobe_creation_date(file_path: str, file_type: str) -> Optional[str]:
    """
    Extract creation date from a video file using ffprobe.

    ffprobe reads only the container header, so it is nearly instant
    regardless of file size. It checks the format-level tags first,
    then falls back to per-stream tags.

    Args:
        file_path: Path to the video file
        file_type: File type for logging

    Returns:
        Validated creation date string, or None
    """
    if not _FFPROBE_BIN:
        return None

    try:
        result = subprocess.run(
            [
                _FFPROBE_BIN,
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                file_path,
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            logger.debug(
                "ffprobe returned %d for %s",
                result.returncode,
                file_path,
            )
            return None

        probe = json.loads(result.stdout)

        # Check format-level tags first (most reliable)
        date = _find_date_in_tags(probe.get("format", {}).get("tags", {}))
        if date:
            logger.debug(
                "ffprobe found %s date (format tags): %s",
                file_type,
                date,
            )
            return date

        # Then check per-stream tags
        for stream in probe.get("streams", []):
            date = _find_date_in_tags(stream.get("tags", {}))
            if date:
                logger.debug(
                    "ffprobe found %s date (stream tags): %s",
                    file_type,
                    date,
                )
                return date

        return None

    except subprocess.TimeoutExpired:
        logger.warning("ffprobe timed out for %s: %s", file_type, file_path)
        return None
    except (OSError, json.JSONDecodeError, ValueError) as e:
        logger.debug("ffprobe error for %s %s: %s", file_type, file_path, e)
        return None


def _find_date_in_tags(tags: dict) -> Optional[str]:
    """
    Search an ffprobe tags dict for a creation date.

    Tag keys are case-insensitive in practice, so we normalise.

    Args:
        tags: Dict of metadata tags from ffprobe

    Returns:
        Validated date string, or None
    """
    if not tags:
        return None

    # Normalise keys to lowercase for comparison
    lower_tags = {k.lower(): v for k, v in tags.items()}

    # Priority order of tag names
    tag_names = [
        "creation_time",
        "date",
        "date_recorded",
        "com.apple.quicktime.creationdate",
    ]

    for name in tag_names:
        value = lower_tags.get(name)
        if value:
            validated = validate_date(str(value))
            if validated:
                return validated

    return None


# ── hachoir (slow fallback) ──────────────────────────────────────────


def _extract_hachoir_creation_date(file_path: str, file_type: str) -> Optional[str]:
    """
    Extract creation date using hachoir (fallback when ffprobe
    is unavailable or returns no date).

    Args:
        file_path: Path to the video file
        file_type: File type for logging

    Returns:
        Validated creation date string, or None
    """
    try:
        from hachoir.metadata import extractMetadata
        from hachoir.parser import createParser

        parser = createParser(file_path)
        if not parser:
            logger.warning(
                "Could not create parser for %s file: %s",
                file_type,
                file_path,
            )
            return None

        with parser:
            metadata = extractMetadata(parser)

        if metadata and metadata.has("creation_date"):
            creation_date: Optional[datetime] = metadata.get("creation_date")
            if creation_date:
                date_str = creation_date.strftime("%Y:%m:%d %H:%M:%S")
                validated = validate_date(date_str)
                if validated:
                    return validated

        logger.debug(
            "No creation date found in %s file: %s",
            file_type,
            file_path,
        )
        return None

    except (OSError, IOError, ValueError) as e:
        logger.error(
            "Error extracting %s creation date from %s: %s",
            file_type,
            file_path,
            e,
        )
        return None


# ── Combined extractor (ffprobe → hachoir) ───────────────────────────


def _extract_video_creation_date(file_path: str, file_type: str) -> Optional[str]:
    """
    Try ffprobe first (fast), fall back to hachoir (slow).

    Args:
        file_path: Path to the video file
        file_type: File type for logging

    Returns:
        Validated creation date string, or None
    """
    # Fast path
    date = _extract_ffprobe_creation_date(file_path, file_type)
    if date:
        return date

    # Slow fallback
    return _extract_hachoir_creation_date(file_path, file_type)


def extract_mov_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from MOV file."""
    return _extract_video_creation_date(file_path, "MOV")


def extract_mp4_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from MP4 file."""
    return _extract_video_creation_date(file_path, "MP4")


def extract_avi_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from AVI file."""
    return _extract_video_creation_date(file_path, "AVI")


def extract_m4v_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from M4V file."""
    return _extract_video_creation_date(file_path, "M4V")


def extract_3gp_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from 3GP file."""
    return _extract_video_creation_date(file_path, "3GP")


def extract_mkv_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from MKV file."""
    return _extract_video_creation_date(file_path, "MKV")


def extract_webm_creation_date(file_path: str) -> Optional[str]:
    """Extract creation date from WebM file."""
    return _extract_video_creation_date(file_path, "WebM")


# Registry for video extractors
VIDEO_EXTRACTORS = {
    ".mov": extract_mov_creation_date,
    ".mp4": extract_mp4_creation_date,
    ".avi": extract_avi_creation_date,
    ".m4v": extract_m4v_creation_date,
    ".3gp": extract_3gp_creation_date,
    ".mkv": extract_mkv_creation_date,
    ".webm": extract_webm_creation_date,
}

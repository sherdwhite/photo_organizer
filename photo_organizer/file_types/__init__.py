"""
File type extractors for photo organizer.

This module provides a unified interface to all file type extractors,
consolidating previously separate modules for better maintainability.
"""

from .image_extractors import (
    IMAGE_EXTRACTORS,
    extract_gif_creation_date,
    extract_png_creation_date,
)
from .video_extractors import (
    VIDEO_EXTRACTORS,
    extract_3gp_creation_date,
    extract_avi_creation_date,
    extract_m4v_creation_date,
    extract_mov_creation_date,
    extract_mp4_creation_date,
)

# Combined registry of all extractors
ALL_EXTRACTORS = {**VIDEO_EXTRACTORS, **IMAGE_EXTRACTORS}

__all__ = [
    # Individual extractor functions
    "extract_mov_creation_date",
    "extract_mp4_creation_date",
    "extract_avi_creation_date",
    "extract_m4v_creation_date",
    "extract_3gp_creation_date",
    "extract_png_creation_date",
    "extract_gif_creation_date",
    # Registries
    "VIDEO_EXTRACTORS",
    "IMAGE_EXTRACTORS",
    "ALL_EXTRACTORS",
]

"""
File type extractors for photo organizer.

This module provides a unified interface to all file type extractors,
consolidating separate modules for better maintainability.
"""

from .heif_extractor import (
    HEIF_EXTRACTORS,
    extract_heif_creation_date,
)
from .image_extractors import (
    IMAGE_EXTRACTORS,
    extract_avif_creation_date,
    extract_bmp_creation_date,
    extract_gif_creation_date,
    extract_jpeg2000_creation_date,
    extract_mpo_creation_date,
    extract_png_creation_date,
    extract_tiff_creation_date,
    extract_webp_creation_date,
)
from .raw_extractors import (
    RAW_EXTRACTORS,
    extract_arw_creation_date,
    extract_cr2_creation_date,
    extract_cr3_creation_date,
    extract_dng_creation_date,
    extract_nef_creation_date,
    extract_orf_creation_date,
    extract_raf_creation_date,
    extract_rw2_creation_date,
)
from .video_extractors import (
    VIDEO_EXTRACTORS,
    extract_3gp_creation_date,
    extract_avi_creation_date,
    extract_m4v_creation_date,
    extract_mkv_creation_date,
    extract_mov_creation_date,
    extract_mp4_creation_date,
    extract_webm_creation_date,
)

# Combined registry of all extractors
ALL_EXTRACTORS = {
    **VIDEO_EXTRACTORS,
    **IMAGE_EXTRACTORS,
    **RAW_EXTRACTORS,
    **HEIF_EXTRACTORS,
}

__all__ = [
    # Individual extractor functions — video
    "extract_mov_creation_date",
    "extract_mp4_creation_date",
    "extract_avi_creation_date",
    "extract_m4v_creation_date",
    "extract_3gp_creation_date",
    "extract_mkv_creation_date",
    "extract_webm_creation_date",
    # Individual extractor functions — image
    "extract_png_creation_date",
    "extract_gif_creation_date",
    "extract_webp_creation_date",
    "extract_tiff_creation_date",
    "extract_bmp_creation_date",
    "extract_jpeg2000_creation_date",
    "extract_mpo_creation_date",
    "extract_avif_creation_date",
    # Individual extractor functions — RAW
    "extract_dng_creation_date",
    "extract_cr2_creation_date",
    "extract_cr3_creation_date",
    "extract_nef_creation_date",
    "extract_arw_creation_date",
    "extract_orf_creation_date",
    "extract_rw2_creation_date",
    "extract_raf_creation_date",
    # Individual extractor functions — HEIF
    "extract_heif_creation_date",
    # Registries
    "VIDEO_EXTRACTORS",
    "IMAGE_EXTRACTORS",
    "RAW_EXTRACTORS",
    "HEIF_EXTRACTORS",
    "ALL_EXTRACTORS",
]

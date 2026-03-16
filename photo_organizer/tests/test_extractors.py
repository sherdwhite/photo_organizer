import importlib
import json
from datetime import datetime
from unittest.mock import MagicMock, patch


from photo_organizer.file_types.video_extractors import (
    _extract_ffprobe_creation_date,
    _extract_hachoir_creation_date,
    _extract_video_creation_date,
    _find_date_in_tags,
    extract_3gp_creation_date,
    extract_avi_creation_date,
    extract_m4v_creation_date,
    extract_mkv_creation_date,
    extract_mov_creation_date,
    extract_mp4_creation_date,
    extract_webm_creation_date,
)
from photo_organizer.file_types.image_extractors import (
    _extract_pil_creation_date,
    _extract_pil_exif_date,
    extract_bmp_creation_date,
    extract_gif_creation_date,
    extract_png_creation_date,
    extract_tiff_creation_date,
    extract_webp_creation_date,
    extract_mpo_creation_date,
    extract_avif_creation_date,
    extract_jpeg2000_creation_date,
)
from photo_organizer.file_types.raw_extractors import (
    _extract_raw_creation_date,
    extract_arw_creation_date,
    extract_cr2_creation_date,
    extract_cr3_creation_date,
    extract_dng_creation_date,
    extract_nef_creation_date,
    extract_orf_creation_date,
    extract_raf_creation_date,
    extract_rw2_creation_date,
)
from photo_organizer.file_types.heif_extractor import (
    _ensure_heif_support,
    extract_heif_creation_date,
)


# ── Video: _find_date_in_tags ────────────────────────────────────────


class TestFindDateInTags:
    def test_empty_tags_returns_none(self):
        assert _find_date_in_tags({}) is None

    def test_none_tags_returns_none(self):
        assert _find_date_in_tags(None) is None

    def test_creation_time_found(self):
        tags = {"creation_time": "2023-06-15T10:30:00.000000Z"}
        result = _find_date_in_tags(tags)
        assert result == "2023:06:15 10:30:00"

    def test_date_tag_found(self):
        tags = {"date": "2023:06:15 10:30:00"}
        result = _find_date_in_tags(tags)
        assert result == "2023:06:15 10:30:00"

    def test_case_insensitive_keys(self):
        tags = {"Creation_Time": "2023-06-15T10:30:00"}
        result = _find_date_in_tags(tags)
        assert result == "2023:06:15 10:30:00"

    def test_apple_quicktime_tag(self):
        tags = {"com.apple.quicktime.creationdate": "2023-06-15T10:30:00+05:30"}
        result = _find_date_in_tags(tags)
        assert result == "2023:06:15 10:30:00"

    def test_invalid_date_value_returns_none(self):
        tags = {"creation_time": "not a date"}
        result = _find_date_in_tags(tags)
        assert result is None


# ── Video: _extract_ffprobe_creation_date ────────────────────────────


class TestExtractFfprobeCreationDate:
    @patch("photo_organizer.file_types.video_extractors._FFPROBE_BIN", None)
    def test_no_ffprobe_returns_none(self):
        result = _extract_ffprobe_creation_date("/fake/video.mp4", "MP4")
        assert result is None

    @patch(
        "photo_organizer.file_types.video_extractors._FFPROBE_BIN", "/usr/bin/ffprobe"
    )
    @patch("photo_organizer.file_types.video_extractors.subprocess.run")
    def test_ffprobe_format_tags(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(
                {
                    "format": {
                        "tags": {"creation_time": "2023-06-15T10:30:00.000000Z"}
                    },
                    "streams": [],
                }
            ),
        )
        result = _extract_ffprobe_creation_date("/fake/video.mp4", "MP4")
        assert result == "2023:06:15 10:30:00"

    @patch(
        "photo_organizer.file_types.video_extractors._FFPROBE_BIN", "/usr/bin/ffprobe"
    )
    @patch("photo_organizer.file_types.video_extractors.subprocess.run")
    def test_ffprobe_stream_tags(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(
                {
                    "format": {"tags": {}},
                    "streams": [
                        {"tags": {"creation_time": "2023-06-15T10:30:00.000000Z"}}
                    ],
                }
            ),
        )
        result = _extract_ffprobe_creation_date("/fake/video.mp4", "MP4")
        assert result == "2023:06:15 10:30:00"

    @patch(
        "photo_organizer.file_types.video_extractors._FFPROBE_BIN", "/usr/bin/ffprobe"
    )
    @patch("photo_organizer.file_types.video_extractors.subprocess.run")
    def test_ffprobe_nonzero_return(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = _extract_ffprobe_creation_date("/fake/video.mp4", "MP4")
        assert result is None

    @patch(
        "photo_organizer.file_types.video_extractors._FFPROBE_BIN", "/usr/bin/ffprobe"
    )
    @patch("photo_organizer.file_types.video_extractors.subprocess.run")
    def test_ffprobe_timeout(self, mock_run):
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ffprobe", timeout=10)
        result = _extract_ffprobe_creation_date("/fake/video.mp4", "MP4")
        assert result is None

    @patch(
        "photo_organizer.file_types.video_extractors._FFPROBE_BIN", "/usr/bin/ffprobe"
    )
    @patch("photo_organizer.file_types.video_extractors.subprocess.run")
    def test_ffprobe_os_error(self, mock_run):
        mock_run.side_effect = OSError("ffprobe not found")
        result = _extract_ffprobe_creation_date("/fake/video.mp4", "MP4")
        assert result is None

    @patch(
        "photo_organizer.file_types.video_extractors._FFPROBE_BIN", "/usr/bin/ffprobe"
    )
    @patch("photo_organizer.file_types.video_extractors.subprocess.run")
    def test_ffprobe_no_tags(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"format": {}, "streams": []}),
        )
        result = _extract_ffprobe_creation_date("/fake/video.mp4", "MP4")
        assert result is None


# ── Video: _extract_hachoir_creation_date ────────────────────────────


class TestExtractHachoirCreationDate:
    @patch("photo_organizer.file_types.video_extractors.createParser")
    def test_no_parser_returns_none(self, mock_create_parser):
        mock_create_parser.return_value = None
        result = _extract_hachoir_creation_date("/fake/video.mp4", "MP4")
        assert result is None

    @patch("photo_organizer.file_types.video_extractors.extractMetadata")
    @patch("photo_organizer.file_types.video_extractors.createParser")
    def test_with_creation_date(self, mock_create_parser, mock_extract_meta):
        mock_parser = MagicMock()
        mock_parser.__enter__ = MagicMock(return_value=mock_parser)
        mock_parser.__exit__ = MagicMock(return_value=False)
        mock_create_parser.return_value = mock_parser

        mock_meta = MagicMock()
        mock_meta.has.return_value = True
        mock_meta.get.return_value = datetime(2023, 6, 15, 10, 30, 0)
        mock_extract_meta.return_value = mock_meta

        result = _extract_hachoir_creation_date("/fake/video.mp4", "MP4")
        assert result == "2023:06:15 10:30:00"

    @patch("photo_organizer.file_types.video_extractors.extractMetadata")
    @patch("photo_organizer.file_types.video_extractors.createParser")
    def test_no_creation_date_metadata(self, mock_create_parser, mock_extract_meta):
        mock_parser = MagicMock()
        mock_parser.__enter__ = MagicMock(return_value=mock_parser)
        mock_parser.__exit__ = MagicMock(return_value=False)
        mock_create_parser.return_value = mock_parser

        mock_meta = MagicMock()
        mock_meta.has.return_value = False
        mock_extract_meta.return_value = mock_meta

        result = _extract_hachoir_creation_date("/fake/video.mp4", "MP4")
        assert result is None


# ── Video: _extract_video_creation_date (combined) ───────────────────


class TestExtractVideoCreationDate:
    @patch("photo_organizer.file_types.video_extractors._extract_hachoir_creation_date")
    @patch("photo_organizer.file_types.video_extractors._extract_ffprobe_creation_date")
    def test_ffprobe_success_skips_hachoir(self, mock_ffprobe, mock_hachoir):
        mock_ffprobe.return_value = "2023:06:15 10:30:00"
        result = _extract_video_creation_date("/fake/video.mp4", "MP4")
        assert result == "2023:06:15 10:30:00"
        mock_hachoir.assert_not_called()

    @patch("photo_organizer.file_types.video_extractors._extract_hachoir_creation_date")
    @patch("photo_organizer.file_types.video_extractors._extract_ffprobe_creation_date")
    def test_ffprobe_fails_falls_back_to_hachoir(self, mock_ffprobe, mock_hachoir):
        mock_ffprobe.return_value = None
        mock_hachoir.return_value = "2023:06:15 10:30:00"
        result = _extract_video_creation_date("/fake/video.mp4", "MP4")
        assert result == "2023:06:15 10:30:00"


# ── Video: convenience functions ─────────────────────────────────────


class TestVideoConvenienceFunctionsBase:
    @patch(
        "photo_organizer.file_types.video_extractors._extract_video_creation_date",
        return_value="2023:06:15 10:30:00",
    )
    def test_extract_mov(self, mock_extract):
        assert extract_mov_creation_date("/f.mov") == "2023:06:15 10:30:00"
        mock_extract.assert_called_with("/f.mov", "MOV")

    @patch(
        "photo_organizer.file_types.video_extractors._extract_video_creation_date",
        return_value="2023:06:15 10:30:00",
    )
    def test_extract_mp4(self, mock_extract):
        assert extract_mp4_creation_date("/f.mp4") == "2023:06:15 10:30:00"
        mock_extract.assert_called_with("/f.mp4", "MP4")


# ── Image: _extract_pil_creation_date ────────────────────────────────


class TestExtractPilCreationDate:
    @patch("photo_organizer.file_types.image_extractors.PILImage")
    def test_with_metadata_field(self, mock_pil):
        mock_img = MagicMock()
        mock_img.info = {"creation_time": "2023:06:15 10:30:00"}
        mock_img.__enter__ = MagicMock(return_value=mock_img)
        mock_img.__exit__ = MagicMock(return_value=False)
        mock_pil.open.return_value = mock_img

        result = _extract_pil_creation_date("/f.png", "PNG", ["creation_time"])
        assert result == "2023:06:15 10:30:00"

    @patch("photo_organizer.file_types.image_extractors.PILImage")
    def test_no_metadata_returns_none(self, mock_pil):
        mock_img = MagicMock()
        mock_img.info = {}
        mock_img.__enter__ = MagicMock(return_value=mock_img)
        mock_img.__exit__ = MagicMock(return_value=False)
        mock_pil.open.return_value = mock_img

        result = _extract_pil_creation_date("/f.png", "PNG", ["creation_time"])
        assert result is None

    def test_nonexistent_file_returns_none(self):
        result = _extract_pil_creation_date(
            "/nonexistent.png", "PNG", ["creation_time"]
        )
        assert result is None


# ── Image: _extract_pil_exif_date ────────────────────────────────────


class TestExtractPilExifDate:
    @patch("photo_organizer.file_types.image_extractors.PILImage")
    def test_with_exif_date(self, mock_pil):
        mock_img = MagicMock()
        mock_exif = {36867: "2023:06:15 10:30:00"}
        mock_img.getexif.return_value = mock_exif
        mock_img.__enter__ = MagicMock(return_value=mock_img)
        mock_img.__exit__ = MagicMock(return_value=False)
        mock_pil.open.return_value = mock_img

        result = _extract_pil_exif_date("/f.tiff", "TIFF")
        assert result == "2023:06:15 10:30:00"

    @patch("photo_organizer.file_types.image_extractors.PILImage")
    def test_no_exif_returns_none(self, mock_pil):
        mock_img = MagicMock()
        mock_img.getexif.return_value = None
        mock_img.__enter__ = MagicMock(return_value=mock_img)
        mock_img.__exit__ = MagicMock(return_value=False)
        mock_pil.open.return_value = mock_img

        result = _extract_pil_exif_date("/f.tiff", "TIFF")
        assert result is None

    def test_nonexistent_file_returns_none(self):
        result = _extract_pil_exif_date("/nonexistent.tiff", "TIFF")
        assert result is None


# ── Image: format-specific extractors ────────────────────────────────


class TestImageExtractors:
    @patch("photo_organizer.file_types.image_extractors._extract_pil_creation_date")
    def test_png_extractor(self, mock_extract):
        mock_extract.return_value = "2023:06:15 10:30:00"
        result = extract_png_creation_date("/f.png")
        assert result == "2023:06:15 10:30:00"

    @patch("photo_organizer.file_types.image_extractors._extract_pil_creation_date")
    def test_gif_extractor(self, mock_extract):
        mock_extract.return_value = "2023:06:15 10:30:00"
        result = extract_gif_creation_date("/f.gif")
        assert result == "2023:06:15 10:30:00"

    @patch("photo_organizer.file_types.image_extractors._extract_pil_exif_date")
    def test_webp_extractor(self, mock_extract):
        mock_extract.return_value = "2023:06:15 10:30:00"
        result = extract_webp_creation_date("/f.webp")
        assert result == "2023:06:15 10:30:00"

    @patch("photo_organizer.file_types.image_extractors._extract_pil_exif_date")
    def test_tiff_extractor(self, mock_extract):
        mock_extract.return_value = "2023:06:15 10:30:00"
        result = extract_tiff_creation_date("/f.tiff")
        assert result == "2023:06:15 10:30:00"

    def test_bmp_returns_none(self):
        result = extract_bmp_creation_date("/f.bmp")
        assert result is None

    @patch("photo_organizer.file_types.image_extractors._extract_pil_exif_date")
    def test_jpeg2000_extractor(self, mock_extract):
        mock_extract.return_value = "2023:06:15 10:30:00"
        result = extract_jpeg2000_creation_date("/f.jp2")
        assert result == "2023:06:15 10:30:00"

    @patch("photo_organizer.file_types.image_extractors._extract_pil_exif_date")
    def test_mpo_extractor(self, mock_extract):
        mock_extract.return_value = "2023:06:15 10:30:00"
        result = extract_mpo_creation_date("/f.mpo")
        assert result == "2023:06:15 10:30:00"

    @patch("photo_organizer.file_types.image_extractors._extract_pil_exif_date")
    def test_avif_extractor(self, mock_extract):
        mock_extract.return_value = "2023:06:15 10:30:00"
        result = extract_avif_creation_date("/f.avif")
        assert result == "2023:06:15 10:30:00"


# ── RAW: _extract_raw_creation_date ──────────────────────────────────


class TestRawExtractors:
    @patch("exifread.process_file")
    def test_with_datetime_original(self, mock_process_file):
        mock_process_file.return_value = {
            "EXIF DateTimeOriginal": "2023:06:15 10:30:00"
        }
        with patch("builtins.open", MagicMock()):
            result = _extract_raw_creation_date("/f.cr2", "CR2")
        assert result == "2023:06:15 10:30:00"

    @patch("exifread.process_file")
    def test_no_date_tags(self, mock_process_file):
        mock_process_file.return_value = {}
        with patch("builtins.open", MagicMock()):
            result = _extract_raw_creation_date("/f.cr2", "CR2")
        assert result is None

    def test_nonexistent_file_returns_none(self):
        result = _extract_raw_creation_date("/nonexistent.cr2", "CR2")
        assert result is None

    @patch("photo_organizer.file_types.raw_extractors._extract_raw_creation_date")
    def test_dng_convenience(self, mock_extract):
        mock_extract.return_value = "2023:06:15 10:30:00"
        result = extract_dng_creation_date("/f.dng")
        assert result == "2023:06:15 10:30:00"
        mock_extract.assert_called_with("/f.dng", "DNG")

    @patch("photo_organizer.file_types.raw_extractors._extract_raw_creation_date")
    def test_cr2_convenience(self, mock_extract):
        mock_extract.return_value = "2023:06:15 10:30:00"
        result = extract_cr2_creation_date("/f.cr2")
        assert result == "2023:06:15 10:30:00"

    @patch("photo_organizer.file_types.raw_extractors._extract_raw_creation_date")
    def test_nef_convenience(self, mock_extract):
        mock_extract.return_value = "2023:06:15 10:30:00"
        result = extract_nef_creation_date("/f.nef")
        assert result == "2023:06:15 10:30:00"


# ── HEIF: _ensure_heif_support ───────────────────────────────────────


class TestHeifExtractor:
    def test_ensure_heif_support_succeeds(self):
        # pillow-heif is installed in our venv
        assert _ensure_heif_support() is True

    def test_ensure_heif_already_registered(self):
        """Second call should use cached flag."""
        import photo_organizer.file_types.heif_extractor as mod

        original = mod._heif_registered
        try:
            mod._heif_registered = True
            assert _ensure_heif_support() is True
        finally:
            mod._heif_registered = original

    def test_extract_heif_nonexistent_file(self):
        result = extract_heif_creation_date("/nonexistent.heic")
        assert result is None

    @patch("photo_organizer.file_types.heif_extractor._ensure_heif_support")
    def test_extract_heif_no_support(self, mock_support):
        mock_support.return_value = False
        result = extract_heif_creation_date("/f.heic")
        assert result is None

    @patch("photo_organizer.file_types.heif_extractor._ensure_heif_support")
    def test_extract_heif_with_exif(self, mock_support):
        mock_support.return_value = True

        mock_img = MagicMock()
        mock_exif = {36867: "2023:06:15 10:30:00"}
        mock_img.getexif.return_value = mock_exif
        mock_img.__enter__ = MagicMock(return_value=mock_img)
        mock_img.__exit__ = MagicMock(return_value=False)

        with patch("PIL.Image.open", return_value=mock_img):
            result = extract_heif_creation_date("/f.heic")
        assert result == "2023:06:15 10:30:00"

    @patch("photo_organizer.file_types.heif_extractor._ensure_heif_support")
    def test_extract_heif_no_exif(self, mock_support):
        mock_support.return_value = True

        mock_img = MagicMock()
        mock_img.getexif.return_value = None
        mock_img.__enter__ = MagicMock(return_value=mock_img)
        mock_img.__exit__ = MagicMock(return_value=False)

        with patch("PIL.Image.open", return_value=mock_img):
            result = extract_heif_creation_date("/f.heic")
        assert result is None


# ── Additional video convenience functions ───────────────────────────


class TestVideoConvenienceFunctions:
    @patch(
        "photo_organizer.file_types.video_extractors._extract_video_creation_date",
        return_value="2023:01:01 00:00:00",
    )
    def test_extract_avi(self, mock_extract):
        assert extract_avi_creation_date("/f.avi") == "2023:01:01 00:00:00"
        mock_extract.assert_called_once_with("/f.avi", "AVI")

    @patch(
        "photo_organizer.file_types.video_extractors._extract_video_creation_date",
        return_value="2023:01:01 00:00:00",
    )
    def test_extract_m4v(self, mock_extract):
        assert extract_m4v_creation_date("/f.m4v") == "2023:01:01 00:00:00"
        mock_extract.assert_called_once_with("/f.m4v", "M4V")

    @patch(
        "photo_organizer.file_types.video_extractors._extract_video_creation_date",
        return_value="2023:01:01 00:00:00",
    )
    def test_extract_3gp(self, mock_extract):
        assert extract_3gp_creation_date("/f.3gp") == "2023:01:01 00:00:00"
        mock_extract.assert_called_once_with("/f.3gp", "3GP")

    @patch(
        "photo_organizer.file_types.video_extractors._extract_video_creation_date",
        return_value="2023:01:01 00:00:00",
    )
    def test_extract_mkv(self, mock_extract):
        assert extract_mkv_creation_date("/f.mkv") == "2023:01:01 00:00:00"
        mock_extract.assert_called_once_with("/f.mkv", "MKV")

    @patch(
        "photo_organizer.file_types.video_extractors._extract_video_creation_date",
        return_value="2023:01:01 00:00:00",
    )
    def test_extract_webm(self, mock_extract):
        assert extract_webm_creation_date("/f.webm") == "2023:01:01 00:00:00"
        mock_extract.assert_called_once_with("/f.webm", "WebM")


# ── Hachoir error handler ────────────────────────────────────────────


class TestHachoirErrors:
    def test_oserror_returns_none(self):
        with patch(
            "photo_organizer.file_types.video_extractors.createParser",
            side_effect=OSError("fail"),
        ):
            result = _extract_hachoir_creation_date("/f.mov", "MOV")
        assert result is None

    def test_ioerror_returns_none(self):
        with patch(
            "photo_organizer.file_types.video_extractors.createParser",
            side_effect=IOError("fail"),
        ):
            result = _extract_hachoir_creation_date("/f.mov", "MOV")
        assert result is None

    def test_valueerror_returns_none(self):
        with patch(
            "photo_organizer.file_types.video_extractors.createParser",
            side_effect=ValueError("fail"),
        ):
            result = _extract_hachoir_creation_date("/f.mov", "MOV")
        assert result is None


# ── Additional RAW convenience functions ─────────────────────────────


class TestRawConvenienceFunctions:
    @patch(
        "photo_organizer.file_types.raw_extractors._extract_raw_creation_date",
        return_value="2023:01:01 00:00:00",
    )
    def test_extract_cr3(self, mock_extract):
        assert extract_cr3_creation_date("/f.cr3") == "2023:01:01 00:00:00"
        mock_extract.assert_called_once_with("/f.cr3", "CR3")

    @patch(
        "photo_organizer.file_types.raw_extractors._extract_raw_creation_date",
        return_value="2023:01:01 00:00:00",
    )
    def test_extract_arw(self, mock_extract):
        assert extract_arw_creation_date("/f.arw") == "2023:01:01 00:00:00"
        mock_extract.assert_called_once_with("/f.arw", "ARW")

    @patch(
        "photo_organizer.file_types.raw_extractors._extract_raw_creation_date",
        return_value="2023:01:01 00:00:00",
    )
    def test_extract_orf(self, mock_extract):
        assert extract_orf_creation_date("/f.orf") == "2023:01:01 00:00:00"
        mock_extract.assert_called_once_with("/f.orf", "ORF")

    @patch(
        "photo_organizer.file_types.raw_extractors._extract_raw_creation_date",
        return_value="2023:01:01 00:00:00",
    )
    def test_extract_rw2(self, mock_extract):
        assert extract_rw2_creation_date("/f.rw2") == "2023:01:01 00:00:00"
        mock_extract.assert_called_once_with("/f.rw2", "RW2")

    @patch(
        "photo_organizer.file_types.raw_extractors._extract_raw_creation_date",
        return_value="2023:01:01 00:00:00",
    )
    def test_extract_raf(self, mock_extract):
        assert extract_raf_creation_date("/f.raf") == "2023:01:01 00:00:00"
        mock_extract.assert_called_once_with("/f.raf", "RAF")


# ── RAW error handlers ──────────────────────────────────────────────


class TestRawErrorHandlers:
    def test_import_error_returns_none(self):
        with patch.dict("sys.modules", {"exifread": None}):
            result = _extract_raw_creation_date("/f.cr2", "CR2")
        assert result is None

    def test_generic_exception_returns_none(self):
        with patch("builtins.open", side_effect=RuntimeError("boom")):
            result = _extract_raw_creation_date("/f.cr2", "CR2")
        assert result is None


# ── HEIF error handlers ─────────────────────────────────────────────


class TestHeifErrorHandlers:
    def test_ensure_heif_support_import_error(self):
        import photo_organizer.file_types.heif_extractor as heif_mod

        heif_mod._heif_registered = False
        with patch.dict("sys.modules", {"pillow_heif": None}):
            result = _ensure_heif_support()
        assert result is False
        heif_mod._heif_registered = False  # reset

    @patch("photo_organizer.file_types.heif_extractor._ensure_heif_support")
    def test_oserror_returns_none(self, mock_support):
        mock_support.return_value = True
        with patch("PIL.Image.open", side_effect=OSError("fail")):
            result = extract_heif_creation_date("/f.heic")
        assert result is None

    @patch("photo_organizer.file_types.heif_extractor._ensure_heif_support")
    def test_exif_present_but_no_dates(self, mock_support):
        """Test HEIF with EXIF data but no date tags (lines 88-89)."""
        mock_support.return_value = True
        mock_img = MagicMock()
        mock_img.getexif.return_value = {999: "some_value"}  # non-date tag
        mock_img.__enter__ = MagicMock(return_value=mock_img)
        mock_img.__exit__ = MagicMock(return_value=False)

        with patch("PIL.Image.open", return_value=mock_img):
            result = extract_heif_creation_date("/f.heic")
        assert result is None

    @patch("photo_organizer.file_types.heif_extractor._ensure_heif_support")
    def test_generic_exception_returns_none(self, mock_support):
        mock_support.return_value = True
        with patch("PIL.Image.open", side_effect=RuntimeError("boom")):
            result = extract_heif_creation_date("/f.heic")
        assert result is None


# ── Image extractor error handler ────────────────────────────────────


class TestImageExtractorErrors:
    def test_pil_creation_date_oserror(self):
        with patch("PIL.Image.open", side_effect=OSError("fail")):
            result = _extract_pil_creation_date("/f.png", "PNG", ["creation_time"])
        assert result is None

    def test_pil_exif_date_oserror(self):
        with patch("PIL.Image.open", side_effect=OSError("fail")):
            result = _extract_pil_exif_date("/f.tiff", "TIFF")
        assert result is None

    def test_pil_exif_date_no_date_tags(self):
        """EXIF present but no date tags → return None (line 110)."""
        mock_img = MagicMock()
        mock_img.getexif.return_value = {999: "some_value"}
        mock_img.__enter__ = MagicMock(return_value=mock_img)
        mock_img.__exit__ = MagicMock(return_value=False)

        with patch("PIL.Image.open", return_value=mock_img):
            result = _extract_pil_exif_date("/f.tiff", "TIFF")
        assert result is None


# ── Video: module-level ffprobe-not-found branch ─────────────────────


class TestVideoFfprobeNotFound:
    def test_ffprobe_not_found_branch(self):
        """Cover line 28: logger.info when ffprobe is not installed."""
        import photo_organizer.file_types.video_extractors as vid_mod

        with patch("shutil.which", return_value=None):
            importlib.reload(vid_mod)

        assert vid_mod._FFPROBE_BIN is None

        # Restore module to original state
        importlib.reload(vid_mod)

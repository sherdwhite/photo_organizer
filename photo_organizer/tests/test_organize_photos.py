import logging
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from photo_organizer.organize_photos import (
    _cross_reference_dates,
    _try_build_datetime,
    extract_date_from_filename,
    get_file_creation_date,
    organize,
)


@pytest.fixture
def setup_dirs():
    """Create temporary test directories and clean them up after test."""
    test_dir = tempfile.mkdtemp()
    origin_dir = os.path.join(test_dir, "origin")
    destination_dir = os.path.join(test_dir, "destination")
    os.makedirs(origin_dir)
    os.makedirs(destination_dir)
    yield origin_dir, destination_dir

    # Close all logging handlers to release file locks
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)

    shutil.rmtree(test_dir)


@patch("photo_organizer.organize_photos.get_file_creation_date")
def test_move_files_to_correct_destination(mock_get_creation_date, setup_dirs):
    """Test that files are moved to correct year/month folders."""
    origin_dir, destination_dir = setup_dirs
    mock_get_creation_date.return_value = "2023:01:01 12:00:00"

    test_file = os.path.join(origin_dir, "test.mov")
    with open(test_file, "w") as f:
        f.write("dummy data")

    organize(origin_dir, destination_dir)

    expected_dir = os.path.join(destination_dir, "2023", "01")
    expected_file = os.path.join(expected_dir, "test.mov")

    assert os.path.exists(expected_dir)
    assert os.path.exists(expected_file)
    assert not os.path.exists(test_file)


def test_remove_empty_directories(setup_dirs):
    """Test that empty directories are removed after organization."""
    origin_dir, destination_dir = setup_dirs

    empty_dir = os.path.join(origin_dir, "empty_dir")
    os.makedirs(empty_dir)

    organize(origin_dir, destination_dir)

    assert not os.path.exists(empty_dir)


def test_delete_specific_files(setup_dirs):
    """Test that specific unwanted files are deleted."""
    origin_dir, destination_dir = setup_dirs

    thumbs_file = os.path.join(origin_dir, "Thumbs.db")
    desktop_file = os.path.join(origin_dir, "desktop")
    with open(thumbs_file, "w") as f:
        f.write("dummy data")
    with open(desktop_file, "w") as f:
        f.write("dummy data")

    organize(origin_dir, destination_dir)

    assert not os.path.exists(thumbs_file)
    assert not os.path.exists(desktop_file)


@patch("photo_organizer.organize_photos.get_file_creation_date")
@patch("photo_organizer.organize_photos.log_and_handle_error")
def test_handle_files_without_exif_data(
    mock_log_and_handle_error,
    mock_get_creation_date,
    setup_dirs,
):
    """Test proper error handling for files without EXIF data."""
    origin_dir, destination_dir = setup_dirs
    mock_get_creation_date.return_value = None

    test_file = os.path.join(origin_dir, "test.jpg")
    with open(test_file, "w") as f:
        f.write("dummy data")

    organize(origin_dir, destination_dir)

    mock_log_and_handle_error.assert_called_once()


@patch("photo_organizer.organize_photos.get_file_creation_date")
@patch("photo_organizer.organize_photos.log_and_handle_error")
def test_handle_files_with_bad_exif_data(
    mock_log_and_handle_error,
    mock_get_creation_date,
    setup_dirs,
):
    """Test proper error handling for files with corrupted EXIF."""
    origin_dir, destination_dir = setup_dirs
    mock_get_creation_date.side_effect = ValueError("Bad EXIF data")

    test_file = os.path.join(origin_dir, "test.jpg")
    with open(test_file, "w") as f:
        f.write("dummy data")

    organize(origin_dir, destination_dir)

    mock_log_and_handle_error.assert_called_once()


@patch(
    "photo_organizer.organize_photos.os.remove",
    side_effect=PermissionError("Permission denied"),
)
@patch("photo_organizer.organize_photos.logger.error")
def test_handle_permission_error(mock_logger_error, mock_os_remove, setup_dirs):
    """Test proper error handling for file permission errors."""
    origin_dir, destination_dir = setup_dirs

    # Create a file that will match FILES_TO_DELETE to trigger os.remove
    test_file = os.path.join(origin_dir, "Thumbs.db")
    with open(test_file, "w") as f:
        f.write("dummy data")

    organize(origin_dir, destination_dir)

    mock_logger_error.assert_called()


# ── extract_date_from_filename ───────────────────────────────────────


class TestExtractDateFromFilename:
    def test_android_pattern(self):
        result = extract_date_from_filename("IMG_20230615_103045.jpg")
        assert result == "2023:06:15 10:30:45"

    def test_pixel_pattern(self):
        result = extract_date_from_filename("PXL_20230115_103045123.jpg")
        assert result == "2023:01:15 10:30:45"

    def test_screenshot_android_pattern(self):
        result = extract_date_from_filename("Screenshot_20230115-103045.png")
        assert result == "2023:01:15 10:30:45"

    def test_bare_date_time(self):
        result = extract_date_from_filename("20230615_103045.jpg")
        assert result == "2023:06:15 10:30:45"

    def test_iso_like_pattern(self):
        result = extract_date_from_filename("Screenshot 2023-06-15 at 10.30.45.png")
        assert result == "2023:06:15 10:30:45"

    def test_signal_pattern(self):
        result = extract_date_from_filename("signal-2023-06-15-10-30-45.jpg")
        assert result == "2023:06:15 10:30:45"

    def test_date_only_fallback(self):
        result = extract_date_from_filename("2023-06-15_photo.jpg")
        assert result == "2023:06:15 12:00:00"

    def test_date_only_compact(self):
        result = extract_date_from_filename("20230615_photo.jpg")
        assert result == "2023:06:15 12:00:00"

    def test_no_date_pattern(self):
        result = extract_date_from_filename("vacation_photo.jpg")
        assert result is None

    def test_whatsapp_pattern(self):
        result = extract_date_from_filename("IMG-20230615-103045.jpg")
        assert result == "2023:06:15 10:30:45"

    def test_invalid_date_values(self):
        result = extract_date_from_filename("IMG_20231340_103045.jpg")
        assert result is None


# ── _try_build_datetime ──────────────────────────────────────────────


class TestTryBuildDatetime:
    def test_valid_datetime(self):
        dt = _try_build_datetime("2023", "06", "15", "10", "30", "45")
        assert dt is not None
        assert dt.year == 2023
        assert dt.month == 6

    def test_invalid_month(self):
        dt = _try_build_datetime("2023", "13", "15", "10", "30", "45")
        assert dt is None

    def test_invalid_day(self):
        dt = _try_build_datetime("2023", "02", "30", "10", "30", "45")
        assert dt is None

    def test_invalid_hour(self):
        dt = _try_build_datetime("2023", "06", "15", "25", "30", "45")
        assert dt is None


# ── get_file_creation_date ───────────────────────────────────────────


class TestGetFileCreationDate:
    @patch("photo_organizer.organize_photos.extract_xmp_date")
    @patch("photo_organizer.organize_photos.extract_exif_via_pillow")
    @patch("photo_organizer.organize_photos.extract_exif_data")
    def test_exif_date_returned(self, mock_exif, mock_pillow, mock_xmp, tmp_path):
        test_file = tmp_path / "photo.jpg"
        test_file.write_text("data")
        mock_exif.return_value = "2023:06:15 10:30:00"

        result = get_file_creation_date(str(test_file))
        assert result == "2023:06:15 10:30:00"

    @patch("photo_organizer.organize_photos.get_filesystem_date")
    @patch("photo_organizer.organize_photos.extract_xmp_date")
    @patch("photo_organizer.organize_photos.extract_exif_via_pillow")
    @patch("photo_organizer.organize_photos.extract_exif_data")
    def test_fallback_to_filename(
        self, mock_exif, mock_pillow, mock_xmp, mock_fs, tmp_path
    ):
        test_file = tmp_path / "IMG_20230615_103045.jpg"
        test_file.write_text("data")
        mock_exif.return_value = None
        mock_pillow.return_value = None
        mock_xmp.return_value = None

        result = get_file_creation_date(str(test_file))
        assert result == "2023:06:15 10:30:45"

    @patch("photo_organizer.organize_photos.get_filesystem_date")
    @patch("photo_organizer.organize_photos.extract_xmp_date")
    @patch("photo_organizer.organize_photos.extract_exif_via_pillow")
    @patch("photo_organizer.organize_photos.extract_exif_data")
    def test_fallback_to_filesystem(
        self, mock_exif, mock_pillow, mock_xmp, mock_fs, tmp_path
    ):
        test_file = tmp_path / "nodate.jpg"
        test_file.write_text("data")
        mock_exif.return_value = None
        mock_pillow.return_value = None
        mock_xmp.return_value = None
        mock_fs.return_value = "2023:06:15 10:30:00"

        result = get_file_creation_date(str(test_file))
        assert result == "2023:06:15 10:30:00"

    @patch("photo_organizer.organize_photos.get_filesystem_date")
    @patch("photo_organizer.organize_photos.extract_xmp_date")
    @patch("photo_organizer.organize_photos.extract_exif_via_pillow")
    @patch("photo_organizer.organize_photos.extract_exif_data")
    def test_all_fallbacks_fail_returns_none(
        self, mock_exif, mock_pillow, mock_xmp, mock_fs, tmp_path
    ):
        test_file = tmp_path / "nodate.jpg"
        test_file.write_text("data")
        mock_exif.return_value = None
        mock_pillow.return_value = None
        mock_xmp.return_value = None
        mock_fs.return_value = None

        result = get_file_creation_date(str(test_file))
        assert result is None

    @patch("photo_organizer.organize_photos.extract_xmp_date")
    @patch("photo_organizer.organize_photos.extract_exif_via_pillow")
    @patch("photo_organizer.organize_photos.extract_exif_data")
    def test_xmp_date_used(self, mock_exif, mock_pillow, mock_xmp, tmp_path):
        test_file = tmp_path / "photo.jpg"
        test_file.write_text("data")
        mock_exif.return_value = None
        mock_pillow.return_value = None
        mock_xmp.return_value = "2023:06:15 10:30:00"

        result = get_file_creation_date(str(test_file))
        assert result == "2023:06:15 10:30:00"

    @patch("photo_organizer.organize_photos.extract_xmp_date")
    @patch("photo_organizer.organize_photos.extract_exif_via_pillow")
    @patch("photo_organizer.organize_photos.extract_exif_data")
    def test_pillow_fallback_used(self, mock_exif, mock_pillow, mock_xmp, tmp_path):
        test_file = tmp_path / "photo.jpg"
        test_file.write_text("data")
        mock_exif.return_value = None
        mock_pillow.return_value = "2023:06:15 10:30:00"

        result = get_file_creation_date(str(test_file))
        assert result == "2023:06:15 10:30:00"

    @patch("photo_organizer.organize_photos.extract_xmp_date")
    def test_video_skips_exif_pillow(self, mock_xmp, tmp_path):
        """Video files should skip EXIF/Pillow steps."""
        test_file = tmp_path / "video.mp4"
        test_file.write_text("data")
        mock_xmp.return_value = None

        with patch(
            "photo_organizer.organize_photos.FILE_TYPE_EXTRACTORS",
            {".mp4": lambda p: "2023:06:15 10:30:00"},
        ):
            result = get_file_creation_date(str(test_file))
        assert result == "2023:06:15 10:30:00"

    @patch("photo_organizer.organize_photos.extract_xmp_date")
    @patch("photo_organizer.organize_photos.extract_exif_via_pillow")
    @patch("photo_organizer.organize_photos.extract_exif_data")
    def test_metadata_preferred_over_filename(
        self, mock_exif, mock_pillow, mock_xmp, tmp_path
    ):
        """Metadata date should be preferred over filename date."""
        test_file = tmp_path / "IMG_20230101_120000.jpg"
        test_file.write_text("data")
        mock_exif.return_value = "2023:06:15 10:30:00"

        result = get_file_creation_date(str(test_file))
        assert result == "2023:06:15 10:30:00"


# ── _cross_reference_dates ───────────────────────────────────────────


class TestCrossReferenceDates:
    def test_matching_dates_no_warning(self, caplog):
        with caplog.at_level(logging.WARNING):
            _cross_reference_dates(
                "photo.jpg",
                "2023:06:15 10:30:00",
                "2023:06:15 10:30:00",
            )
        assert "mismatch" not in caplog.text.lower()

    def test_mismatched_dates_logs_warning(self, caplog):
        with caplog.at_level(logging.WARNING):
            _cross_reference_dates(
                "photo.jpg",
                "2023:06:15 10:30:00",
                "2023:01:01 12:00:00",
            )
        assert "mismatch" in caplog.text.lower()

    def test_invalid_date_format_no_crash(self):
        """Should not crash with unparseable dates."""
        _cross_reference_dates("photo.jpg", "bad date", "also bad")


# ── organize with progress_callback ──────────────────────────────────


@patch("photo_organizer.organize_photos.get_file_creation_date")
def test_organize_with_progress_callback(mock_get_creation_date, setup_dirs):
    """Test that progress callback is called during organization."""
    origin_dir, destination_dir = setup_dirs
    mock_get_creation_date.return_value = "2023:01:01 12:00:00"

    test_file = os.path.join(origin_dir, "test.jpg")
    with open(test_file, "w") as f:
        f.write("dummy data")

    callback = MagicMock()
    organize(origin_dir, destination_dir, progress_callback=callback)

    assert callback.call_count >= 2  # At least "Found X files" + processing


@patch("photo_organizer.organize_photos.get_file_creation_date")
@patch("photo_organizer.organize_photos.move_file_safely")
def test_organize_handles_move_failure(mock_move, mock_get_date, setup_dirs):
    """Test handling when move_file_safely returns False and file still exists."""
    origin_dir, destination_dir = setup_dirs
    mock_get_date.return_value = "2023:01:01 12:00:00"
    mock_move.return_value = False

    test_file = os.path.join(origin_dir, "test.jpg")
    with open(test_file, "w") as f:
        f.write("dummy data")

    with patch("photo_organizer.organize_photos.log_and_handle_error") as mock_error:
        organize(origin_dir, destination_dir)
        mock_error.assert_called_once()


# ── organize with default directories (lines 295-297) ────────────────


@patch("photo_organizer.organize_photos.get_default_pictures_directory")
@patch("photo_organizer.organize_photos.setup_logging")
def test_organize_uses_default_dirs(mock_logging, mock_default_pics, tmp_path):
    """Test that None origin/dest falls back to default pictures dirs."""
    unsorted = tmp_path / "Unsorted"
    unsorted.mkdir()
    mock_default_pics.return_value = str(tmp_path)

    organize(None, None)
    mock_default_pics.assert_called_once()


# ── EXIF read OSError (lines 186-187) ────────────────────────────────


class TestGetFileCreationDateExifError:
    @patch("photo_organizer.organize_photos.extract_xmp_date", return_value=None)
    @patch("photo_organizer.organize_photos.extract_exif_via_pillow", return_value=None)
    @patch("photo_organizer.organize_photos.get_filesystem_date", return_value=None)
    def test_exif_read_oserror_handled(self, mock_fs, mock_pillow, mock_xmp, tmp_path):
        """Test that OSError reading EXIF is caught gracefully."""
        test_file = tmp_path / "bad.jpg"
        test_file.write_text("data")

        with patch(
            "photo_organizer.organize_photos.extract_exif_data",
            side_effect=OSError("cannot read"),
        ):
            with patch("builtins.open", side_effect=OSError("cannot read")):
                result = get_file_creation_date(str(test_file))
        assert result is None


# ── moved_count % 100 log (line 371) ────────────────────────────────


@patch("photo_organizer.organize_photos.get_file_creation_date")
@patch("photo_organizer.organize_photos.move_file_safely", return_value=True)
def test_organize_logs_every_100_moves(mock_move, mock_get_date, setup_dirs):
    """Test that a log message is emitted every 100 successful moves."""
    origin_dir, destination_dir = setup_dirs
    mock_get_date.return_value = "2023:01:01 12:00:00"

    for i in range(100):
        with open(os.path.join(origin_dir, f"file_{i:03d}.jpg"), "w") as f:
            f.write("data")

    with patch("photo_organizer.organize_photos.logger") as mock_logger:
        organize(origin_dir, destination_dir)
        # Check that "Successfully moved 100 files so far" was logged
        info_calls = [str(c) for c in mock_logger.info.call_args_list]
        assert any("100" in c and "moved" in c for c in info_calls)


# ── OSError/PermissionError handler (lines 399-401) ─────────────────


@patch("photo_organizer.organize_photos.get_file_creation_date")
def test_organize_handles_oserror_on_file(mock_get_date, setup_dirs):
    """Test that OSError/PermissionError during processing is caught."""
    origin_dir, destination_dir = setup_dirs
    mock_get_date.side_effect = OSError("disk error")

    test_file = os.path.join(origin_dir, "test.jpg")
    with open(test_file, "w") as f:
        f.write("dummy data")

    # Should not raise
    organize(origin_dir, destination_dir)

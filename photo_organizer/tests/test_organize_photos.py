import logging
import os
import shutil
import tempfile
import time
from unittest.mock import patch

import pytest

from photo_organizer.organize_photos import organize


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

    # Also close photo_organizer logger handlers
    photo_logger = logging.getLogger("photo_organizer")
    for handler in photo_logger.handlers[:]:
        handler.close()
        photo_logger.removeHandler(handler)

    # Use retry logic for Windows file locking issues
    for attempt in range(5):
        try:
            shutil.rmtree(test_dir)
            break
        except PermissionError:
            time.sleep(0.1)
            if attempt == 4:
                raise


@patch("photo_organizer.organize_photos.parse_args")
@patch("photo_organizer.organize_photos.get_file_creation_date")
def test_move_files_to_correct_destination(
    mock_get_creation_date, mock_parse_args, setup_dirs
):
    """Test that files are moved to correct year/month destination folders."""
    origin_dir, destination_dir = setup_dirs
    mock_parse_args.return_value = {
        "origin_dir": origin_dir,
        "destination_dir": destination_dir,
    }
    mock_get_creation_date.return_value = "2023:01:01 12:00:00"

    test_file = os.path.join(origin_dir, "test.mov")
    with open(test_file, "w") as f:
        f.write("dummy data")

    organize()

    expected_dir = os.path.join(destination_dir, "2023", "01")
    expected_file = os.path.join(expected_dir, "test.mov")

    assert os.path.exists(expected_dir)
    assert os.path.exists(expected_file)
    assert not os.path.exists(test_file)


@patch("photo_organizer.organize_photos.parse_args")
def test_remove_empty_directories(mock_parse_args, setup_dirs):
    """Test that empty directories are removed after organization."""
    origin_dir, destination_dir = setup_dirs
    mock_parse_args.return_value = {
        "origin_dir": origin_dir,
        "destination_dir": destination_dir,
    }

    empty_dir = os.path.join(origin_dir, "empty_dir")
    os.makedirs(empty_dir)

    organize()

    assert not os.path.exists(empty_dir)


@patch("photo_organizer.organize_photos.parse_args")
def test_delete_specific_files(mock_parse_args, setup_dirs):
    """Test that specific unwanted files are deleted during organization."""
    origin_dir, destination_dir = setup_dirs
    mock_parse_args.return_value = {
        "origin_dir": origin_dir,
        "destination_dir": destination_dir,
    }

    thumbs_file = os.path.join(origin_dir, "Thumbs.db")
    desktop_file = os.path.join(origin_dir, "desktop")
    with open(thumbs_file, "w") as f:
        f.write("dummy data")
    with open(desktop_file, "w") as f:
        f.write("dummy data")

    organize()

    assert not os.path.exists(thumbs_file)
    assert not os.path.exists(desktop_file)


@patch("photo_organizer.organize_photos.parse_args")
@patch("photo_organizer.organize_photos.extract_exif_data")
@patch("photo_organizer.organize_photos.log_and_handle_error")
def test_handle_files_without_exif_data(
    mock_log_and_handle_error, mock_extract_exif_data, mock_parse_args, setup_dirs
):
    """Test proper error handling for files without EXIF data."""
    origin_dir, destination_dir = setup_dirs
    mock_parse_args.return_value = {
        "origin_dir": origin_dir,
        "destination_dir": destination_dir,
    }
    mock_extract_exif_data.return_value = None

    test_file = os.path.join(origin_dir, "test.jpg")
    with open(test_file, "w") as f:
        f.write("dummy data")

    organize()

    mock_log_and_handle_error.assert_called_once()


@patch("photo_organizer.organize_photos.parse_args")
@patch("photo_organizer.organize_photos.extract_exif_data")
@patch("photo_organizer.organize_photos.log_and_handle_error")
def test_handle_files_with_bad_exif_data(
    mock_log_and_handle_error, mock_extract_exif_data, mock_parse_args, setup_dirs
):
    """Test proper error handling for files with corrupted EXIF data."""
    origin_dir, destination_dir = setup_dirs
    mock_parse_args.return_value = {
        "origin_dir": origin_dir,
        "destination_dir": destination_dir,
    }
    mock_extract_exif_data.side_effect = ValueError("Bad EXIF data")

    test_file = os.path.join(origin_dir, "test.jpg")
    with open(test_file, "w") as f:
        f.write("dummy data")

    organize()

    mock_log_and_handle_error.assert_called_once()


@patch("photo_organizer.organize_photos.parse_args")
@patch("photo_organizer.organize_photos.os.remove")
@patch("photo_organizer.organize_photos.logger.error")
def test_handle_permission_error(
    mock_logger_error, mock_os_remove, mock_parse_args, setup_dirs
):
    """Test proper error handling for file permission errors."""
    origin_dir, destination_dir = setup_dirs
    mock_parse_args.return_value = {
        "origin_dir": origin_dir,
        "destination_dir": destination_dir,
    }
    mock_os_remove.side_effect = PermissionError("Permission denied")

    test_file = os.path.join(origin_dir, "test.jpg")
    with open(test_file, "w") as f:
        f.write("dummy data")

    organize()

    mock_logger_error.assert_called()

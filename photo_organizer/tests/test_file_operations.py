import os
from unittest.mock import patch

import pytest

from photo_organizer.file_operations import (
    FILES_TO_DELETE,
    FileOperationError,
    _get_unique_filename,
    cleanup_empty_directories,
    create_destination_path,
    delete_unwanted_files,
    ensure_directory_exists,
    move_file_safely,
    should_skip_file,
)


# ── create_destination_path ──────────────────────────────────────────


class TestCreateDestinationPath:
    def test_valid_date(self, tmp_path):
        result = create_destination_path("2023:01:15 14:30:00", str(tmp_path))
        assert result == os.path.join(str(tmp_path), "2023", "01")

    def test_december_date(self, tmp_path):
        result = create_destination_path("2023:12:25 08:00:00", str(tmp_path))
        assert result == os.path.join(str(tmp_path), "2023", "12")

    def test_single_digit_month_padded(self, tmp_path):
        result = create_destination_path("2023:03:01 12:00:00", str(tmp_path))
        assert result == os.path.join(str(tmp_path), "2023", "03")

    def test_invalid_date_returns_unknown(self, tmp_path):
        result = create_destination_path("not a date", str(tmp_path))
        assert result == os.path.join(str(tmp_path), "Unknown")

    def test_empty_date_returns_unknown(self, tmp_path):
        result = create_destination_path("", str(tmp_path))
        assert result == os.path.join(str(tmp_path), "Unknown")


# ── ensure_directory_exists ──────────────────────────────────────────


class TestEnsureDirectoryExists:
    def test_creates_new_directory(self, tmp_path):
        new_dir = str(tmp_path / "new" / "nested" / "dir")
        ensure_directory_exists(new_dir)
        assert os.path.isdir(new_dir)

    def test_existing_directory_no_error(self, tmp_path):
        ensure_directory_exists(str(tmp_path))

    def test_unwritable_path_raises(self):
        with pytest.raises(FileOperationError):
            ensure_directory_exists("/proc/fake/impossible/dir")


# ── move_file_safely ─────────────────────────────────────────────────


class TestMoveFileSafely:
    def test_moves_file_successfully(self, tmp_path):
        src = tmp_path / "source" / "test.jpg"
        src.parent.mkdir()
        src.write_text("data")
        dest_dir = str(tmp_path / "dest")

        result = move_file_safely(str(src), dest_dir, "test.jpg")

        assert result is True
        assert os.path.exists(os.path.join(dest_dir, "test.jpg"))
        assert not src.exists()

    def test_handles_duplicate_filename(self, tmp_path):
        src = tmp_path / "source" / "test.jpg"
        src.parent.mkdir()
        src.write_text("new data")

        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        (dest_dir / "test.jpg").write_text("existing data")

        result = move_file_safely(str(src), str(dest_dir), "test.jpg")

        assert result is True
        assert os.path.exists(os.path.join(str(dest_dir), "test_1.jpg"))

    def test_returns_false_on_error(self, tmp_path):
        result = move_file_safely("/nonexistent/source.jpg", str(tmp_path), "src.jpg")
        assert result is False


# ── _get_unique_filename ─────────────────────────────────────────────


class TestGetUniqueFilename:
    def test_no_conflict(self, tmp_path):
        path = str(tmp_path / "photo.jpg")
        # File doesn't exist, so it should return the same path
        result = _get_unique_filename(path)
        assert result == path

    def test_single_conflict(self, tmp_path):
        existing = tmp_path / "photo.jpg"
        existing.write_text("data")

        result = _get_unique_filename(str(existing))
        assert result == str(tmp_path / "photo_1.jpg")

    def test_multiple_conflicts(self, tmp_path):
        (tmp_path / "photo.jpg").write_text("data")
        (tmp_path / "photo_1.jpg").write_text("data")
        (tmp_path / "photo_2.jpg").write_text("data")

        result = _get_unique_filename(str(tmp_path / "photo.jpg"))
        assert result == str(tmp_path / "photo_3.jpg")


# ── cleanup_empty_directories ────────────────────────────────────────


class TestCleanupEmptyDirectories:
    def test_removes_empty_dirs(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()

        count = cleanup_empty_directories(str(tmp_path))
        assert count >= 1
        assert not empty.exists()

    def test_preserves_non_empty_dirs(self, tmp_path):
        non_empty = tmp_path / "non_empty"
        non_empty.mkdir()
        (non_empty / "file.txt").write_text("data")

        count = cleanup_empty_directories(str(tmp_path))
        assert non_empty.exists()

    def test_handles_nested_empty_dirs(self, tmp_path):
        nested = tmp_path / "a" / "b" / "c"
        nested.mkdir(parents=True)

        count = cleanup_empty_directories(str(tmp_path))
        assert count >= 1

    def test_nonexistent_dir_returns_zero(self):
        count = cleanup_empty_directories("/nonexistent/path")
        assert count == 0


# ── should_skip_file ─────────────────────────────────────────────────


class TestShouldSkipFile:
    def test_thumbs_db_skipped(self):
        assert should_skip_file("Thumbs.db") is True

    def test_desktop_skipped(self):
        assert should_skip_file("desktop") is True

    def test_case_insensitive(self):
        assert should_skip_file("THUMBS.DB") is True

    def test_normal_file_not_skipped(self):
        assert should_skip_file("photo.jpg") is False

    def test_custom_patterns(self):
        assert should_skip_file("custom.tmp", {"custom.tmp"}) is True
        assert should_skip_file("photo.jpg", {"custom.tmp"}) is False


# ── delete_unwanted_files ────────────────────────────────────────────


class TestDeleteUnwantedFiles:
    def test_deletes_matching_files(self, tmp_path):
        (tmp_path / "Thumbs.db").write_text("data")
        (tmp_path / "desktop").write_text("data")
        (tmp_path / "photo.jpg").write_text("data")

        count = delete_unwanted_files(str(tmp_path), FILES_TO_DELETE)

        assert count == 2
        assert not (tmp_path / "Thumbs.db").exists()
        assert not (tmp_path / "desktop").exists()
        assert (tmp_path / "photo.jpg").exists()

    def test_no_matches_returns_zero(self, tmp_path):
        (tmp_path / "photo.jpg").write_text("data")

        count = delete_unwanted_files(str(tmp_path), FILES_TO_DELETE)
        assert count == 0

    def test_empty_directory(self, tmp_path):
        count = delete_unwanted_files(str(tmp_path), FILES_TO_DELETE)
        assert count == 0

    def test_nonexistent_directory(self):
        count = delete_unwanted_files("/nonexistent/path", FILES_TO_DELETE)
        assert count == 0

    def test_delete_permission_error(self, tmp_path):
        """Test that OSError on individual file delete is handled."""
        (tmp_path / "Thumbs.db").write_text("data")

        with patch(
            "photo_organizer.file_operations.os.remove", side_effect=OSError("perm")
        ):
            count = delete_unwanted_files(str(tmp_path), FILES_TO_DELETE)
        assert count == 0


class TestCleanupEmptyDirectoriesErrors:
    def test_rmdir_permission_error(self, tmp_path):
        """Test OSError on rmdir is handled gracefully."""
        empty = tmp_path / "empty"
        empty.mkdir()

        with patch(
            "photo_organizer.file_operations.os.rmdir", side_effect=OSError("perm")
        ):
            count = cleanup_empty_directories(str(tmp_path))
        assert count == 0

    def test_walk_oserror(self):
        """Test outer OSError on os.walk is handled (lines 138-142)."""
        with patch(
            "photo_organizer.file_operations.os.walk", side_effect=OSError("fail")
        ):
            count = cleanup_empty_directories("/some/path")
        assert count == 0


class TestDeleteUnwantedFilesWalkError:
    def test_walk_oserror(self):
        """Test outer OSError on os.walk is handled (lines 186-190)."""
        with patch(
            "photo_organizer.file_operations.os.walk", side_effect=OSError("fail")
        ):
            count = delete_unwanted_files("/some/path", FILES_TO_DELETE)
        assert count == 0

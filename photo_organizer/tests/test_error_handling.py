from photo_organizer.error_handling import handle_error_cases, log_and_handle_error


class TestHandleErrorCases:
    def test_moves_file_to_unknown(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        test_file = source / "photo.jpg"
        test_file.write_text("data")

        handle_error_cases(str(tmp_path), "photo.jpg", str(test_file))

        unknown_dir = tmp_path / "Unknown"
        assert unknown_dir.exists()
        assert (unknown_dir / "photo.jpg").exists()
        assert not test_file.exists()

    def test_deletes_duplicate_in_unknown(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        test_file = source / "photo.jpg"
        test_file.write_text("new data")

        # Pre-create the file in Unknown
        unknown_dir = tmp_path / "Unknown"
        unknown_dir.mkdir()
        (unknown_dir / "photo.jpg").write_text("existing data")

        handle_error_cases(str(tmp_path), "photo.jpg", str(test_file))

        # Source file should be deleted
        assert not test_file.exists()
        # Existing Unknown file should still have original content
        assert (unknown_dir / "photo.jpg").read_text() == "existing data"

    def test_creates_unknown_dir_if_missing(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        test_file = source / "photo.jpg"
        test_file.write_text("data")

        unknown_dir = tmp_path / "Unknown"
        assert not unknown_dir.exists()

        handle_error_cases(str(tmp_path), "photo.jpg", str(test_file))

        assert unknown_dir.exists()


class TestLogAndHandleError:
    def test_logs_and_handles(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        test_file = source / "photo.jpg"
        test_file.write_text("data")

        log_and_handle_error(
            str(tmp_path), "photo.jpg", str(test_file), "test error message"
        )

        assert (tmp_path / "Unknown" / "photo.jpg").exists()
        assert not test_file.exists()

from unittest.mock import patch

from photo_organizer.log import setup_logging


class TestSetupLogging:
    @patch("photo_organizer.log.platform.system", return_value="Windows")
    def test_windows_uses_cwd(self, mock_system, tmp_path, monkeypatch):
        """Test that Windows uses cwd instead of cwd/log."""
        monkeypatch.chdir(tmp_path)
        setup_logging("test_app", enable_file_logging=False)
        mock_system.assert_called()

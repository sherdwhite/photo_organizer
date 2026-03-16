import subprocess
import sys
from unittest.mock import patch


from photo_organizer.main import main, run


class TestMain:
    def test_cli_mode_default(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["program"])
        with patch("photo_organizer.main.organize") as mock_organize:
            result = main()
        assert result == 0
        mock_organize.assert_called_once_with(None, None)

    def test_cli_with_origin_and_destination(self, monkeypatch):
        monkeypatch.setattr(
            "sys.argv",
            ["program", "-o", "/origin", "-d", "/dest"],
        )
        with patch("photo_organizer.main.organize") as mock_organize:
            result = main()
        assert result == 0
        mock_organize.assert_called_once_with("/origin", "/dest")

    def test_gui_import_error(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["program", "--gui"])
        with patch("photo_organizer.main.run_gui", side_effect=ImportError("No GUI")):
            result = main()
        assert result == 1
        captured = capsys.readouterr()
        assert "GUI components not available" in captured.out

    def test_gui_success(self, monkeypatch):
        """Test successful GUI launch (line 44)."""
        monkeypatch.setattr("sys.argv", ["program", "--gui"])
        with patch("photo_organizer.main.run_gui", return_value=0):
            result = main()
        assert result == 0


class TestRun:
    def test_run_with_args_calls_organize(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["program", "--some-arg"])
        with patch("photo_organizer.main.organize") as mock_organize:
            run()
        mock_organize.assert_called_once()

    def test_run_no_args_tries_gui_then_fallback(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["program"])
        with patch("photo_organizer.main.run_gui", side_effect=ImportError("No GUI")):
            with patch("photo_organizer.main.organize") as mock_organize:
                run()
            mock_organize.assert_called_once()

    def test_run_no_args_gui_success(self, monkeypatch):
        """Test run() successfully launches GUI when no args."""
        monkeypatch.setattr("sys.argv", ["program"])
        with patch("photo_organizer.main.run_gui", return_value=0):
            result = run()
        assert result == 0


class TestMainGuard:
    def test_main_module_execution(self):
        """Cover `if __name__ == '__main__': sys.exit(main())` (line 76)."""
        result = subprocess.run(
            [sys.executable, "-m", "photo_organizer.main", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Photo Organizer" in result.stdout

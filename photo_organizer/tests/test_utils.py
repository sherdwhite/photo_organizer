import os
from unittest.mock import patch

from photo_organizer.utils import get_default_pictures_directory, parse_args


def test_get_default_pictures_directory():
    """Test that get_default_pictures_directory returns a valid path."""
    pictures_dir = get_default_pictures_directory()
    assert isinstance(pictures_dir, str)
    assert len(pictures_dir) > 0


def test_parse_args_defaults(monkeypatch):
    """Test that parse_args uses the default Pictures directory structure."""
    monkeypatch.setattr("sys.argv", ["program_name"])

    # Mock the default pictures directory to make test predictable
    with patch("photo_organizer.utils.get_default_pictures_directory") as mock_pictures:
        mock_pictures.return_value = "/home/user/Pictures"
        args = parse_args()

        expected_origin = os.path.join("/home/user/Pictures", "Unsorted")
        expected_destination = os.path.join("/home/user/Pictures", "Organized")

        assert args["origin_dir"] == expected_origin
        assert args["destination_dir"] == expected_destination


def test_parse_args_custom_origin(monkeypatch):
    """Test parse_args with custom origin directory."""
    monkeypatch.setattr("sys.argv", ["program_name", "--origin", "/custom/origin"])

    with patch("photo_organizer.utils.get_default_pictures_directory") as mock_pictures:
        mock_pictures.return_value = "/home/user/Pictures"
        args = parse_args()

        expected_destination = os.path.join("/home/user/Pictures", "Organized")

        assert args["origin_dir"] == "/custom/origin"
        assert args["destination_dir"] == expected_destination


def test_parse_args_custom_destination(monkeypatch):
    """Test parse_args with custom destination directory."""
    monkeypatch.setattr(
        "sys.argv", ["program_name", "--destination", "/custom/destination"]
    )

    with patch("photo_organizer.utils.get_default_pictures_directory") as mock_pictures:
        mock_pictures.return_value = "/home/user/Pictures"
        args = parse_args()

        expected_origin = os.path.join("/home/user/Pictures", "Unsorted")

        assert args["origin_dir"] == expected_origin
        assert args["destination_dir"] == "/custom/destination"


def test_parse_args_custom_both(monkeypatch):
    """Test parse_args with both custom origin and destination directories."""
    monkeypatch.setattr(
        "sys.argv",
        [
            "program_name",
            "--origin",
            "/custom/origin",
            "--destination",
            "/custom/destination",
        ],
    )
    args = parse_args()
    assert args["origin_dir"] == "/custom/origin"
    assert args["destination_dir"] == "/custom/destination"

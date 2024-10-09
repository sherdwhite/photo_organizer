from photo_organizer.utils import parse_args


def test_parse_args_defaults(monkeypatch):
    monkeypatch.setattr("sys.argv", ["program_name"])
    args = parse_args()
    assert args["origin_dir"] == r"C:/Users/sherd/Documents/Unsorted_Pics"
    assert args["destination_dir"] == r"C:/Users/sherd/Documents/Sorted_Pics"


def test_parse_args_custom_origin(monkeypatch):
    monkeypatch.setattr("sys.argv", ["program_name", "--origin", "/custom/origin"])
    args = parse_args()
    assert args["origin_dir"] == "/custom/origin"
    assert args["destination_dir"] == r"C:/Users/sherd/Documents/Sorted_Pics"


def test_parse_args_custom_destination(monkeypatch):
    monkeypatch.setattr(
        "sys.argv", ["program_name", "--destination", "/custom/destination"]
    )
    args = parse_args()
    assert args["origin_dir"] == r"C:/Users/sherd/Documents/Unsorted_Pics"
    assert args["destination_dir"] == "/custom/destination"


def test_parse_args_custom_both(monkeypatch):
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

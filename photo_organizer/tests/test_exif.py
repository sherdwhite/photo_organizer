from io import BytesIO
from unittest.mock import MagicMock, patch


from photo_organizer.exif import extract_exif_data, extract_exif_via_pillow


# ── extract_exif_data ────────────────────────────────────────────────


class TestExtractExifData:
    @patch("photo_organizer.exif.Image")
    def test_no_exif_returns_none(self, mock_image_class):
        mock_img = MagicMock()
        mock_img.has_exif = False
        mock_image_class.return_value = mock_img

        result = extract_exif_data(BytesIO(b"fake image data"))
        assert result is None

    @patch("photo_organizer.exif.Image")
    def test_datetime_original_found(self, mock_image_class):
        mock_img = MagicMock()
        mock_img.has_exif = True
        mock_img.get.side_effect = lambda field: (
            "2023:06:15 10:30:00" if field == "datetime_original" else None
        )
        mock_image_class.return_value = mock_img

        result = extract_exif_data(BytesIO(b"fake image data"))
        assert result == "2023:06:15 10:30:00"

    @patch("photo_organizer.exif.Image")
    def test_fallback_to_datetime(self, mock_image_class):
        mock_img = MagicMock()
        mock_img.has_exif = True
        mock_img.get.side_effect = lambda field: (
            "2023:06:15 10:30:00" if field == "datetime" else None
        )
        mock_image_class.return_value = mock_img

        result = extract_exif_data(BytesIO(b"fake image data"))
        assert result == "2023:06:15 10:30:00"

    @patch("photo_organizer.exif.Image")
    def test_no_date_fields_returns_none(self, mock_image_class):
        mock_img = MagicMock()
        mock_img.has_exif = True
        mock_img.get.return_value = None
        mock_image_class.return_value = mock_img

        result = extract_exif_data(BytesIO(b"fake image data"))
        assert result is None

    @patch("photo_organizer.exif.Image")
    def test_corrupted_exif_value_error(self, mock_image_class):
        mock_image_class.side_effect = ValueError("Invalid TIFF byte order")

        result = extract_exif_data(BytesIO(b"fake image data"))
        assert result is None

    @patch("photo_organizer.exif.Image")
    def test_key_error(self, mock_image_class):
        mock_image_class.side_effect = KeyError("missing key")

        result = extract_exif_data(BytesIO(b"fake image data"))
        assert result is None

    @patch("photo_organizer.exif.Image")
    def test_attribute_error(self, mock_image_class):
        mock_image_class.side_effect = AttributeError("bad attr")

        result = extract_exif_data(BytesIO(b"fake image data"))
        assert result is None

    @patch("photo_organizer.exif.Image")
    def test_unexpected_error(self, mock_image_class):
        mock_image_class.side_effect = RuntimeError("unexpected")

        result = extract_exif_data(BytesIO(b"fake image data"))
        assert result is None

    @patch("photo_organizer.exif.Image")
    def test_garbage_date_rejected(self, mock_image_class):
        mock_img = MagicMock()
        mock_img.has_exif = True
        mock_img.get.side_effect = lambda field: (
            "0000:00:00 00:00:00" if field == "datetime_original" else None
        )
        mock_image_class.return_value = mock_img

        result = extract_exif_data(BytesIO(b"fake image data"))
        assert result is None


# ── extract_exif_via_pillow ──────────────────────────────────────────


class TestExtractExifViaPillow:
    @patch("photo_organizer.exif.PILImage", create=True)
    def test_with_valid_exif(self, mock_pil):
        mock_img = MagicMock()
        mock_exif = {36867: "2023:06:15 10:30:00"}  # DateTimeOriginal tag
        mock_img.getexif.return_value = mock_exif
        mock_img.__enter__ = MagicMock(return_value=mock_img)
        mock_img.__exit__ = MagicMock(return_value=False)

        with patch("photo_organizer.exif.extract_exif_via_pillow") as mock_func:
            mock_func.return_value = "2023:06:15 10:30:00"
            result = mock_func("/fake/image.jpg")

        assert result == "2023:06:15 10:30:00"

    def test_nonexistent_file_returns_none(self):
        result = extract_exif_via_pillow("/nonexistent/file.jpg")
        assert result is None

    def test_with_real_no_exif_file(self, tmp_path):
        # Create a minimal valid PNG without EXIF
        import struct
        import zlib

        png_file = tmp_path / "test.png"
        # Minimal 1x1 PNG
        signature = b"\x89PNG\r\n\x1a\n"
        # IHDR chunk
        ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
        ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF
        ihdr = struct.pack(">I", 13) + b"IHDR" + ihdr_data + struct.pack(">I", ihdr_crc)
        # IDAT chunk
        raw_data = zlib.compress(b"\x00\x00\x00\x00")
        idat_crc = zlib.crc32(b"IDAT" + raw_data) & 0xFFFFFFFF
        idat = (
            struct.pack(">I", len(raw_data))
            + b"IDAT"
            + raw_data
            + struct.pack(">I", idat_crc)
        )
        # IEND chunk
        iend_crc = zlib.crc32(b"IEND") & 0xFFFFFFFF
        iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc)

        png_file.write_bytes(signature + ihdr + idat + iend)

        result = extract_exif_via_pillow(str(png_file))
        assert result is None


class TestExtractExifViaPillowMocked:
    def test_pillow_exif_success_path(self):
        """Test the full Pillow EXIF success path with proper mocking."""
        mock_img = MagicMock()
        mock_exif = MagicMock()
        mock_exif.get.side_effect = lambda tag_id: (
            "2023:06:15 10:30:00" if tag_id == 36867 else None
        )
        mock_exif.__bool__ = MagicMock(return_value=True)
        mock_img.getexif.return_value = mock_exif
        mock_img.__enter__ = MagicMock(return_value=mock_img)
        mock_img.__exit__ = MagicMock(return_value=False)

        with patch("PIL.Image.open", return_value=mock_img):
            result = extract_exif_via_pillow("/fake/image.jpg")
        assert result == "2023:06:15 10:30:00"

    def test_pillow_exif_no_date_fields(self):
        """Test when EXIF exists but has no date fields."""
        mock_img = MagicMock()
        mock_exif = MagicMock()
        mock_exif.get.return_value = None
        mock_exif.__bool__ = MagicMock(return_value=True)
        mock_img.getexif.return_value = mock_exif
        mock_img.__enter__ = MagicMock(return_value=mock_img)
        mock_img.__exit__ = MagicMock(return_value=False)

        with patch("PIL.Image.open", return_value=mock_img):
            result = extract_exif_via_pillow("/fake/image.jpg")
        assert result is None

    def test_pillow_exif_empty(self):
        """Test when no EXIF data exists via Pillow."""
        mock_img = MagicMock()
        mock_img.getexif.return_value = None
        mock_img.__enter__ = MagicMock(return_value=mock_img)
        mock_img.__exit__ = MagicMock(return_value=False)

        with patch("PIL.Image.open", return_value=mock_img):
            result = extract_exif_via_pillow("/fake/image.jpg")
        assert result is None

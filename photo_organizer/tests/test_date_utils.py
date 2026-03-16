import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from photo_organizer.date_utils import (
    GARBAGE_DATE_PATTERNS,
    _parse_date_flexible,
    extract_xmp_date,
    get_filesystem_date,
    validate_date,
)


# ── validate_date ────────────────────────────────────────────────────


class TestValidateDate:
    def test_none_returns_none(self):
        assert validate_date(None) is None

    def test_empty_string_returns_none(self):
        assert validate_date("") is None

    def test_whitespace_only_returns_none(self):
        assert validate_date("   ") is None

    @pytest.mark.parametrize("garbage", GARBAGE_DATE_PATTERNS)
    def test_garbage_patterns_rejected(self, garbage):
        assert validate_date(garbage) is None

    def test_garbage_pattern_prefix_rejected(self):
        assert validate_date("0000:00:00 some extra text") is None

    def test_pre_digital_date_rejected(self):
        assert validate_date("1985:06:15 10:30:00") is None

    def test_future_date_rejected(self):
        future = datetime.now() + timedelta(days=30)
        future_str = future.strftime("%Y:%m:%d %H:%M:%S")
        assert validate_date(future_str) is None

    def test_valid_exif_date(self):
        result = validate_date("2023:01:15 14:30:00")
        assert result == "2023:01:15 14:30:00"

    def test_valid_iso_date(self):
        result = validate_date("2023-01-15 14:30:00")
        assert result == "2023:01:15 14:30:00"

    def test_valid_iso8601_date(self):
        result = validate_date("2023-01-15T14:30:00")
        assert result == "2023:01:15 14:30:00"

    def test_valid_date_with_whitespace(self):
        result = validate_date("  2023:01:15 14:30:00  ")
        assert result == "2023:01:15 14:30:00"

    def test_unparseable_date_returns_none(self):
        assert validate_date("not a date at all") is None

    def test_boundary_year_1990_accepted(self):
        result = validate_date("1990:06:15 12:00:00")
        assert result == "1990:06:15 12:00:00"

    def test_date_just_before_1990_rejected(self):
        assert validate_date("1989:12:31 23:59:59") is None

    def test_date_within_one_day_grace_accepted(self):
        """Dates up to 1 day in the future should be accepted (timezone grace)."""
        near_future = datetime.now() + timedelta(hours=12)
        future_str = near_future.strftime("%Y:%m:%d %H:%M:%S")
        result = validate_date(future_str)
        assert result is not None


# ── _parse_date_flexible ─────────────────────────────────────────────


class TestParseDateFlexible:
    def test_exif_standard_format(self):
        dt = _parse_date_flexible("2023:01:15 14:30:00")
        assert dt == datetime(2023, 1, 15, 14, 30, 0)

    def test_iso_format(self):
        dt = _parse_date_flexible("2023-01-15 14:30:00")
        assert dt == datetime(2023, 1, 15, 14, 30, 0)

    def test_iso8601_format(self):
        dt = _parse_date_flexible("2023-01-15T14:30:00")
        assert dt == datetime(2023, 1, 15, 14, 30, 0)

    def test_iso8601_with_timezone(self):
        dt = _parse_date_flexible("2023-01-15T14:30:00+05:30")
        assert dt is not None
        assert dt.tzinfo is None  # Should be converted to naive

    def test_iso8601_with_fractional_seconds(self):
        dt = _parse_date_flexible("2023-01-15T14:30:00.123456")
        assert dt is not None
        assert dt.year == 2023

    def test_date_only_iso(self):
        dt = _parse_date_flexible("2023-01-15")
        assert dt == datetime(2023, 1, 15)

    def test_date_only_exif(self):
        dt = _parse_date_flexible("2023:01:15")
        assert dt == datetime(2023, 1, 15)

    def test_trailing_z_stripped(self):
        dt = _parse_date_flexible("2023-01-15T14:30:00Z")
        assert dt is not None
        assert dt.year == 2023

    def test_trailing_timezone_offset_stripped(self):
        dt = _parse_date_flexible("2023-01-15T14:30:00+00:00")
        assert dt is not None

    def test_space_separated_with_tz_offset_stripped(self):
        """Hits the fallback timezone-strip path (line 123)."""
        dt = _parse_date_flexible("2023-01-15 14:30:00+05:30")
        assert dt is not None
        assert dt.year == 2023

    def test_completely_invalid_returns_none(self):
        assert _parse_date_flexible("not-a-date") is None

    def test_whitespace_handling(self):
        dt = _parse_date_flexible("  2023:01:15 14:30:00  ")
        assert dt is not None


# ── extract_xmp_date ─────────────────────────────────────────────────


class TestExtractXmpDate:
    def test_no_xmp_data_returns_none(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"no xmp data here")
            f.flush()
            result = extract_xmp_date(f.name)
        os.unlink(f.name)
        assert result is None

    def test_xmp_with_create_date(self):
        xmp_data = (
            b"<x:xmpmeta>"
            b"<xmp:CreateDate>2023-06-15T10:30:00</xmp:CreateDate>"
            b"</x:xmpmeta>"
        )
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(xmp_data)
            f.flush()
            result = extract_xmp_date(f.name)
        os.unlink(f.name)
        assert result == "2023:06:15 10:30:00"

    def test_xmp_with_datetime_original(self):
        xmp_data = (
            b"<x:xmpmeta>"
            b"<exif:DateTimeOriginal>2023-06-15T10:30:00</exif:DateTimeOriginal>"
            b"</x:xmpmeta>"
        )
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(xmp_data)
            f.flush()
            result = extract_xmp_date(f.name)
        os.unlink(f.name)
        assert result == "2023:06:15 10:30:00"

    def test_xmp_with_photoshop_date(self):
        xmp_data = (
            b"<x:xmpmeta>"
            b"<photoshop:DateCreated>2023-06-15T10:30:00</photoshop:DateCreated>"
            b"</x:xmpmeta>"
        )
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(xmp_data)
            f.flush()
            result = extract_xmp_date(f.name)
        os.unlink(f.name)
        assert result == "2023:06:15 10:30:00"

    def test_xmp_with_modify_date(self):
        xmp_data = (
            b"<x:xmpmeta>"
            b"<xmp:ModifyDate>2023-06-15T10:30:00</xmp:ModifyDate>"
            b"</x:xmpmeta>"
        )
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(xmp_data)
            f.flush()
            result = extract_xmp_date(f.name)
        os.unlink(f.name)
        assert result == "2023:06:15 10:30:00"

    def test_xmp_with_rdf_tags(self):
        xmp_data = (
            b"<rdf:RDF>"
            b"<xmp:CreateDate>2023-06-15T10:30:00</xmp:CreateDate>"
            b"</rdf:RDF>"
        )
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(xmp_data)
            f.flush()
            result = extract_xmp_date(f.name)
        os.unlink(f.name)
        assert result == "2023:06:15 10:30:00"

    def test_nonexistent_file_returns_none(self):
        result = extract_xmp_date("/nonexistent/file.jpg")
        assert result is None

    def test_xmp_with_invalid_date_returns_none(self):
        xmp_data = (
            b"<x:xmpmeta>"
            b"<xmp:CreateDate>0000-00-00T00:00:00</xmp:CreateDate>"
            b"</x:xmpmeta>"
        )
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(xmp_data)
            f.flush()
            result = extract_xmp_date(f.name)
        os.unlink(f.name)
        assert result is None


# ── get_filesystem_date ──────────────────────────────────────────────


class TestGetFilesystemDate:
    def test_returns_date_for_existing_file(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"test data")
            f.flush()
            result = get_filesystem_date(f.name)
        os.unlink(f.name)
        assert result is not None
        # Should be in EXIF date format
        datetime.strptime(result, "%Y:%m:%d %H:%M:%S")

    def test_nonexistent_file_returns_none(self):
        result = get_filesystem_date("/nonexistent/file.jpg")
        assert result is None

    def test_uses_mtime_when_no_birthtime(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"test data")
            f.flush()
            result = get_filesystem_date(f.name)
        os.unlink(f.name)
        # Should still return a date from mtime
        assert result is not None

    def test_uses_birthtime_when_available(self):
        """Test birthtime preference when st_birthtime exists."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"test data")
            f.flush()
            mock_stat = os.stat(f.name)

            class FakeStat:
                st_birthtime = mock_stat.st_mtime
                st_mtime = mock_stat.st_mtime

            with patch("photo_organizer.date_utils.os.stat", return_value=FakeStat()):
                result = get_filesystem_date(f.name)
        os.unlink(f.name)
        assert result is not None


class TestXmpEdgeCases:
    def test_xmp_without_closing_tag(self):
        """XMP data without closing tag should use chunk fallback."""
        xmp_data = (
            b"<x:xmpmeta>"
            b"<xmp:CreateDate>2023-06-15T10:30:00</xmp:CreateDate>"
            # No closing </x:xmpmeta>
        )
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(xmp_data)
            f.flush()
            result = extract_xmp_date(f.name)
        os.unlink(f.name)
        assert result == "2023:06:15 10:30:00"

    def test_xmp_generic_exception(self):
        """Generic exception should be caught."""
        with patch("builtins.open", side_effect=RuntimeError("unexpected")):
            result = extract_xmp_date("/fake/file.jpg")
        assert result is None

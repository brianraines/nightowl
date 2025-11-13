"""Tests for CSV storage functionality."""

import csv
import tempfile
from pathlib import Path
import pytest

from nightowl.storage import SleepDataStorage


class TestSleepDataStorage:
    """Test cases for SleepDataStorage."""

    def test_init_creates_directory(self):
        """Test that storage creates parent directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "subdir" / "sleep.csv"
            storage = SleepDataStorage(csv_path=str(csv_path))
            assert csv_path.parent.exists()

    def test_save_new_file(self):
        """Test saving to a new CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "sleep.csv"
            storage = SleepDataStorage(csv_path=str(csv_path))

            sleep_data = [
                {
                    "day": "2024-01-01",
                    "score": 85,
                    "total_sleep_duration": 28800,
                    "contributors": {"total": 90},
                }
            ]

            saved = storage.save(sleep_data, append=False)
            assert saved == 1
            assert csv_path.exists()

            # Verify content
            with open(csv_path, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]["date"] == "2024-01-01"

    def test_save_append_no_duplicates(self):
        """Test that appending avoids duplicates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "sleep.csv"
            storage = SleepDataStorage(csv_path=str(csv_path))

            sleep_data = [
                {"day": "2024-01-01", "score": 85},
                {"day": "2024-01-02", "score": 90},
            ]

            # First save
            saved1 = storage.save(sleep_data, append=False)
            assert saved1 == 2

            # Try to save same data again
            saved2 = storage.save(sleep_data, append=True)
            assert saved2 == 0

            # Add new data
            new_data = [{"day": "2024-01-03", "score": 88}]
            saved3 = storage.save(new_data, append=True)
            assert saved3 == 1

            # Verify total rows
            with open(csv_path, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 3

    def test_save_empty_data(self):
        """Test saving empty data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "sleep.csv"
            storage = SleepDataStorage(csv_path=str(csv_path))

            saved = storage.save([], append=False)
            assert saved == 0
            assert not csv_path.exists()

    def test_flatten_sleep_record(self):
        """Test flattening of nested sleep records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "sleep.csv"
            storage = SleepDataStorage(csv_path=str(csv_path))

            record = {
                "day": "2024-01-01",
                "score": 85,
                "total_sleep_duration": 28800,
                "contributors": {"total": 90, "efficiency": 95},
                "sleep_phase_5_min": [1, 2, 3],
            }

            flattened = storage._flatten_sleep_record(record)
            assert flattened["date"] == "2024-01-01"
            assert flattened["score"] == 85
            assert flattened["contributor_total"] == 90
            assert flattened["contributor_efficiency"] == 95
            assert flattened["phases_count"] == 3

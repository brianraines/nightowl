"""CSV storage for Oura data persistence."""

import csv
import os
from pathlib import Path
from typing import List, Dict, Set, Optional
import logging

logger = logging.getLogger(__name__)


class OuraDataStorage:
    """Manages CSV storage for Oura data."""

    def __init__(self, base_dir: str = "exports/data"):
        """
        Initialize the storage handler.

        Args:
            base_dir: Base directory for storing CSV files.
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_csv_path(self, data_type: str) -> Path:
        """Get CSV path for a data type."""
        return self.base_dir / f"{data_type}_data.csv"

    def _get_existing_dates(self, csv_path: Path, date_field: str = "date") -> Set[str]:
        """
        Read existing CSV and return set of dates already stored.

        Args:
            csv_path: Path to CSV file.
            date_field: Name of the date field in the CSV.

        Returns:
            Set of date strings (YYYY-MM-DD format).
        """
        if not csv_path.exists():
            return set()

        existing_dates = set()
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if date_field in reader.fieldnames:
                    for row in reader:
                        if date_field in row and row[date_field]:
                            existing_dates.add(row[date_field])
        except Exception as e:
            logger.warning(f"Error reading existing CSV {csv_path}: {e}")
        return existing_dates

    def _get_existing_timestamps(self, csv_path: Path, timestamp_field: str = "timestamp") -> Set[str]:
        """
        Read existing CSV and return set of timestamps already stored.
        Used for time-series data like heartrate where multiple records per day exist.

        Args:
            csv_path: Path to CSV file.
            timestamp_field: Name of the timestamp field in the CSV.

        Returns:
            Set of timestamp strings.
        """
        if not csv_path.exists():
            return set()

        existing_timestamps = set()
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if timestamp_field in reader.fieldnames:
                    for row in reader:
                        if timestamp_field in row and row[timestamp_field]:
                            existing_timestamps.add(row[timestamp_field])
        except Exception as e:
            logger.warning(f"Error reading existing CSV {csv_path}: {e}")
        return existing_timestamps

    def _is_nap(self, record: Dict) -> bool:
        """
        Determine if a sleep record is a nap.

        Naps are typically shorter than regular sleep. Using 3 hours (10800 seconds)
        as the threshold - sleep sessions shorter than this are considered naps.

        Args:
            record: Sleep record from Oura API.

        Returns:
            True if the record is a nap, False otherwise.
        """
        total_sleep = record.get("total_sleep_duration", 0)
        # 3 hours = 10800 seconds
        # Sleep sessions shorter than 3 hours are considered naps
        return total_sleep > 0 and total_sleep < 10800

    def _flatten_record(self, record: Dict, data_type: str) -> Dict:
        """
        Flatten a nested record into a flat dictionary.

        Args:
            record: Record from Oura API.
            data_type: Type of data (sleep, heartrate, activity, etc.).

        Returns:
            Flattened dictionary suitable for CSV storage.
        """
        flattened = {}

        # Extract date field (varies by data type)
        date_fields = {
            "sleep": "day",
            "heartrate": "day",
            "activity": "day",
            "readiness": "day",
            "session": "day",
            "workout": "day",
            "tag": "day",
        }
        date_field = date_fields.get(data_type, "day")
        flattened["date"] = record.get(date_field) or record.get("timestamp", "").split("T")[0]

        # For sleep data, also extract bedtime_start timestamp for duplicate detection
        if data_type == "sleep" and "bedtime_start" in record:
            flattened["bedtime_start"] = record["bedtime_start"]

        # Special handling for sleep data (nap detection)
        if data_type == "sleep":
            flattened["is_nap"] = 1 if self._is_nap(record) else 0

        # Flatten all top-level fields
        for key, value in record.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                flattened[key] = value
            elif isinstance(value, dict):
                # Flatten nested dictionaries with prefix
                for nested_key, nested_value in value.items():
                    if isinstance(nested_value, (str, int, float, bool)) or nested_value is None:
                        flattened[f"{key}_{nested_key}"] = nested_value
            elif isinstance(value, list):
                # For lists, store count or first few items
                if len(value) > 0:
                    flattened[f"{key}_count"] = len(value)
                    # Store first item if it's a simple value
                    if isinstance(value[0], (str, int, float, bool)):
                        flattened[f"{key}_first"] = value[0]

        return flattened

    def save(
        self,
        data: List[Dict],
        data_type: str,
        append: bool = True,
        date_field: str = "date",
    ) -> int:
        """
        Save data to CSV, avoiding duplicates.

        Args:
            data: List of data dictionaries from Oura API.
            data_type: Type of data (sleep, heartrate, activity, etc.).
            append: If True, append to existing file. If False, overwrite.
            date_field: Name of the date field for duplicate detection.

        Returns:
            Number of new records saved.
        """
        if not data:
            logger.info(f"No {data_type} data to save")
            return 0

        csv_path = self._get_csv_path(data_type)

        # For time-series data, use timestamp-based duplicate detection
        # For sleep data, use bedtime_start timestamp for duplicate detection
        # For other daily summary data, use date-based duplicate detection
        if data_type == "heartrate":
            existing_keys = self._get_existing_timestamps(csv_path, "timestamp") if append else set()
            key_field = "timestamp"
        elif data_type == "sleep":
            existing_keys = self._get_existing_timestamps(csv_path, "bedtime_start") if append else set()
            key_field = "bedtime_start"
        else:
            existing_keys = self._get_existing_dates(csv_path, date_field) if append else set()
            key_field = date_field

        # Flatten and filter out duplicates
        new_records = []
        for record in data:
            flattened = self._flatten_record(record, data_type)
            key = flattened.get(key_field)
            if key and key not in existing_keys:
                new_records.append(flattened)
                existing_keys.add(key)

        if not new_records:
            logger.info(f"No new {data_type} records to save (all dates already exist)")
            return 0

        # Determine fieldnames from all records
        all_fieldnames = set()
        for record in new_records:
            all_fieldnames.update(record.keys())

        # Read existing fieldnames if appending
        existing_fieldnames = set()
        if append and csv_path.exists():
            try:
                with open(csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    if reader.fieldnames:
                        existing_fieldnames = set(reader.fieldnames)
            except Exception:
                pass

        # Combine fieldnames, ensuring 'date' and 'is_nap' (for sleep) are first
        all_fieldnames = existing_fieldnames | all_fieldnames
        priority_fields = ["date"]
        if data_type == "sleep":
            priority_fields.append("is_nap")
        other_fields = sorted([f for f in all_fieldnames if f not in priority_fields])
        fieldnames = priority_fields + other_fields

        # Write records
        file_exists = csv_path.exists() and append
        mode = "a" if file_exists else "w"

        try:
            with open(csv_path, mode, encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerows(new_records)

            logger.info(f"Saved {len(new_records)} new {data_type} records to {csv_path}")
            return len(new_records)
        except Exception as e:
            logger.error(f"Failed to save {data_type} data: {e}")
            raise


# Backward compatibility alias
SleepDataStorage = OuraDataStorage

"""CSV storage for sleep data persistence."""

import csv
import os
from pathlib import Path
from typing import List, Dict, Set
import logging

logger = logging.getLogger(__name__)


class SleepDataStorage:
    """Manages CSV storage for sleep data."""

    def __init__(self, csv_path: str = "exports/data/sleep_data.csv"):
        """
        Initialize the storage handler.

        Args:
            csv_path: Path to the CSV file for storing sleep data.
        """
        self.csv_path = Path(csv_path)
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_existing_dates(self) -> Set[str]:
        """
        Read existing CSV and return set of dates already stored.

        Returns:
            Set of date strings (YYYY-MM-DD format).
        """
        if not self.csv_path.exists():
            return set()

        existing_dates = set()
        try:
            with open(self.csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if "date" in reader.fieldnames:
                    for row in reader:
                        if "date" in row and row["date"]:
                            existing_dates.add(row["date"])
        except Exception as e:
            logger.warning(f"Error reading existing CSV: {e}")
        return existing_dates

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

    def _flatten_sleep_record(self, record: Dict) -> Dict:
        """
        Flatten a nested sleep record into a flat dictionary.

        Args:
            record: Sleep record from Oura API.

        Returns:
            Flattened dictionary suitable for CSV storage.
        """
        flattened = {"date": record.get("day")}

        # Detect and flag naps
        flattened["is_nap"] = 1 if self._is_nap(record) else 0

        # Extract top-level fields
        for key in [
            "score",
            "total_sleep_duration",
            "average_breath",
            "average_heart_rate",
            "average_hrv",
            "lowest_heart_rate",
            "highest_heart_rate",
            "time_in_bed",
            "total_sleep_time",
            "awake_time",
            "rem_sleep_duration",
            "deep_sleep_duration",
            "light_sleep_duration",
        ]:
            if key in record:
                flattened[key] = record[key]

        # Extract nested contributors
        contributors = record.get("contributors", {})
        if contributors:
            for key, value in contributors.items():
                flattened[f"contributor_{key}"] = value

        # Extract sleep phases summary
        phases = record.get("sleep_phase_5_min", [])
        if phases:
            flattened["phases_count"] = len(phases)

        return flattened

    def save(self, sleep_data: List[Dict], append: bool = True) -> int:
        """
        Save sleep data to CSV, avoiding duplicates.

        Args:
            sleep_data: List of sleep data dictionaries from Oura API.
            append: If True, append to existing file. If False, overwrite.

        Returns:
            Number of new records saved.
        """
        if not sleep_data:
            logger.info("No sleep data to save")
            return 0

        existing_dates = self._get_existing_dates() if append else set()

        # Flatten and filter out duplicates
        new_records = []
        for record in sleep_data:
            date = record.get("day")
            if date and date not in existing_dates:
                flattened = self._flatten_sleep_record(record)
                new_records.append(flattened)
                existing_dates.add(date)

        if not new_records:
            logger.info("No new records to save (all dates already exist)")
            return 0

        # Determine fieldnames from all records
        all_fieldnames = set()
        for record in new_records:
            all_fieldnames.update(record.keys())

        # Read existing fieldnames if appending
        existing_fieldnames = set()
        if append and self.csv_path.exists():
            try:
                with open(self.csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    if reader.fieldnames:
                        existing_fieldnames = set(reader.fieldnames)
            except Exception:
                pass

        # Combine fieldnames, ensuring 'date' and 'is_nap' are first
        all_fieldnames = existing_fieldnames | all_fieldnames
        priority_fields = ["date", "is_nap"]
        other_fields = sorted([f for f in all_fieldnames if f not in priority_fields])
        fieldnames = priority_fields + other_fields

        # Write records
        file_exists = self.csv_path.exists() and append
        mode = "a" if file_exists else "w"

        try:
            with open(self.csv_path, mode, encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerows(new_records)

            logger.info(f"Saved {len(new_records)} new records to {self.csv_path}")
            return len(new_records)
        except Exception as e:
            logger.error(f"Failed to save sleep data: {e}")
            raise

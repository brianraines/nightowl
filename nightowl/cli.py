"""CLI interface for NightOwl sleep data collection."""

import argparse
import logging
import sys
from datetime import datetime, timedelta
from typing import Optional

from nightowl.api import OuraAPIClient, OuraAPIError
from nightowl.storage import SleepDataStorage
from nightowl.dashboard import create_dashboard

logger = logging.getLogger(__name__)


def setup_logging(debug: bool = False) -> None:
    """Configure logging for the application."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_date(date_str: str) -> str:
    """
    Validate and return date string in YYYY-MM-DD format.

    Args:
        date_str: Date string to validate.

    Returns:
        Validated date string.

    Raises:
        argparse.ArgumentTypeError: If date format is invalid.
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: {date_str}. Expected YYYY-MM-DD"
        )


def main() -> int:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Pull sleep data from the Oura API and persist to CSV"
    )
    parser.add_argument(
        "-s",
        "--start-date",
        type=parse_date,
        help="Start date in YYYY-MM-DD format (defaults to --days days ago)",
    )
    parser.add_argument(
        "-e",
        "--end-date",
        type=parse_date,
        help="End date in YYYY-MM-DD format (defaults to today)",
    )
    parser.add_argument(
        "-d",
        "--days",
        type=int,
        default=7,
        help="Number of days to fetch if dates not specified (default: 7)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="exports/sleep_data.csv",
        help="Path to CSV output file (default: exports/sleep_data.csv)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing CSV file instead of appending",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    setup_logging(debug=args.debug)

    try:
        # Initialize API client
        client = OuraAPIClient()

        # Fetch sleep data
        logger.info("Fetching sleep data from Oura API...")
        sleep_data = client.fetch_sleep_data(
            start_date=args.start_date,
            end_date=args.end_date,
            days=args.days,
        )

        if not sleep_data:
            logger.warning("No sleep data returned from API")
            return 0

        logger.info(f"Retrieved {len(sleep_data)} sleep records")

        # Save to CSV
        storage = SleepDataStorage(csv_path=args.output)
        saved_count = storage.save(sleep_data, append=not args.overwrite)

        logger.info(f"Successfully saved {saved_count} new records")

        # Generate dashboard
        try:
            dashboard_path = create_dashboard(args.output)
            logger.info(f"Dashboard generated: {dashboard_path}")
        except ImportError as e:
            logger.warning(
                f"Dashboard generation skipped: {e}. "
                "Install plotly and pandas to enable dashboard generation."
            )
        except Exception as e:
            logger.warning(f"Dashboard generation failed: {e}")

        return 0

    except OuraAPIError as e:
        logger.error(f"Oura API error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

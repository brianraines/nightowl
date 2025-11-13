"""CLI interface for NightOwl sleep data collection."""

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from nightowl.api import OuraAPIClient, OuraAPIError
from nightowl.storage import OuraDataStorage
from nightowl.dashboard import create_all_dashboards

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
        description="Pull all available data from the Oura API and persist to CSV"
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
        default="exports/data",
        help="Base directory for CSV output files (default: exports/data)",
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

        # Fetch all available data
        logger.info("Fetching all available data from Oura API...")
        all_data = client.fetch_all_data(
            start_date=args.start_date,
            end_date=args.end_date,
            days=args.days,
        )

        if not any(all_data.values()):
            logger.warning("No data returned from API")
            return 0

        # Initialize storage
        storage = OuraDataStorage(base_dir=args.output)
        total_saved = 0

        # Save each data type to its own CSV file
        for data_type, data_list in all_data.items():
            if data_list:
                logger.info(f"Saving {data_type} data...")
                saved_count = storage.save(
                    data_list,
                    data_type=data_type,
                    append=not args.overwrite,
                )
                total_saved += saved_count
                logger.info(f"Saved {saved_count} new {data_type} records")

        logger.info(f"Successfully saved {total_saved} total new records")

        # Generate all dashboards
        try:
            dashboard_paths = create_all_dashboards(args.output)
            logger.info(
                f"Generated {len(dashboard_paths)} dashboard(s): "
                + ", ".join([Path(p).name for p in dashboard_paths])
            )
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

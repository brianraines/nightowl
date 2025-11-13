"""Oura API client for fetching sleep data."""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class OuraAPIError(Exception):
    """Raised when Oura API requests fail."""

    pass


class OuraAPIClient:
    """Client for interacting with the Oura API."""

    BASE_URL = "https://api.ouraring.com/v2"
    SLEEP_ENDPOINT = f"{BASE_URL}/usercollection/sleep"

    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize the Oura API client.

        Args:
            access_token: Oura Personal Access Token. If not provided,
                         reads from OURA_ACCESS_TOKEN environment variable.
        """
        self.access_token = access_token or os.getenv("OURA_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError(
                "Oura access token required. Set OURA_ACCESS_TOKEN environment "
                "variable or pass access_token parameter."
            )

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests."""
        return {"Authorization": f"Bearer {self.access_token}"}

    def fetch_sleep_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 7,
    ) -> List[Dict]:
        """
        Fetch sleep data from the Oura API.

        Args:
            start_date: Start date in YYYY-MM-DD format. If not provided,
                       defaults to `days` days ago.
            end_date: End date in YYYY-MM-DD format. If not provided,
                     defaults to today.
            days: Number of days to fetch if start_date/end_date not provided.
                 Defaults to 7.

        Returns:
            List of sleep data dictionaries.

        Raises:
            OuraAPIError: If the API request fails.
        """
        if not end_date:
            end_date = datetime.today().date().isoformat()

        if not start_date:
            start = datetime.today().date() - timedelta(days=days)
            start_date = start.isoformat()

        params = {
            "start_date": start_date,
            "end_date": end_date,
        }

        logger.debug(
            f"Fetching sleep data from {start_date} to {end_date}"
        )

        try:
            response = requests.get(
                self.SLEEP_ENDPOINT,
                headers=self._get_headers(),
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch sleep data: {e}")
            raise OuraAPIError(f"API request failed: {e}") from e

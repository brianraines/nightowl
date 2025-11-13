"""Oura API client for fetching all available data."""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class OuraAPIError(Exception):
    """Raised when Oura API requests fails."""

    pass


class OuraAPIClient:
    """Client for interacting with the Oura API."""

    BASE_URL = "https://api.ouraring.com/v2"

    # All available endpoints per Oura API v2 documentation
    # Reference: https://cloud.ouraring.com/v2/docs
    # Note: activity and readiness endpoints return 404 and are not available in API v2
    SLEEP_ENDPOINT = f"{BASE_URL}/usercollection/sleep"
    HEARTRATE_ENDPOINT = f"{BASE_URL}/usercollection/heartrate"
    SESSION_ENDPOINT = f"{BASE_URL}/usercollection/session"
    WORKOUT_ENDPOINT = f"{BASE_URL}/usercollection/workout"
    TAG_ENDPOINT = f"{BASE_URL}/usercollection/tag"
    SPO2_ENDPOINT = f"{BASE_URL}/usercollection/spo2"

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

    def _get_date_params(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 7,
    ) -> Tuple[str, str]:
        """
        Get start and end date parameters.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            days: Number of days to fetch if dates not provided.

        Returns:
            Tuple of (start_date, end_date) strings.
        """
        if not end_date:
            end_date = datetime.today().date().isoformat()

        if not start_date:
            start = datetime.today().date() - timedelta(days=days)
            start_date = start.isoformat()

        return start_date, end_date

    def _fetch_endpoint(
        self,
        endpoint: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 7,
    ) -> List[Dict]:
        """
        Generic method to fetch data from any Oura API endpoint.

        Args:
            endpoint: API endpoint URL.
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            days: Number of days to fetch if dates not provided.

        Returns:
            List of data dictionaries.

        Raises:
            OuraAPIError: If the API request fails.
        """
        start_date, end_date = self._get_date_params(start_date, end_date, days)

        params = {
            "start_date": start_date,
            "end_date": end_date,
        }

        endpoint_name = endpoint.split("/")[-1]
        logger.debug(f"Fetching {endpoint_name} data from {start_date} to {end_date}")

        try:
            response = requests.get(
                endpoint,
                headers=self._get_headers(),
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except requests.exceptions.HTTPError as e:
            # Provide more context for 404 errors
            if e.response.status_code == 404:
                logger.debug(
                    f"404 error for {endpoint_name}: This endpoint may not be available "
                    f"for your account, may require different scopes, or may not exist in API v2"
                )
            raise OuraAPIError(f"API request failed for {endpoint_name}: {e}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {endpoint_name} data: {e}")
            raise OuraAPIError(f"API request failed for {endpoint_name}: {e}") from e

    def fetch_sleep_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 7,
    ) -> List[Dict]:
        """
        Fetch sleep data from the Oura API.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            days: Number of days to fetch if dates not provided.

        Returns:
            List of sleep data dictionaries.
        """
        return self._fetch_endpoint(
            self.SLEEP_ENDPOINT, start_date, end_date, days
        )

    def fetch_heartrate_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 7,
    ) -> List[Dict]:
        """
        Fetch heart rate data from the Oura API.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            days: Number of days to fetch if dates not provided.

        Returns:
            List of heart rate data dictionaries.
        """
        return self._fetch_endpoint(
            self.HEARTRATE_ENDPOINT, start_date, end_date, days
        )

    def fetch_session_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 7,
    ) -> List[Dict]:
        """
        Fetch session data from the Oura API.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            days: Number of days to fetch if dates not provided.

        Returns:
            List of session data dictionaries.
        """
        return self._fetch_endpoint(
            self.SESSION_ENDPOINT, start_date, end_date, days
        )

    def fetch_workout_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 7,
    ) -> List[Dict]:
        """
        Fetch workout data from the Oura API.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            days: Number of days to fetch if dates not provided.

        Returns:
            List of workout data dictionaries.
        """
        return self._fetch_endpoint(
            self.WORKOUT_ENDPOINT, start_date, end_date, days
        )

    def fetch_tag_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 7,
    ) -> List[Dict]:
        """
        Fetch tag data from the Oura API.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            days: Number of days to fetch if dates not provided.

        Returns:
            List of tag data dictionaries.
        """
        return self._fetch_endpoint(
            self.TAG_ENDPOINT, start_date, end_date, days
        )

    def fetch_spo2_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 7,
    ) -> List[Dict]:
        """
        Fetch SpO2 (blood oxygen saturation) data from the Oura API.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            days: Number of days to fetch if dates not provided.

        Returns:
            List of SpO2 data dictionaries.
        """
        return self._fetch_endpoint(
            self.SPO2_ENDPOINT, start_date, end_date, days
        )

    def fetch_all_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 7,
    ) -> Dict[str, List[Dict]]:
        """
        Fetch all available data from the Oura API.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            days: Number of days to fetch if dates not provided.

        Returns:
            Dictionary mapping data type names to lists of data dictionaries.
        """
        all_data = {}

        # Fetch all available data types per Oura API v2 documentation
        # Reference: https://cloud.ouraring.com/v2/docs
        # Note: activity and readiness endpoints return 404 and are not available in API v2
        data_fetchers = {
            "sleep": self.fetch_sleep_data,
            "heartrate": self.fetch_heartrate_data,
            "session": self.fetch_session_data,
            "workout": self.fetch_workout_data,
            "tag": self.fetch_tag_data,
            "spo2": self.fetch_spo2_data,
        }

        for data_type, fetcher in data_fetchers.items():
            try:
                logger.info(f"Fetching {data_type} data...")
                data = fetcher(start_date, end_date, days)
                all_data[data_type] = data
                logger.info(f"Retrieved {len(data)} {data_type} records")
            except OuraAPIError as e:
                # Check if it's a 404 error (endpoint not found)
                error_msg = str(e)
                if "404" in error_msg:
                    logger.warning(
                        f"Endpoint for {data_type} returned 404 - this endpoint may not be "
                        f"available for your account or may require different scopes. Skipping."
                    )
                else:
                    logger.warning(f"Failed to fetch {data_type} data: {e}")
                all_data[data_type] = []

        return all_data

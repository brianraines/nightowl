"""Tests for Oura API client."""

import os
from unittest.mock import Mock, patch
import pytest
import requests

from nightowl.api import OuraAPIClient, OuraAPIError

# Test token constant (not a real secret)
# nosec: B106 - This is a test-only token, not a real secret
TEST_TOKEN = "test-token-for-unit-tests-only"  # noqa: S106


class TestOuraAPIClient:
    """Test cases for OuraAPIClient."""

    def test_init_with_token(self):
        """Test initialization with explicit token."""
        client = OuraAPIClient(access_token=TEST_TOKEN)
        assert client.access_token == TEST_TOKEN

    def test_init_from_env(self):
        """Test initialization from environment variable."""
        with patch.dict(os.environ, {"OURA_ACCESS_TOKEN": "env-token"}):
            client = OuraAPIClient()
            assert client.access_token == "env-token"

    def test_init_no_token(self):
        """Test initialization fails without token."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Oura access token required"):
                OuraAPIClient()

    @patch("nightowl.api.requests.get")
    def test_fetch_sleep_data_success(self, mock_get):
        """Test successful sleep data fetch."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"day": "2024-01-01", "score": 85},
                {"day": "2024-01-02", "score": 90},
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = OuraAPIClient(access_token=TEST_TOKEN)
        data = client.fetch_sleep_data(start_date="2024-01-01", end_date="2024-01-02")

        assert len(data) == 2
        assert data[0]["day"] == "2024-01-01"
        mock_get.assert_called_once()

    @patch("nightowl.api.requests.get")
    def test_fetch_sleep_data_api_error(self, mock_get):
        """Test API error handling."""
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        client = OuraAPIClient(access_token=TEST_TOKEN)
        with pytest.raises(OuraAPIError, match="API request failed"):
            client.fetch_sleep_data()

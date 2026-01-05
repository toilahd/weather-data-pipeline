import unittest
from unittest.mock import patch, MagicMock

from api_request.api_client import OpenMeteoAPIClient
from api_request.exceptions import APIConnectionError
import requests

class TestOpenMeteoAPIClient(unittest.TestCase):

    def setUp(self):
        self.client = OpenMeteoAPIClient()
        self.city = {
            "name": "Hanoi",
            "lat": 21.0285,
            "lon": 105.8542
        }

    @patch("api_request.api_client.requests.Session.get")
    def test_fetch_current_weather_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "current_weather": {"temperature": 30}
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.client.fetch_current_weather(self.city)

        self.assertIn("current_weather", result)
        mock_get.assert_called_once()



    @patch("api_request.api_client.time.sleep")
    @patch("api_request.api_client.requests.Session.get")
    def test_api_retry_and_fail(self, mock_get, mock_sleep):
        mock_get.side_effect = requests.RequestException("API down")

        with self.assertRaises(APIConnectionError):
            self.client.fetch_current_weather(self.city)

        self.assertEqual(mock_get.call_count, self.client.max_retries)

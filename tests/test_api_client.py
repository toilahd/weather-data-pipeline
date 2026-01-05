import unittest
from unittest.mock import patch, Mock
from api_request.api_client import OpenMeteoAPIClient
from api_request.exceptions import APIConnectionError


class TestOpenMeteoAPIClient(unittest.TestCase):

    def setUp(self):
        self.client = OpenMeteoAPIClient()
        self.city_data = {
            "name": "Ha Noi",
            "lat": 21.0285,
            "lon": 105.8542
        }

    @patch("api_request.requests.Session.get")
    def test_fetch_current_weather_success(self, mock_get):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "current_weather": {
                "temperature": 26.5,
                "windspeed": 10.2,
                "weathercode": 2,
                "time": "2025-01-05T10:00"
            }
        }
        mock_get.return_value = mock_response

        data = self.client.fetch_current_weather(self.city_data)

        self.assertIsNotNone(data)
        self.assertIn("current_weather", data)

    @patch("api_request.requests.Session.get")
    def test_api_retry_and_fail(self, mock_get):
        mock_get.side_effect = Exception("Network error")

        with self.assertRaises(APIConnectionError):
            self.client.fetch_current_weather(self.city_data)


if __name__ == "__main__":
    unittest.main()

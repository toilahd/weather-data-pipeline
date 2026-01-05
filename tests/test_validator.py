"""
Unit tests for weather data pipeline
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from api_request.api_client import OpenMeteoAPIClient
from api_request.validators import WeatherDataValidator
from api_request.config import Config
from api_request.exceptions import APIConnectionError, DataValidationError


class TestWeatherDataValidator(unittest.TestCase):
    """Test data validation logic"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_data = {
            "latitude": 40.714,
            "longitude": -74.006,
            "timezone": "America/New_York",
            "current": {
                "time": "2023-10-01T10:00",
                "temperature_2m": 22,
                "relative_humidity_2m": 65,
                "apparent_temperature": 21,
                "precipitation": 0.0,
                "weather_code": 0,
                "cloud_cover": 25,
                "pressure_msl": 1013.5,
                "wind_speed_10m": 13,
                "wind_direction_10m": 180,
                "is_day": 1
            }
        }
    
    def test_validate_temperature_valid(self):
        """Test temperature validation with valid values"""
        self.assertTrue(WeatherDataValidator.validate_temperature(25))
        self.assertTrue(WeatherDataValidator.validate_temperature(-10))
        self.assertTrue(WeatherDataValidator.validate_temperature(0))
    
    def test_validate_temperature_invalid(self):
        """Test temperature validation with invalid values"""
        self.assertFalse(WeatherDataValidator.validate_temperature(-150))
        self.assertFalse(WeatherDataValidator.validate_temperature(100))
    
    def test_validate_wind_speed_valid(self):
        """Test wind speed validation with valid values"""
        self.assertTrue(WeatherDataValidator.validate_wind_speed(0))
        self.assertTrue(WeatherDataValidator.validate_wind_speed(50))
        self.assertTrue(WeatherDataValidator.validate_wind_speed(150))
    
    def test_validate_wind_speed_invalid(self):
        """Test wind speed validation with invalid values"""
        self.assertFalse(WeatherDataValidator.validate_wind_speed(-10))
        self.assertFalse(WeatherDataValidator.validate_wind_speed(300))
    
    def test_validate_humidity_valid(self):
        """Test humidity validation with valid values"""
        self.assertTrue(WeatherDataValidator.validate_humidity(0))
        self.assertTrue(WeatherDataValidator.validate_humidity(50))
        self.assertTrue(WeatherDataValidator.validate_humidity(100))
    
    def test_validate_humidity_invalid(self):
        """Test humidity validation with invalid values"""
        self.assertFalse(WeatherDataValidator.validate_humidity(-5))
        self.assertFalse(WeatherDataValidator.validate_humidity(105))
    
    def test_validate_coordinates_valid(self):
        """Test coordinate validation with valid values"""
        self.assertTrue(WeatherDataValidator.validate_coordinates("40.714", "-74.006"))
        self.assertTrue(WeatherDataValidator.validate_coordinates("0", "0"))
        self.assertTrue(WeatherDataValidator.validate_coordinates("90", "180"))
    
    def test_validate_coordinates_invalid(self):
        """Test coordinate validation with invalid values"""
        self.assertFalse(WeatherDataValidator.validate_coordinates("100", "0"))
        self.assertFalse(WeatherDataValidator.validate_coordinates("0", "200"))
        self.assertFalse(WeatherDataValidator.validate_coordinates("invalid", "invalid"))
    
    def test_validate_complete_data_valid(self):
        """Test complete data validation with valid data"""
        is_valid, errors = WeatherDataValidator.validate_weather_data(self.valid_data)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_complete_data_missing_fields(self):
        """Test validation with missing required fields"""
        invalid_data = {"latitude": 40.714}
        is_valid, errors = WeatherDataValidator.validate_weather_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


class TestWeatherAPIClient(unittest.TestCase):
    """Test API client"""
    
    @patch('requests.Session')
    def test_fetch_city_weather_success(self, mock_session):
        """Test successful weather fetch"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "latitude": 40.714,
            "longitude": -74.006,
            "timezone": "America/New_York",
            "current": {
                "time": "2023-10-01T10:00",
                "temperature_2m": 20,
                "relative_humidity_2m": 60,
                "apparent_temperature": 19,
                "precipitation": 0.0,
                "weather_code": 0,
                "cloud_cover": 30,
                "pressure_msl": 1015.0,
                "wind_speed_10m": 10,
                "wind_direction_10m": 90,
                "is_day": 1
            }
        }
        mock_response.raise_for_status = Mock()
        mock_session.return_value.get.return_value = mock_response
        
        client = OpenMeteoAPIClient()
        city_data = {"name": "Test City", "lat": 40.714, "lon": -74.006}
        data = client.fetch_current_weather(city_data)
        
        self.assertIsNotNone(data)
        self.assertEqual(data['latitude'], 40.714)
    
    @patch('requests.Session')
    def test_fetch_city_weather_api_error(self, mock_session):
        """Test API error response"""
        # Mock error response that raises an exception
        mock_session.return_value.get.side_effect = Exception("API down")
        
        client = OpenMeteoAPIClient()
        city_data = {"name": "Test City", "lat": 40.714, "lon": -74.006}
        
        with self.assertRaises(Exception):
            client.fetch_current_weather(city_data)


class TestConfig(unittest.TestCase):
    """Test configuration"""
    
    def test_database_url_construction(self):
        """Test database URL construction"""
        url = Config.get_database_url()
        self.assertIn(Config.DB_HOST, url)
        self.assertIn(Config.DB_NAME, url)
        self.assertIn(str(Config.DB_PORT), url)


if __name__ == '__main__':
    unittest.main()

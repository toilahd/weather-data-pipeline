"""
Unit tests for weather data pipeline
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from api_request import WeatherAPIClient
from api_request.validators import WeatherDataValidator
from api_request.config import Config
from api_request.exceptions import APIConnectionError, DataValidationError


class TestWeatherDataValidator(unittest.TestCase):
    """Test data validation logic"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_data = {
            "location": {
                "name": "New York",
                "country": "USA",
                "lat": "40.714",
                "lon": "-74.006",
                "localtime": "2023-10-01 10:00",
                "utc_offset": "-4.0"
            },
            "current": {
                "temperature": 22,
                "wind_speed": 13,
                "humidity": 56,
                "weather_descriptions": ["Sunny"]
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
        invalid_data = {"location": {}}
        is_valid, errors = WeatherDataValidator.validate_weather_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_sanitize_data(self):
        """Test data sanitization"""
        sanitized = WeatherDataValidator.sanitize_data(self.valid_data)
        self.assertIsInstance(sanitized['temperature'], float)
        self.assertIsInstance(sanitized['wind_speed'], float)
        self.assertEqual(sanitized['city'], "New York")


class TestWeatherAPIClient(unittest.TestCase):
    """Test API client"""
    
    @patch('api_request.requests.Session')
    def test_fetch_city_weather_success(self, mock_session):
        """Test successful weather fetch"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "location": {"name": "Test City", "localtime": "2023-10-01 10:00"},
            "current": {"temperature": 20, "wind_speed": 10}
        }
        mock_response.raise_for_status = Mock()
        mock_session.return_value.get.return_value = mock_response
        
        client = WeatherAPIClient()
        data = client.fetch_city_weather("Test City")
        
        self.assertIsNotNone(data)
        self.assertEqual(data['location']['name'], "Test City")
    
    @patch('api_request.requests.Session')
    def test_fetch_city_weather_api_error(self, mock_session):
        """Test API error response"""
        # Mock error response
        mock_response = Mock()
        mock_response.json.return_value = {
            "error": {"info": "API key invalid"}
        }
        mock_response.raise_for_status = Mock()
        mock_session.return_value.get.return_value = mock_response
        
        client = WeatherAPIClient()
        data = client.fetch_city_weather("Test City")
        
        self.assertIsNone(data)


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

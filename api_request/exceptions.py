"""
Custom exceptions for weather data pipeline
"""


class WeatherPipelineException(Exception):
    """Base exception for weather pipeline"""
    pass


class APIConnectionError(WeatherPipelineException):
    """Raised when API connection fails"""
    pass


class APIResponseError(WeatherPipelineException):
    """Raised when API returns invalid response"""
    pass


class DatabaseConnectionError(WeatherPipelineException):
    """Raised when database connection fails"""
    pass


class DataValidationError(WeatherPipelineException):
    """Raised when data validation fails"""
    pass


class ConfigurationError(WeatherPipelineException):
    """Raised when configuration is invalid"""
    pass

"""
Configuration management for weather data pipeline
"""
import os
from typing import Any, List, Dict
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration class"""

    # =========================
    # API Configuration
    # =========================
    API_BASE_URL = "https://api.open-meteo.com/v1/forecast"
    HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"

    API_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    TIMEZONE = "Asia/Ho_Chi_Minh"

    WEATHER_CODES = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",

        45: "Fog",
        48: "Depositing rime fog",

        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",

        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",

        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",

        66: "Light freezing rain",
        67: "Heavy freezing rain",

        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",

        77: "Snow grains",

        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",

        85: "Slight snow showers",
        86: "Heavy snow showers",

        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }

    # =========================
    # Database Configuration
    # =========================
    DB_NAME = os.getenv("DB_NAME", "db")
    DB_USER = os.getenv("DB_USER", "db_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "db_password")
    DB_HOST = os.getenv("DB_HOST", "db")
    DB_PORT = os.getenv("DB_PORT", "5432")

    # =========================
    # Cities to track (Vietnam)
    # =========================
    CITIES: List[Dict[str, Any]] = [

        {"name": "Ha Noi", "lat": 21.0285, "lon": 105.8542},
        {"name": "Hai Phong", "lat": 20.8449, "lon": 106.6881},

        {"name": "Da Nang", "lat": 16.0544, "lon": 108.2022},
        {"name": "Hue", "lat": 16.4637, "lon": 107.5909},
        {"name": "Nha Trang", "lat": 12.2388, "lon": 109.1967},
        
        {"name": "Ho Chi Minh", "lat": 10.8231, "lon": 106.6297},
        {"name": "Can Tho", "lat": 10.0452, "lon": 105.7469},
        {"name": "Vung Tau", "lat": 10.4114, "lon": 107.1362},
    ]

    # =========================
    # Data Quality Thresholds
    # =========================
    TEMPERATURE_MIN = -100  # Celsius
    TEMPERATURE_MAX = 60
    WIND_SPEED_MAX = 200    # km/h
    HUMIDITY_MIN = 0
    HUMIDITY_MAX = 100

    # =========================
    # Helpers
    # =========================
    @classmethod
    def get_database_url(cls) -> str:
        """Construct database connection URL"""
        return (
            f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}"
            f"@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
        )

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not all([cls.DB_NAME, cls.DB_USER, cls.DB_PASSWORD, cls.DB_HOST, cls.DB_PORT]):
            raise ValueError("Database configuration is incomplete")

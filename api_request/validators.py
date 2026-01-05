"""
Data validation module for Open-Meteo weather data
"""
from typing import Dict, Any, List, Tuple
from datetime import datetime
from config import Config
from logger_config import setup_logger

logger = setup_logger(__name__)


class WeatherDataValidator:
    """Validates Open-Meteo weather data before insertion"""

    # =========================
    # Field-level validators
    # =========================
    @staticmethod
    def validate_temperature(temp: float) -> bool:
        return Config.TEMPERATURE_MIN <= temp <= Config.TEMPERATURE_MAX

    @staticmethod
    def validate_wind_speed(speed: float) -> bool:
        return 0 <= speed <= Config.WIND_SPEED_MAX

    @staticmethod
    def validate_humidity(humidity: float) -> bool:
        return Config.HUMIDITY_MIN <= humidity <= Config.HUMIDITY_MAX

    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> bool:
        return -90 <= lat <= 90 and -180 <= lon <= 180

    # =========================
    # Main validation
    # =========================
    @classmethod
    def validate_weather_data(
        cls, data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate Open-Meteo API response

        Expected:
        - latitude, longitude
        - current_weather OR daily/hourly blocks
        """
        errors: List[str] = []

        # Validate coordinates
        lat = data.get("latitude")
        lon = data.get("longitude")

        if lat is None or lon is None:
            errors.append("Missing latitude or longitude")
        elif not cls.validate_coordinates(lat, lon):
            errors.append(f"Invalid coordinates: lat={lat}, lon={lon}")

        # Validate current weather (forecast endpoint)
        current = data.get("current_weather")
        if not current:
            errors.append("Missing current_weather block")
        else:
            # Temperature
            temp = current.get("temperature")
            if temp is None:
                errors.append("Missing temperature")
            elif not isinstance(temp, (int, float)):
                errors.append("Temperature must be numeric")
            elif not cls.validate_temperature(temp):
                errors.append(f"Temperature out of range: {temp}")

            # Wind speed
            wind_speed = current.get("windspeed")
            if wind_speed is None:
                errors.append("Missing windspeed")
            elif not isinstance(wind_speed, (int, float)):
                errors.append("Windspeed must be numeric")
            elif not cls.validate_wind_speed(wind_speed):
                errors.append(f"Windspeed too high: {wind_speed}")

            # Weather code
            weather_code = current.get("weathercode")
            if weather_code is None:
                errors.append("Missing weathercode")
            elif weather_code not in Config.WEATHER_CODES:
                errors.append(f"Unknown weathercode: {weather_code}")

            # Time
            time_str = current.get("time")
            if not time_str:
                errors.append("Missing weather time")
            else:
                try:
                    datetime.fromisoformat(time_str)
                except ValueError:
                    errors.append(f"Invalid time format: {time_str}")

        is_valid = len(errors) == 0

        if is_valid:
            logger.debug("Weather data validation passed")
        else:
            logger.warning(f"Weather data validation failed: {errors}")

        return is_valid, errors

    # =========================
    # Sanitization
    # =========================
    @staticmethod
    def sanitize_weather_data(
        data: Dict[str, Any], city_name: str
    ) -> Dict[str, Any]:
        """
        Normalize Open-Meteo data into DB-friendly format
        """
        current = data.get("current_weather", {})

        return {
            "city": city_name,
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "temperature": float(current.get("temperature", 0.0)),
            "windspeed": float(current.get("windspeed", 0.0)),
            "winddirection": int(current.get("winddirection", 0)),
            "weathercode": int(current.get("weathercode", -1)),
            "weather_description": Config.WEATHER_CODES.get(
                current.get("weathercode"), "Unknown"
            ),
            "time": current.get("time"),
            "timezone": data.get("timezone"),
        }

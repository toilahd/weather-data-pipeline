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
        try:
            lat_val = float(lat)
            lon_val = float(lon)
            return -90 <= lat_val <= 90 and -180 <= lon_val <= 180
        except (ValueError, TypeError):
            return False

    # =========================
    # Main validation
    # =========================
    @classmethod
    def validate_weather_data(
        cls, data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate Open-Meteo API response with current weather data

        Expected:
        - latitude, longitude
        - current block with weather variables
        """
        errors: List[str] = []

        # Validate coordinates
        lat = data.get("latitude")
        lon = data.get("longitude")

        if lat is None or lon is None:
            errors.append("Missing latitude or longitude")
        elif not cls.validate_coordinates(lat, lon):
            errors.append(f"Invalid coordinates: lat={lat}, lon={lon}")

        # Validate current weather data
        current = data.get("current")
        if not current:
            errors.append("Missing current block")
        else:
            # Temperature
            temp = current.get("temperature_2m")
            if temp is None:
                errors.append("Missing temperature_2m")
            elif not isinstance(temp, (int, float)):
                errors.append("Temperature must be numeric")
            elif not cls.validate_temperature(temp):
                errors.append(f"Temperature out of range: {temp}")

            # Wind speed
            wind_speed = current.get("wind_speed_10m")
            if wind_speed is None:
                errors.append("Missing wind_speed_10m")
            elif not isinstance(wind_speed, (int, float)):
                errors.append("Wind speed must be numeric")
            elif not cls.validate_wind_speed(wind_speed):
                errors.append(f"Wind speed too high: {wind_speed}")

            # Humidity
            humidity = current.get("relative_humidity_2m")
            if humidity is not None:
                if not isinstance(humidity, (int, float)):
                    errors.append("Humidity must be numeric")
                elif not cls.validate_humidity(humidity):
                    errors.append(f"Humidity out of range: {humidity}")

            # Weather code
            weather_code = current.get("weather_code")
            if weather_code is None:
                errors.append("Missing weather_code")
            elif weather_code not in Config.WEATHER_CODES:
                errors.append(f"Unknown weather_code: {weather_code}")

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
        current = data.get("current", {})
        weather_code = int(current.get("weather_code", -1))

        return {
            "city": city_name,
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "temperature": float(current.get("temperature_2m", 0.0)),
            "feels_like": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "pressure": current.get("pressure_msl"),
            "windspeed": float(current.get("wind_speed_10m", 0.0)),
            "winddirection": int(current.get("wind_direction_10m", 0)),
            "cloud_cover": current.get("cloud_cover"),
            "precipitation": current.get("precipitation"),
            "is_day": current.get("is_day"),
            "weathercode": weather_code,
            "weather_description": Config.WEATHER_CODES.get(
                weather_code, "Unknown"
            ),
            "time": current.get("time"),
            "timezone": data.get("timezone"),
        }

"""
Database operations for Open-Meteo weather data pipeline
"""
import psycopg2
from psycopg2 import pool
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

from config import Config
from api_client import OpenMeteoAPIClient
from validators import WeatherDataValidator
from exceptions import DatabaseConnectionError
from logger_config import setup_logger

logger = setup_logger(__name__)


class WeatherDatabase:
    """Database handler with connection pooling"""

    def __init__(self):
        try:
            self.connection_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=Config.DB_HOST,
                database=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                port=Config.DB_PORT,
            )
            logger.info("Database connection pool initialized")
        except psycopg2.Error as e:
            raise DatabaseConnectionError(e)

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = self.connection_pool.getconn()
            yield conn
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            raise DatabaseConnectionError(e)
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    # =========================
    # Schema
    # =========================
    def create_tables(self):
        with self.get_connection() as conn:
            cur = conn.cursor()

            cur.execute("CREATE SCHEMA IF NOT EXISTS dev;")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS dev.raw_weather_data (
                    id SERIAL PRIMARY KEY,
                    city VARCHAR(100) NOT NULL,
                    latitude DECIMAL(8,5),
                    longitude DECIMAL(8,5),

                    temperature FLOAT NOT NULL,
                    feels_like FLOAT,
                    humidity INTEGER,
                    pressure FLOAT,
                    windspeed FLOAT NOT NULL,
                    winddirection INTEGER,
                    cloud_cover INTEGER,
                    precipitation FLOAT,
                    is_day INTEGER,
                    
                    weathercode INTEGER,
                    weather_description TEXT,

                    time TIMESTAMP NOT NULL,
                    timezone TEXT,
                    inserted_at TIMESTAMP DEFAULT NOW(),

                    CONSTRAINT uq_city_time UNIQUE (city, time)
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS dev.data_quality_audit (
                    id SERIAL PRIMARY KEY,
                    city VARCHAR(100),
                    validation_errors TEXT[],
                    raw_data JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)

            conn.commit()
            cur.close()
            logger.info("Database schema ready")

    # =========================
    # Insert
    # =========================
    def insert_weather_record(
        self, city: Dict[str, Any], data: Dict[str, Any]
    ) -> bool:

        is_valid, errors = WeatherDataValidator.validate_weather_data(data)

        if not is_valid:
            self._log_validation_failure(city["name"], data, errors)
            return False

        row = WeatherDataValidator.sanitize_weather_data(data, city["name"])

        with self.get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("""
                    INSERT INTO dev.raw_weather_data (
                        city, latitude, longitude,
                        temperature, feels_like, humidity, pressure,
                        windspeed, winddirection, cloud_cover,
                        precipitation, is_day,
                        weathercode, weather_description,
                        time, timezone
                    ) VALUES (
                        %(city)s, %(latitude)s, %(longitude)s,
                        %(temperature)s, %(feels_like)s, %(humidity)s, %(pressure)s,
                        %(windspeed)s, %(winddirection)s, %(cloud_cover)s,
                        %(precipitation)s, %(is_day)s,
                        %(weathercode)s, %(weather_description)s,
                        %(time)s, %(timezone)s
                    )
                    ON CONFLICT (city, time) DO UPDATE SET
                        temperature = EXCLUDED.temperature,
                        feels_like = EXCLUDED.feels_like,
                        humidity = EXCLUDED.humidity,
                        pressure = EXCLUDED.pressure,
                        windspeed = EXCLUDED.windspeed,
                        winddirection = EXCLUDED.winddirection,
                        cloud_cover = EXCLUDED.cloud_cover,
                        precipitation = EXCLUDED.precipitation,
                        is_day = EXCLUDED.is_day,
                        weathercode = EXCLUDED.weathercode,
                        weather_description = EXCLUDED.weather_description,
                        inserted_at = NOW();
                """, row)

                conn.commit()
                cur.close()
                logger.info(f"Inserted weather data for {row['city']}")
                return True

            except psycopg2.Error as e:
                conn.rollback()
                cur.close()
                logger.error(f"Insert failed for {row['city']}: {e}")
                return False

    def insert_batch(
        self,
        cities: List[Dict[str, Any]],
        api_client: OpenMeteoAPIClient,
        days: int = 1,
    ) -> Dict[str, int]:

        success = 0
        failed = 0

        for city in cities:
            data = api_client.fetch_forecast_weather(city, days)
            if data and self.insert_weather_record(city, data):
                success += 1
            else:
                failed += 1

        return {"success": success, "failed": failed}

    # =========================
    # Audit
    # =========================
    def _log_validation_failure(
        self,
        city: str,
        data: Dict[str, Any],
        errors: List[str],
    ):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO dev.data_quality_audit
                (city, validation_errors, raw_data)
                VALUES (%s, %s, %s)
            """, (city, errors, psycopg2.extras.Json(data)))
            conn.commit()
            cur.close()

    # =========================
    # Stats
    # =========================
    def get_stats(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    COUNT(*) AS total_records,
                    COUNT(DISTINCT city) AS cities,
                    MIN(inserted_at),
                    MAX(inserted_at)
                FROM dev.raw_weather_data;
            """)
            r = cur.fetchone()
            cur.close()

            return {
                "total_records": r[0],
                "cities": r[1],
                "first_insert": r[2],
                "last_insert": r[3],
            }

    def __del__(self):
        if hasattr(self, 'connection_pool') and self.connection_pool:
            self.connection_pool.closeall()

{{
    config(
        materialized='table'
    )
}}

WITH latest_per_city AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY city 
            ORDER BY weather_time DESC
        ) AS recency_rank
    FROM {{ ref('stg_weather_data') }}
),

current_weather AS (
    SELECT 
        weather_id,
        city,
        latitude,
        longitude,
        weather_time AS observation_time,
        timezone,
        
        -- Temperature
        temperature_c,
        feels_like_c,
        temperature_f,
        feels_like_f,
        temperature_c - feels_like_c AS temp_feels_diff,
        
        -- Atmosphere
        humidity_pct,
        pressure_msl,
        cloud_cover_pct,
        precipitation_mm,
        
        -- Wind
        wind_speed_kmh,
        wind_speed_mph,
        wind_direction_deg,
        CASE 
            WHEN wind_direction_deg >= 337.5 OR wind_direction_deg < 22.5 THEN 'N'
            WHEN wind_direction_deg < 67.5 THEN 'NE'
            WHEN wind_direction_deg < 112.5 THEN 'E'
            WHEN wind_direction_deg < 157.5 THEN 'SE'
            WHEN wind_direction_deg < 202.5 THEN 'S'
            WHEN wind_direction_deg < 247.5 THEN 'SW'
            WHEN wind_direction_deg < 292.5 THEN 'W'
            WHEN wind_direction_deg < 337.5 THEN 'NW'
        END AS wind_direction_cardinal,
        
        -- Weather codes
        weathercode,
        weather_description,
        
        -- Day/Night
        CASE WHEN is_day = 1 THEN 'Day' ELSE 'Night' END AS time_of_day,
        
        -- Derived metrics
        CASE 
            WHEN temperature_c < 10 THEN 'Cold'
            WHEN temperature_c < 20 THEN 'Cool'
            WHEN temperature_c < 25 THEN 'Comfortable'
            WHEN temperature_c < 30 THEN 'Warm'
            ELSE 'Hot'
        END AS comfort_level,
        
        CASE 
            WHEN wind_speed_kmh < 5 THEN 'Calm'
            WHEN wind_speed_kmh < 20 THEN 'Light'
            WHEN wind_speed_kmh < 40 THEN 'Moderate'
            WHEN wind_speed_kmh < 60 THEN 'Strong'
            ELSE 'Very Strong'
        END AS wind_strength,
        
        CASE 
            WHEN precipitation_mm > 10 THEN 'Heavy Rain'
            WHEN precipitation_mm > 2 THEN 'Moderate Rain'
            WHEN precipitation_mm > 0 THEN 'Light Rain'
            ELSE 'No Rain'
        END AS rain_status,
        
        -- Data freshness
        inserted_at AS data_loaded_at,
        EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - inserted_at))/60 AS minutes_since_load
        
    FROM latest_per_city
    WHERE recency_rank = 1
)

SELECT * FROM current_weather
ORDER BY city
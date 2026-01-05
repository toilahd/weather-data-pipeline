{{
    config(
        materialized='incremental',
        unique_key='id',
        on_schema_change='fail'
    )
}}

WITH source AS (
    SELECT * 
    FROM {{ source('dev', 'raw_weather_data') }}
    {% if is_incremental() %}
    -- Only process new records in incremental runs
    WHERE inserted_at > (SELECT MAX(inserted_at_local) FROM {{ this }})
    {% endif %}
),

de_dup AS (
    -- Remove duplicates based on city and time, keeping the most recent insert
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY city, time 
            ORDER BY inserted_at DESC
        ) AS rn
    FROM source
),

cleaned AS (
    SELECT 
        id,
        city,
        latitude,
        longitude,
        temperature,
        feels_like,
        humidity,
        pressure,
        weather_description,
        windspeed,
        winddirection,
        cloud_cover,
        precipitation,
        is_day,
        time AS weather_time_local,
        timezone,
        inserted_at AS inserted_at_utc
    FROM de_dup
    WHERE rn = 1
)

SELECT * FROM cleaned

{{
    config(
        materialized='incremental',
        unique_key=['city', 'weather_time'],
        on_schema_change='append_new_columns'
    )
}}

WITH source AS (
    SELECT * 
    FROM {{ source('dev', 'raw_weather_data') }}
    {% if is_incremental() %}
    WHERE inserted_at > (SELECT COALESCE(MAX(inserted_at), '1900-01-01') FROM {{ this }})
    {% endif %}
),

deduped AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY city, time 
            ORDER BY inserted_at DESC
        ) AS row_num
    FROM source
),

cleaned AS (
    SELECT 
        -- Identifiers
        {{ dbt_utils.generate_surrogate_key(['city', 'time']) }} AS weather_id,
        city,
        ROUND(latitude::numeric, 4) AS latitude,
        ROUND(longitude::numeric, 4) AS longitude,
        
        -- Timestamps
        time AS weather_time,
        timezone,
        inserted_at,
        
        -- Temperature metrics
        ROUND(temperature::numeric, 1) AS temperature_c,
        ROUND(feels_like::numeric, 1) AS feels_like_c,
        ROUND((temperature * 9.0/5.0 + 32)::numeric, 1) AS temperature_f,
        ROUND((feels_like * 9.0/5.0 + 32)::numeric, 1) AS feels_like_f,
        
        -- Atmospheric conditions
        humidity AS humidity_pct,
        ROUND(pressure::numeric, 1) AS pressure_msl,
        cloud_cover AS cloud_cover_pct,
        ROUND(precipitation::numeric, 2) AS precipitation_mm,
        
        -- Wind
        ROUND(windspeed::numeric, 1) AS wind_speed_kmh,
        ROUND((windspeed * 0.621371)::numeric, 1) AS wind_speed_mph,
        winddirection AS wind_direction_deg,
        
        -- Weather codes
        weathercode,
        weather_description,
        
        -- Day/Night flag
        is_day,
        
        -- Data quality
        CASE 
            WHEN temperature IS NULL THEN FALSE
            WHEN humidity IS NULL THEN FALSE
            WHEN windspeed IS NULL THEN FALSE
            ELSE TRUE
        END AS is_valid_record
        
    FROM deduped
    WHERE row_num = 1
)

SELECT * FROM cleaned
WHERE is_valid_record = TRUE

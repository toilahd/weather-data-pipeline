{{
    config(
        materialized='table',
        unique_key='id'

    )
}}
WITH source AS (
    SELECT * 
    FROM {{source('dev', 'raw_weather_data')}}
),


de_dup AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (PARTITION BY id ORDER BY inserted_at DESC) AS rn
    FROM source
)


SELECT 
    id,
    city,
    temperature,
    weather_description,
    wind_speed,
    time as weather_time_local,
    (inserted_at + (utc_offset || ' hours')::interval) AS inserted_at_local
FROM de_dup
WHERE rn = 1


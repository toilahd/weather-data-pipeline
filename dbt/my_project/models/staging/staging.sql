{{
    config(
        materialized='table',
        unique_key='id'

    )
}}
WITH source AS (
    SELECT * 
    FROM {{source('dev', 'raw_weather_data')}}
)

SELECT 
    id,
    city,
    temperature,
    weather_description,
    wind_speed,
    time as weather_time_local,
    (inserted_at + (utc_offset || ' hours')::interval) AS inserted_at_local
FROM source


{{
    config(
        materialized='table',
        unique_key='id'
    )
}}

WITH latest_weather AS (
    SELECT 
        city,
        latitude,
        longitude,
        temperature,
        feels_like,
        weather_description,
        windspeed,
        winddirection,
        humidity,
        pressure,
        cloud_cover,
        precipitation,
        is_day,
        weather_time_local,
        timezone,
        inserted_at_utc,
        
        -- Get the most recent record for each city
        ROW_NUMBER() OVER (PARTITION BY city ORDER BY weather_time_local DESC) AS rn
        
    FROM {{ ref('stg_weather_data') }}
),

weather_with_context AS (
    SELECT 
        *,
        -- Temperature feels like context
        CASE 
            WHEN feels_like IS NOT NULL AND feels_like < temperature - 5 THEN 'Feels colder'
            WHEN feels_like IS NOT NULL AND feels_like > temperature + 5 THEN 'Feels warmer'
            ELSE 'Feels about right'
        END AS feels_like_context,
        
        -- Wind categorization
        CASE 
            WHEN windspeed < 10 THEN 'Calm'
            WHEN windspeed < 30 THEN 'Moderate'
            WHEN windspeed < 60 THEN 'Strong'
            ELSE 'Very Strong'
        END AS wind_category,
        
        -- Wind direction text
        CASE 
            WHEN winddirection >= 337.5 OR winddirection < 22.5 THEN 'N'
            WHEN winddirection >= 22.5 AND winddirection < 67.5 THEN 'NE'
            WHEN winddirection >= 67.5 AND winddirection < 112.5 THEN 'E'
            WHEN winddirection >= 112.5 AND winddirection < 157.5 THEN 'SE'
            WHEN winddirection >= 157.5 AND winddirection < 202.5 THEN 'S'
            WHEN winddirection >= 202.5 AND winddirection < 247.5 THEN 'SW'
            WHEN winddirection >= 247.5 AND winddirection < 292.5 THEN 'W'
            WHEN winddirection >= 292.5 AND winddirection < 337.5 THEN 'NW'
            ELSE 'Unknown'
        END AS wind_dir,
        
        -- Day/Night indicator
        CASE 
            WHEN is_day = 1 THEN 'Day'
            WHEN is_day = 0 THEN 'Night'
            ELSE 'Unknown'
        END AS day_night
        
    FROM latest_weather
    WHERE rn = 1
)

SELECT 
    {{ dbt_utils.generate_surrogate_key(['city', 'weather_time_local']) }} AS id,
    city,
    latitude,
    longitude,
    temperature,
    feels_like,
    feels_like_context,
    weather_description,
    windspeed AS wind_speed,
    winddirection AS wind_degree,
    wind_dir,
    wind_category,
    humidity,
    pressure,
    cloud_cover,
    precipitation,
    day_night,
    weather_time_local AS observation_time,
    timezone,
    inserted_at_utc AS data_inserted_at
FROM weather_with_context
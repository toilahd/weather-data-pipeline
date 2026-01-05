{{
    config(
        materialized='table',
        unique_key=['city', 'date']
    )
}}

WITH daily_stats AS (
    SELECT 
        city,
        country,
        DATE(weather_time_local) AS date,
        
        -- Temperature statistics
        ROUND(AVG(temperature)::numeric, 2) AS avg_temperature,
        ROUND(MIN(temperature)::numeric, 2) AS min_temperature,
        ROUND(MAX(temperature)::numeric, 2) AS max_temperature,
        
        -- Wind statistics
        ROUND(AVG(wind_speed)::numeric, 2) AS avg_wind_speed,
        ROUND(MAX(wind_speed)::numeric, 2) AS max_wind_speed,
        
        -- Weather conditions
        MODE() WITHIN GROUP (ORDER BY weather_description) AS most_common_weather,
        
        -- Additional metrics
        ROUND(AVG(humidity)::numeric, 2) AS avg_humidity,
        ROUND(AVG(pressure)::numeric, 2) AS avg_pressure,
        ROUND(AVG(CASE WHEN feelslike IS NOT NULL THEN feelslike END)::numeric, 2) AS avg_feelslike,
        
        -- Data quality
        COUNT(*) AS observation_count,
        MIN(weather_time_local) AS first_observation,
        MAX(weather_time_local) AS last_observation
        
    FROM {{ ref('stg_weather_data') }}
    GROUP BY 
        city,
        country,
        DATE(weather_time_local)
),

temperature_trends AS (
    SELECT 
        city,
        date,
        avg_temperature,
        LAG(avg_temperature) OVER (PARTITION BY city ORDER BY date) AS prev_day_temp,
        avg_temperature - LAG(avg_temperature) OVER (PARTITION BY city ORDER BY date) AS temp_change
    FROM daily_stats
)

SELECT 
    ds.city,
    ds.country,
    ds.date,
    ds.avg_temperature,
    ds.min_temperature,
    ds.max_temperature,
    ds.avg_wind_speed,
    ds.max_wind_speed,
    ds.most_common_weather,
    ds.avg_humidity,
    ds.avg_pressure,
    ds.avg_feelslike,
    ds.observation_count,
    tt.temp_change,
    -- Temperature classification
    CASE 
        WHEN ds.avg_temperature < 0 THEN 'Freezing'
        WHEN ds.avg_temperature < 10 THEN 'Cold'
        WHEN ds.avg_temperature < 20 THEN 'Cool'
        WHEN ds.avg_temperature < 30 THEN 'Warm'
        ELSE 'Hot'
    END AS temperature_category
FROM daily_stats ds
LEFT JOIN temperature_trends tt 
    ON ds.city = tt.city 
    AND ds.date = tt.date
ORDER BY
    ds.city,
    ds.date DESC
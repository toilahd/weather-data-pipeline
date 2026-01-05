{{
    config(
        materialized='incremental',
        unique_key=['city', 'hour']
    )
}}

WITH hourly_data AS (
    SELECT 
        city,
        DATE_TRUNC('hour', weather_time) AS hour,
        
        -- Aggregations
        ROUND(AVG(temperature_c)::numeric, 1) AS avg_temp_c,
        ROUND(MIN(temperature_c)::numeric, 1) AS min_temp_c,
        ROUND(MAX(temperature_c)::numeric, 1) AS max_temp_c,
        
        ROUND(AVG(feels_like_c)::numeric, 1) AS avg_feels_like_c,
        ROUND(AVG(humidity_pct)::numeric, 1) AS avg_humidity,
        ROUND(AVG(pressure_msl)::numeric, 1) AS avg_pressure,
        ROUND(AVG(wind_speed_kmh)::numeric, 1) AS avg_wind_speed,
        ROUND(SUM(precipitation_mm)::numeric, 2) AS total_precipitation,
        
        MODE() WITHIN GROUP (ORDER BY weather_description) AS dominant_weather,
        COUNT(*) AS observation_count
        
    FROM {{ ref('stg_weather_data') }}
    {% if is_incremental() %}
    WHERE DATE_TRUNC('hour', weather_time) > (
        SELECT COALESCE(MAX(hour), '1900-01-01') FROM {{ this }}
    )
    {% endif %}
    GROUP BY 
        city,
        DATE_TRUNC('hour', weather_time)
),

with_lag AS (
    SELECT 
        *,
        -- Hour-over-hour changes
        avg_temp_c - LAG(avg_temp_c) OVER (
            PARTITION BY city ORDER BY hour
        ) AS temp_change_1h,
        
        -- 24-hour rolling average
        ROUND(AVG(avg_temp_c) OVER (
            PARTITION BY city 
            ORDER BY hour 
            ROWS BETWEEN 23 PRECEDING AND CURRENT ROW
        )::numeric, 1) AS temp_24h_avg
        
    FROM hourly_data
)

SELECT 
    {{ dbt_utils.generate_surrogate_key(['city', 'hour']) }} AS hourly_id,
    city,
    hour,
    EXTRACT(DOW FROM hour) AS day_of_week,  -- 0=Sunday, 6=Saturday
    EXTRACT(HOUR FROM hour) AS hour_of_day,
    
    avg_temp_c,
    min_temp_c,
    max_temp_c,
    avg_feels_like_c,
    temp_change_1h,
    temp_24h_avg,
    
    avg_humidity,
    avg_pressure,
    avg_wind_speed,
    total_precipitation,
    dominant_weather,
    
    observation_count,
    CASE 
        WHEN observation_count >= 4 THEN 'Excellent'
        WHEN observation_count >= 2 THEN 'Good'
        ELSE 'Limited'
    END AS data_completeness
    
FROM with_lag
ORDER BY city, hour DESC

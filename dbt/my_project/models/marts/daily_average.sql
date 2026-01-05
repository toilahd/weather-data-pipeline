{{
    config(
        materialized='incremental',
        unique_key=['city', 'date']
    )
}}

WITH daily_aggregates AS (
    SELECT 
        city,
        latitude,
        longitude,
        DATE(weather_time) AS date,
        
        -- Temperature statistics
        ROUND(AVG(temperature_c)::numeric, 1) AS avg_temp_c,
        ROUND(MIN(temperature_c)::numeric, 1) AS min_temp_c,
        ROUND(MAX(temperature_c)::numeric, 1) AS max_temp_c,
        ROUND(MAX(temperature_c) - MIN(temperature_c)::numeric, 1) AS temp_range_c,
        
        ROUND(AVG(feels_like_c)::numeric, 1) AS avg_feels_like_c,
        
        -- Wind statistics
        ROUND(AVG(wind_speed_kmh)::numeric, 1) AS avg_wind_speed,
        ROUND(MAX(wind_speed_kmh)::numeric, 1) AS max_wind_speed,
        
        -- Atmospheric conditions
        ROUND(AVG(humidity_pct)::numeric, 1) AS avg_humidity,
        ROUND(AVG(pressure_msl)::numeric, 1) AS avg_pressure,
        ROUND(AVG(cloud_cover_pct)::numeric, 1) AS avg_cloud_cover,
        ROUND(SUM(precipitation_mm)::numeric, 2) AS total_precipitation,
        
        -- Most common conditions
        MODE() WITHIN GROUP (ORDER BY weather_description) AS dominant_weather,
        
        -- Data quality metrics
        COUNT(*) AS observation_count,
        MIN(weather_time) AS first_obs_time,
        MAX(weather_time) AS last_obs_time,
        
        -- Day/Night distribution
        SUM(CASE WHEN is_day = 1 THEN 1 ELSE 0 END) AS daytime_observations,
        SUM(CASE WHEN is_day = 0 THEN 1 ELSE 0 END) AS nighttime_observations
        
    FROM {{ ref('stg_weather_data') }}
    {% if is_incremental() %}
    WHERE DATE(weather_time) > (SELECT COALESCE(MAX(date), '1900-01-01') FROM {{ this }})
    {% endif %}
    GROUP BY 
        city,
        latitude,
        longitude,
        DATE(weather_time)
),

with_trends AS (
    SELECT 
        *,
        -- Temperature trends
        avg_temp_c - LAG(avg_temp_c) OVER (
            PARTITION BY city ORDER BY date
        ) AS temp_change_from_prev_day,
        
        -- Moving averages (7-day)
        ROUND(AVG(avg_temp_c) OVER (
            PARTITION BY city 
            ORDER BY date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        )::numeric, 1) AS temp_7day_avg,
        
        ROUND(AVG(total_precipitation) OVER (
            PARTITION BY city 
            ORDER BY date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        )::numeric, 2) AS rain_7day_avg
        
    FROM daily_aggregates
),

final AS (
    SELECT 
        {{ dbt_utils.generate_surrogate_key(['city', 'date']) }} AS daily_id,
        city,
        latitude,
        longitude,
        date,
        
        -- Temperature metrics
        avg_temp_c,
        min_temp_c,
        max_temp_c,
        temp_range_c,
        avg_feels_like_c,
        temp_change_from_prev_day,
        temp_7day_avg,
        
        -- Wind metrics
        avg_wind_speed,
        max_wind_speed,
        
        -- Atmospheric metrics
        avg_humidity,
        avg_pressure,
        avg_cloud_cover,
        total_precipitation,
        rain_7day_avg,
        
        -- Weather summary
        dominant_weather,
        
        -- Classification
        CASE 
            WHEN avg_temp_c < 10 THEN 'Cold Day'
            WHEN avg_temp_c < 20 THEN 'Cool Day'
            WHEN avg_temp_c < 25 THEN 'Pleasant Day'
            WHEN avg_temp_c < 30 THEN 'Warm Day'
            ELSE 'Hot Day'
        END AS day_classification,
        
        CASE 
            WHEN total_precipitation > 20 THEN 'Very Rainy'
            WHEN total_precipitation > 10 THEN 'Rainy'
            WHEN total_precipitation > 2 THEN 'Light Rain'
            WHEN total_precipitation > 0 THEN 'Trace Rain'
            ELSE 'Dry'
        END AS precipitation_level,
        
        -- Data quality
        observation_count,
        CASE 
            WHEN observation_count >= 20 THEN 'Complete'
            WHEN observation_count >= 12 THEN 'Good'
            WHEN observation_count >= 6 THEN 'Fair'
            ELSE 'Limited'
        END AS data_quality,
        daytime_observations,
        nighttime_observations,
        first_obs_time,
        last_obs_time
        
    FROM with_trends
)

SELECT * FROM final
ORDER BY city, date DESC
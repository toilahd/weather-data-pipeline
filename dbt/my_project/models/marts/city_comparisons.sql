{{
    config(
        materialized='table'
    )
}}

WITH latest_weather AS (
    SELECT * FROM {{ ref('weather_report') }}
),

city_rankings AS (
    SELECT 
        city,
        temperature_c,
        ROW_NUMBER() OVER (ORDER BY temperature_c DESC) AS hottest_rank,
        ROW_NUMBER() OVER (ORDER BY temperature_c ASC) AS coldest_rank,
        ROW_NUMBER() OVER (ORDER BY humidity_pct DESC) AS most_humid_rank,
        ROW_NUMBER() OVER (ORDER BY wind_speed_kmh DESC) AS windiest_rank,
        ROW_NUMBER() OVER (ORDER BY precipitation_mm DESC) AS rainiest_rank
    FROM latest_weather
),

aggregated_stats AS (
    SELECT 
        ROUND(AVG(temperature_c)::numeric, 1) AS vietnam_avg_temp,
        ROUND(MAX(temperature_c)::numeric, 1) AS vietnam_max_temp,
        ROUND(MIN(temperature_c)::numeric, 1) AS vietnam_min_temp,
        ROUND(AVG(humidity_pct)::numeric, 1) AS vietnam_avg_humidity
    FROM latest_weather
)

SELECT 
    lw.city,
    lw.observation_time,
    lw.temperature_c,
    lw.temperature_c - agg.vietnam_avg_temp AS temp_vs_national_avg,
    lw.humidity_pct,
    lw.humidity_pct - agg.vietnam_avg_humidity AS humidity_vs_national_avg,
    lw.wind_speed_kmh,
    lw.precipitation_mm,
    lw.comfort_level,
    
    -- Rankings
    cr.hottest_rank,
    cr.coldest_rank,
    cr.most_humid_rank,
    cr.windiest_rank,
    cr.rainiest_rank,
    
    -- Highlights
    CASE WHEN cr.hottest_rank = 1 THEN TRUE ELSE FALSE END AS is_hottest_city,
    CASE WHEN cr.coldest_rank = 1 THEN TRUE ELSE FALSE END AS is_coldest_city,
    CASE WHEN cr.most_humid_rank = 1 THEN TRUE ELSE FALSE END AS is_most_humid_city,
    CASE WHEN cr.windiest_rank = 1 THEN TRUE ELSE FALSE END AS is_windiest_city,
    
    -- National context
    agg.vietnam_avg_temp,
    agg.vietnam_max_temp,
    agg.vietnam_min_temp,
    agg.vietnam_avg_humidity
    
FROM latest_weather lw
CROSS JOIN aggregated_stats agg
LEFT JOIN city_rankings cr ON lw.city = cr.city
ORDER BY lw.temperature_c DESC

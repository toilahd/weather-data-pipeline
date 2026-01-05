{{
    config(
        materialized='view'
    )
}}

WITH daily_temps AS (
    SELECT 
        city,
        date,
        avg_temp_c,
        min_temp_c,
        max_temp_c
    FROM {{ ref('daily_average') }}
),

rolling_averages AS (
    SELECT 
        city,
        date,
        avg_temp_c,
        
        -- 7-day rolling average
        ROUND(AVG(avg_temp_c) OVER (
            PARTITION BY city 
            ORDER BY date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        )::numeric, 2) AS avg_temp_7d,
        
        -- 30-day rolling average
        ROUND(AVG(avg_temp_c) OVER (
            PARTITION BY city 
            ORDER BY date 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        )::numeric, 2) AS avg_temp_30d,
        
        -- Temperature volatility (standard deviation over 7 days)
        ROUND(STDDEV(avg_temp_c) OVER (
            PARTITION BY city 
            ORDER BY date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        )::numeric, 2) AS temp_volatility_7d,
        
        -- Count of days in rolling window
        COUNT(*) OVER (
            PARTITION BY city 
            ORDER BY date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS days_in_window
        
    FROM daily_temps
)

SELECT 
    city,
    date,
    avg_temp_c AS current_temp,
    avg_temp_7d,
    avg_temp_30d,
    temp_volatility_7d,
    
    -- Temperature trend indicator
    CASE 
        WHEN avg_temp_c > avg_temp_7d + 2 THEN 'Warming'
        WHEN avg_temp_c < avg_temp_7d - 2 THEN 'Cooling'
        ELSE 'Stable'
    END AS trend_7d,
    
    -- Anomaly detection
    CASE 
        WHEN temp_volatility_7d > 5 THEN 'High Volatility'
        WHEN temp_volatility_7d > 3 THEN 'Moderate Volatility'
        ELSE 'Stable'
    END AS stability_indicator
    
FROM rolling_averages
WHERE days_in_window >= 7  -- Only show trends when we have enough data
ORDER BY city, date DESC

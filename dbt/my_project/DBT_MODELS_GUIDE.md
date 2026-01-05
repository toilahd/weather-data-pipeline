# DBT Models - Weather Data Pipeline

## Overview

Redesigned DBT model architecture optimized for Vietnamese weather data analytics with focus on hourly tracking, daily trends, and city comparisons.

## Model Architecture

```
raw_weather_data (PostgreSQL)
    ↓
┌───────────────────────────────────────┐
│   STAGING LAYER                       │
│   stg_weather_data                    │
│   - Deduplication                     │
│   - Unit conversions (C/F, km/mi)    │
│   - Data quality checks               │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│   MART LAYER                          │
│                                       │
│   weather_report                      │
│   - Latest conditions per city        │
│   - Derived metrics                   │
│   - Comfort classifications           │
│                                       │
│   daily_average                       │
│   - Daily aggregations                │
│   - 7-day trends                      │
│   - Precipitation totals              │
│                                       │
│   hourly_trends                       │
│   - Hourly aggregations               │
│   - 24-hour rolling averages          │
│   - Hour-over-hour changes            │
│                                       │
│   city_comparisons                    │
│   - Cross-city rankings               │
│   - National averages                 │
│   - Comparative metrics               │
└───────────────────────────────────────┘
```

## Model Details

### Staging Layer

#### `stg_weather_data`
**Purpose:** Clean, deduplicate, and standardize raw weather data

**Materialization:** Incremental (based on `inserted_at`)

**Key Features:**
- Deduplication by city + time (keeps latest insert)
- Unit conversions:
  - Celsius ↔ Fahrenheit
  - km/h ↔ mph
- Data quality flag (`is_valid_record`)
- Surrogate key generation

**Fields Added:**
- `weather_id` - Surrogate key
- `temperature_f`, `feels_like_f` - Fahrenheit conversions
- `wind_speed_mph` - Wind speed in miles per hour
- `is_valid_record` - Quality flag

---

### Mart Layer

#### `weather_report`
**Purpose:** Current weather snapshot for all cities (latest observation)

**Materialization:** Table (full refresh)

**Use Case:** Real-time dashboards, current conditions display

**Key Metrics:**
- Temperature (C/F) and feels-like
- Wind speed, direction (cardinal + degrees)
- Precipitation status
- Comfort level classification
- Data freshness (`minutes_since_load`)

**Derived Fields:**
- `comfort_level`: Cold | Cool | Comfortable | Warm | Hot
- `wind_strength`: Calm | Light | Moderate | Strong | Very Strong
- `rain_status`: No Rain | Light Rain | Moderate Rain | Heavy Rain
- `wind_direction_cardinal`: N, NE, E, SE, S, SW, W, NW

**Example Query:**
```sql
SELECT 
    city,
    temperature_c,
    comfort_level,
    wind_speed_kmh,
    rain_status
FROM dev.weather_report
ORDER BY temperature_c DESC;
```

---

#### `daily_average`
**Purpose:** Daily aggregated statistics with trends

**Materialization:** Incremental (based on date)

**Use Case:** Historical analysis, weekly trends, day-over-day comparisons

**Key Metrics:**
- Temperature: avg, min, max, range
- Wind: average and max speed
- Precipitation: daily total, 7-day average
- Humidity, pressure, cloud cover averages
- Observation count and data quality

**Derived Fields:**
- `temp_change_from_prev_day`: Day-over-day temperature delta
- `temp_7day_avg`: 7-day rolling average
- `rain_7day_avg`: 7-day precipitation average
- `day_classification`: Cold Day | Cool Day | Pleasant Day | Warm Day | Hot Day
- `data_quality`: Complete (20+ obs) | Good (12-19) | Fair (6-11) | Limited (<6)

**Example Query:**
```sql
SELECT 
    city,
    date,
    avg_temp_c,
    temp_7day_avg,
    total_precipitation,
    data_quality
FROM dev.daily_average
WHERE city = 'Ha Noi'
ORDER BY date DESC
LIMIT 7;
```

---

#### `hourly_trends`
**Purpose:** Hourly aggregations with rolling windows

**Materialization:** Incremental (based on hour)

**Use Case:** Intraday analysis, hourly patterns, short-term forecasting

**Key Metrics:**
- Hourly temperature aggregations
- Hour-over-hour changes
- 24-hour rolling averages
- Hourly precipitation totals
- Observation completeness per hour

**Derived Fields:**
- `hour_of_day`: 0-23 (for time-of-day analysis)
- `day_of_week`: 0=Sunday, 6=Saturday
- `temp_change_1h`: Hour-over-hour temperature change
- `temp_24h_avg`: 24-hour rolling average
- `data_completeness`: Excellent (4+ obs) | Good (2-3) | Limited (<2)

**Example Query:**
```sql
SELECT 
    city,
    hour,
    avg_temp_c,
    temp_change_1h,
    temp_24h_avg
FROM dev.hourly_trends
WHERE city = 'Ho Chi Minh'
  AND hour >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY hour DESC;
```

---

#### `city_comparisons`
**Purpose:** Comparative analysis across all cities

**Materialization:** Table (full refresh)

**Use Case:** City rankings, national benchmarks, comparative dashboards

**Key Metrics:**
- Temperature vs national average
- City rankings (hottest, coldest, most humid, windiest, rainiest)
- Boolean flags for extremes
- National statistics (avg, min, max)

**Derived Fields:**
- `hottest_rank`: 1 (hottest) to 8 (coldest)
- `temp_vs_national_avg`: Temperature difference from Vietnam average
- `is_hottest_city`, `is_coldest_city`, `is_most_humid_city`, etc.
- `vietnam_avg_temp`, `vietnam_max_temp`, `vietnam_min_temp`

**Example Query:**
```sql
SELECT 
    city,
    temperature_c,
    hottest_rank,
    temp_vs_national_avg,
    is_hottest_city
FROM dev.city_comparisons
ORDER BY temperature_c DESC;
```

---

## Data Quality

### Staging Layer Checks
- Removes duplicates (keeps latest by `inserted_at`)
- Validates required fields (temperature, humidity, windspeed)
- Sets `is_valid_record` flag

### Mart Layer Indicators
- **daily_average**: `data_quality` based on observation count
- **hourly_trends**: `data_completeness` based on observations per hour
- **weather_report**: `minutes_since_load` for freshness

---

## Running DBT Models

### Full Refresh
```bash
# Run all models
docker compose run dbt run

# Run specific layer
docker compose run dbt run --models staging
docker compose run dbt run --models marts
```

### Incremental Updates
```bash
# Only process new data (for incremental models)
docker compose run dbt run --models stg_weather_data
docker compose run dbt run --models daily_average
docker compose run dbt run --models hourly_trends
```

### Testing
```bash
# Run all tests
docker compose run dbt test

# Test specific model
docker compose run dbt test --models weather_report
```

### Documentation
```bash
# Generate docs
docker compose run dbt docs generate

# Serve docs locally
docker compose run dbt docs serve --port 8080
```

---

## Incremental Strategy

### `stg_weather_data`
- **Trigger:** New records with `inserted_at` > last processed
- **Unique Key:** `[city, weather_time]`
- **Strategy:** Append new, update existing on conflict

### `daily_average`
- **Trigger:** New dates after last processed date
- **Unique Key:** `[city, date]`
- **Strategy:** Calculate for new dates only

### `hourly_trends`
- **Trigger:** New hours after last processed hour
- **Unique Key:** `[city, hour]`
- **Strategy:** Aggregate new hours only

---

## Key Improvements Over Previous Design

1. **Unit Conversions:** Added Fahrenheit and mph for international use
2. **Incremental Processing:** Optimized for hourly data ingestion
3. **Data Quality Metrics:** Added completeness and freshness indicators
4. **Hourly Granularity:** New `hourly_trends` model for intraday analysis
5. **City Comparisons:** New model for cross-city analytics
6. **Rolling Windows:** 7-day and 24-hour moving averages
7. **Better Classifications:** More granular comfort/wind/rain categories
8. **National Benchmarks:** Vietnam-wide statistics for context

---

## Usage Examples

### Dashboard Queries

**Current Weather Map:**
```sql
SELECT 
    city, latitude, longitude, temperature_c, 
    comfort_level, observation_time
FROM dev.weather_report;
```

**Weekly Temperature Trend:**
```sql
SELECT 
    date, city, avg_temp_c, temp_7day_avg,
    temp_change_from_prev_day
FROM dev.daily_average
WHERE date >= CURRENT_DATE - 7
ORDER BY city, date;
```

**Hourly Today:**
```sql
SELECT 
    hour_of_day, city, avg_temp_c, 
    total_precipitation
FROM dev.hourly_trends
WHERE DATE(hour) = CURRENT_DATE
ORDER BY city, hour;
```

**City Rankings:**
```sql
SELECT 
    city, temperature_c, hottest_rank,
    vietnam_avg_temp,
    is_hottest_city
FROM dev.city_comparisons
ORDER BY hottest_rank;
```

---

## Future Enhancements

- Add weather alerts model (extreme conditions)
- Create monthly/seasonal aggregations
- Add predictive features (temperature forecasting)
- Implement anomaly detection
- Add weather pattern recognition

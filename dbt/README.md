# dbt Models Documentation

## Overview
This dbt project transforms raw weather data into analytics-ready models with comprehensive data quality tests.

## Project Structure

```
models/
├── sources/
│   └── sources.yml          # Source definitions and tests
├── staging/
│   ├── stg_weather_data.sql # Cleaned, deduplicated data
│   └── schema.yml           # Staging model tests
└── marts/
    ├── daily_average.sql    # Daily aggregations
    ├── weather_report.sql   # Current weather snapshot
    ├── weather_trends.sql   # Trend analysis
    └── schema.yml          # Mart model tests
```

## Models

### Staging Layer

#### `stg_weather_data`
**Purpose:** Clean and deduplicate raw weather data

**Transformations:**
- Deduplication by city and time
- Timezone normalization
- Incremental loading for efficiency
- Includes all weather metrics

**Materialization:** Incremental (updates only new data)

**Key Features:**
- Handles duplicate records
- Preserves data lineage
- Efficient incremental processing

### Marts Layer

#### `daily_average`
**Purpose:** Daily weather statistics by city

**Metrics:**
- Temperature: avg, min, max
- Wind: avg, max
- Humidity, pressure averages
- Day-over-day temperature changes
- Temperature categorization

**Materialization:** Table

**Business Value:**
- Historical trend analysis
- Climate pattern identification
- Temperature volatility tracking

#### `weather_report`
**Purpose:** Latest weather conditions with context

**Features:**
- Most recent observation per city
- Temperature feel context
- Wind categorization
- UV risk levels
- Visibility categorization
- Surrogate key generation

**Materialization:** Table

**Use Cases:**
- Real-time dashboards
- Weather alerts
- Current conditions display

#### `weather_trends`
**Purpose:** Rolling averages and trend indicators

**Analytics:**
- 7-day rolling average
- 30-day rolling average
- Temperature volatility
- Trend direction (warming/cooling/stable)
- Anomaly detection

**Materialization:** View (for real-time calculations)

**Insights:**
- Climate trends
- Seasonal patterns
- Weather anomalies

## Data Quality Tests

### Source Tests
- **Uniqueness**: ID field must be unique
- **Not Null**: Required fields validated
- **Range Checks**: 
  - Temperature: -100°C to 60°C
  - Wind speed: 0 to 200 km/h
  - Humidity: 0% to 100%
- **Freshness**: Alerts if data older than 6 hours

### Model Tests
- **Referential Integrity**: Foreign key relationships
- **Accepted Values**: Categorical field validation
- **Custom Tests**: Business logic validation

## Running dbt

### Basic Commands
```bash
# Install dependencies
dbt deps

# Run all models
dbt run

# Run specific model
dbt run --select stg_weather_data

# Run tests
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

### Model Selection
```bash
# Run staging models only
dbt run --select staging

# Run marts only
dbt run --select marts

# Run specific model and downstream
dbt run --select weather_report+
```

## Configuration

### profiles.yml
```yaml
my_project:
  target: dev
  outputs:
    dev:
      type: postgres
      host: "{{ env_var('DB_HOST') }}"
      port: "{{ env_var('DB_PORT') }}"
      user: "{{ env_var('DB_USER') }}"
      password: "{{ env_var('DB_PASSWORD') }}"
      database: "{{ env_var('DB_NAME') }}"
      schema: dev
```

## Best Practices

1. **Incremental Models**: Use for large datasets
2. **Testing**: All models should have tests
3. **Documentation**: Document all columns
4. **Naming**: Clear, descriptive model names
5. **Materialization**: Choose based on use case
   - Views: For simple transformations
   - Tables: For complex aggregations
   - Incremental: For large, growing datasets

## Performance Optimization

- Incremental loading reduces processing time
- Indexed source tables
- Efficient window functions
- Materialized tables for dashboards

## Data Lineage

```
raw_weather_data (source)
    ↓
stg_weather_data (staging)
    ↓
├── daily_average (mart)
├── weather_report (mart)
└── weather_trends (mart)
```

## Testing Strategy

1. **Source Tests**: Validate raw data quality
2. **Model Tests**: Ensure transformation accuracy
3. **Freshness Tests**: Alert on stale data
4. **Business Logic**: Custom tests for rules

## Troubleshooting

### Common Issues

**Issue**: Models not updating
```bash
# Force full refresh
dbt run --full-refresh
```

**Issue**: Test failures
```bash
# Run tests with details
dbt test --store-failures
```

**Issue**: Performance slow
```bash
# Use incremental materialization
# Add indexes to source tables
# Limit data in development
```

## Extending the Project

### Adding New Models
1. Create SQL file in appropriate folder
2. Add tests in schema.yml
3. Document columns and purpose
4. Run and validate

### Adding Custom Tests
1. Create test in `tests/` folder
2. Reference in schema.yml
3. Run with `dbt test`

## Dependencies

Add to `packages.yml`:
```yaml
packages:
  - package: dbt-labs/dbt_utils
    version: 1.1.1
```

Then run: `dbt deps`

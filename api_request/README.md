# API Request Module

## Overview
This module handles all interactions with the WeatherStack API, including data fetching, validation, and database operations.

## Components

### 1. Configuration (`config.py`)
Centralized configuration management with environment variable support.

**Key Features:**
- API configuration (URL, key, timeout, retries)
- Database connection settings
- Multi-city support (8 cities by default)
- Data quality thresholds
- Configuration validation

**Usage:**
```python
from config import Config

# Access configuration
api_key = Config.API_KEY
db_url = Config.get_database_url()

# Validate configuration
Config.validate()
```

### 2. API Client (`api_request.py`)
Robust API client with retry logic and error handling.

**Features:**
- Automatic retry on connection failures (3 attempts)
- Exponential backoff
- Connection pooling
- Rate limiting protection
- Multi-city batch fetching

**Usage:**
```python
from api_request import WeatherAPIClient

client = WeatherAPIClient()

# Fetch single city
data = client.fetch_city_weather("New York")

# Fetch multiple cities
results = client.fetch_multiple_cities()
```

### 3. Data Validation (`validators.py`)
Comprehensive data validation before database insertion.

**Validations:**
- Temperature range: -100°C to 60°C
- Wind speed: 0 to 200 km/h
- Humidity: 0% to 100%
- Coordinate bounds
- Required field presence
- Data type validation

**Usage:**
```python
from validators import WeatherDataValidator

is_valid, errors = WeatherDataValidator.validate_weather_data(data)
if is_valid:
    sanitized = WeatherDataValidator.sanitize_data(data)
```

### 4. Database Operations (`insert_records.py`)
Enhanced database handler with connection pooling.

**Features:**
- Connection pooling (1-10 connections)
- Batch insert support
- Upsert logic (ON CONFLICT handling)
- Data quality audit logging
- Enhanced schema with additional metrics
- Database statistics tracking

**Schema:**
- `dev.raw_weather_data` - Main weather data table
- `dev.data_quality_audit` - Failed validation logs

**Usage:**
```python
from insert_records import WeatherDatabase

db = WeatherDatabase()
db.create_tables()

# Insert single record
success = db.insert_weather_record(weather_data)

# Batch insert
successful, failed = db.insert_batch(data_list)

# Get statistics
stats = db.get_stats()
```

### 5. Logging (`logger_config.py`)
Structured logging with file and console handlers.

**Features:**
- Dual handlers (console + file)
- Different log levels per handler
- Timestamped log files
- Detailed formatting with file/line numbers

### 6. Exception Handling (`exceptions.py`)
Custom exceptions for better error handling.

**Exception Types:**
- `APIConnectionError` - API connection failures
- `APIResponseError` - Invalid API responses
- `DatabaseConnectionError` - Database issues
- `DataValidationError` - Validation failures
- `ConfigurationError` - Configuration problems

### 7. Performance Monitoring (`metrics.py`)
Track and measure pipeline performance.

**Metrics Tracked:**
- API call success rate
- Database insert success rate
- Average operation duration
- Validation failure count

**Usage:**
```python
from metrics import PerformanceMonitor

monitor = PerformanceMonitor()
monitor.record_api_call(success=True, duration=1.5)
monitor.log_summary()
```

### 8. Unit Tests (`test_pipeline.py`)
Comprehensive test suite covering all components.

**Test Coverage:**
- Data validation logic
- API client behavior
- Configuration handling
- Mock API responses
- Error scenarios

**Run Tests:**
```bash
cd api-request
pytest test_pipeline.py -v --cov=.
```

## Environment Variables

Required variables in `.env`:
```env
api_key=YOUR_WEATHERSTACK_API_KEY
DB_NAME=db
DB_USER=db_user
DB_PASSWORD=db_password
DB_HOST=db
DB_PORT=5432
```

## Error Handling Strategy

1. **Retry Logic**: API calls retry 3 times with 5-second delays
2. **Validation**: Data validated before insertion
3. **Audit Trail**: Failed validations logged to audit table
4. **Graceful Degradation**: Pipeline continues on single city failure
5. **Detailed Logging**: All errors logged with context

## Performance Optimization

- Connection pooling reduces overhead
- Batch operations for multiple cities
- Incremental data loading
- Indexed database queries
- Efficient deduplication

## Best Practices

1. Always validate configuration before running
2. Monitor validation failure rates
3. Review audit logs regularly
4. Use connection pooling for production
5. Set appropriate retry limits
6. Monitor API rate limits

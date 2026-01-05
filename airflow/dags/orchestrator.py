"""
Enhanced Airflow DAGs for Weather Data Pipeline

Two DAGs:
1. weather_hourly_pipeline - Runs every hour for current weather
2. weather_historical_backfill - One-time/manual run for historical data
"""
from airflow import DAG
from datetime import datetime, timedelta
try:
    from airflow.providers.standard.operators.python import PythonOperator
except ImportError:
    from airflow.operators.python import PythonOperator
try:
    from airflow.providers.docker.operators.docker import DockerOperator
except ImportError:
    from airflow.operators.docker_operator import DockerOperator
from docker.types import Mount
import sys
import logging

sys.path.append('/opt/airflow/api_request')
logger = logging.getLogger(__name__)


# =============================================================================
# TASK FUNCTIONS
# =============================================================================

def extract_current_weather():
    """Extract current weather from Open-Meteo API for all cities"""
    from config import Config
    from api_client import OpenMeteoAPIClient
    from insert_records import WeatherDatabase
    
    logger.info("Starting current weather extraction")
    db = WeatherDatabase()
    db.create_tables()
    client = OpenMeteoAPIClient()
    
    success, failed = 0, 0
    for city in Config.CITIES:
        try:
            logger.info(f"Fetching {city['name']}")
            data = client.fetch_current_weather(city)
            if data and db.insert_weather_record(city, data):
                success += 1
                logger.info(f"✓ {city['name']}")
            else:
                failed += 1
                logger.warning(f"✗ {city['name']} - validation failed")
        except Exception as e:
            failed += 1
            logger.error(f"✗ {city['name']}: {e}")
    
    logger.info(f"Extraction complete: {success} successful, {failed} failed")
    
    if success == 0:
        raise ValueError("All city extractions failed")
    
    return {"success": success, "failed": failed}


def extract_historical_weather(**context):
    """Extract historical weather data for specified date range"""
    from config import Config
    from api_client import OpenMeteoAPIClient
    from insert_records import WeatherDatabase
    from datetime import datetime as dt
    
    # Get date range from DAG params
    params = context.get('params', {})
    start_date = params.get('start_date', (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
    end_date = params.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    logger.info(f"Historical extraction: {start_date} to {end_date}")
    
    db = WeatherDatabase()
    db.create_tables()
    client = OpenMeteoAPIClient()
    
    success, failed, total_records = 0, 0, 0
    for city in Config.CITIES:
        try:
            logger.info(f"Fetching historical data for {city['name']}")
            data = client.fetch_historical_weather(city, start_date, end_date)
            
            if data and 'daily' in data:
                # Historical API returns daily aggregates
                daily = data['daily']
                dates = daily.get('time', [])
                
                # Insert each day's data as a record
                for i, date_str in enumerate(dates):
                    # Create a record for each day with available data
                    # Add noon timestamp to the date
                    timestamp = f"{date_str}T12:00:00"
                    historical_record = {
                        'current': {
                            'time': timestamp,
                            'temperature_2m': daily.get('temperature_2m_max', [None])[i],
                            'apparent_temperature': daily.get('temperature_2m_min', [None])[i],  # Using min as proxy
                            'relative_humidity_2m': 50,  # Default - not available in daily
                            'precipitation': daily.get('precipitation_sum', [None])[i],
                            'weather_code': 0,  # Default - not available
                            'cloud_cover': 0,  # Default - not available
                            'pressure_msl': 1013,  # Default - not available
                            'wind_speed_10m': 0,  # Default - not available
                            'wind_direction_10m': 0,  # Default - not available
                            'is_day': 1  # Default - daytime
                        }
                    }
                    
                    if db.insert_weather_record(city, historical_record):
                        total_records += 1
                
                success += 1
                logger.info(f"✓ {city['name']} - inserted {len(dates)} historical records")
            else:
                failed += 1
                logger.warning(f"✗ {city['name']} - no data returned")
        except Exception as e:
            failed += 1
            logger.error(f"✗ {city['name']}: {e}")
    
    logger.info(f"Historical extraction: {success} cities successful, {failed} failed, {total_records} total records inserted")
    return {"success": success, "failed": failed, "total_records": total_records, "start_date": start_date, "end_date": end_date}


def validate_data_quality(**context):
    """Validate data quality after extraction"""
    import psycopg2
    from config import Config
    
    dag_id = context['dag'].dag_id
    is_historical = 'historical' in dag_id
    interval = '24 hours' if is_historical else '2 hours'
    
    try:
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            port=Config.DB_PORT
        )
        cursor = conn.cursor()
        
        # Check recent data
        cursor.execute(f"""
            SELECT COUNT(*) FROM dev.raw_weather_data 
            WHERE inserted_at > NOW() - INTERVAL '{interval}'
        """)
        recent_count = cursor.fetchone()[0]
        
        logger.info(f"Found {recent_count} records in last {interval}")
        
        if recent_count == 0:
            raise ValueError(f"No data in last {interval}")
        
        # Per-city stats
        cursor.execute(f"""
            SELECT city, COUNT(*), MAX(time) 
            FROM dev.raw_weather_data 
            WHERE inserted_at > NOW() - INTERVAL '{interval}'
            GROUP BY city ORDER BY city
        """)
        
        for city, count, latest in cursor.fetchall():
            logger.info(f"  {city}: {count} records, latest: {latest}")
        
        cursor.close()
        conn.close()
        
        return {"recent_records": recent_count}
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise


def cleanup_old_data():
    """Remove data older than 90 days"""
    import psycopg2
    from config import Config
    
    try:
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            port=Config.DB_PORT
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM dev.raw_weather_data 
            WHERE inserted_at < NOW() - INTERVAL '90 days'
        """)
        deleted = cursor.rowcount
        conn.commit()
        
        logger.info(f"Cleaned up {deleted} old records")
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")


# =============================================================================
# DAG 1: HOURLY CURRENT WEATHER PIPELINE
# =============================================================================

hourly_dag = DAG(
    dag_id="weather_hourly_pipeline",
    default_args={
        'owner': 'data-engineering',
        'start_date': datetime(2026, 1, 5),
        'retries': 3,
        'retry_delay': timedelta(minutes=5),
        'catchup': False,
    },
    description='Fetch current weather every hour for all cities',
    schedule='0 * * * *',  # Every hour
    max_active_runs=1,
    tags=['weather', 'hourly', 'production']
)

with hourly_dag:
    extract = PythonOperator(
        task_id='extract_current_weather',
        python_callable=extract_current_weather
    )
    
    validate = PythonOperator(
        task_id='validate_data_quality',
        python_callable=validate_data_quality
    )
    
    dbt_run = DockerOperator(
        task_id='run_dbt_transformations',
        image='ghcr.io/dbt-labs/dbt-postgres:1.9.latest',
        command=['-c', 'cd /dbt/my_project && dbt deps && dbt run'],
        entrypoint='bash',
        docker_url='unix://var/run/docker.sock',
        network_mode='weather-data-pipeline_my-network',
        auto_remove='success',
        mounts=[
            Mount(source='/home/toilahd/workspace/weather-data-pipeline/dbt/my_project', target='/dbt/my_project', type='bind'),
            Mount(source='/home/toilahd/workspace/weather-data-pipeline/dbt', target='/root/.dbt', type='bind')
        ],
        environment={'DBT_PROFILES_DIR': '/root/.dbt'},
        mount_tmp_dir=False
    )
    
    extract >> validate >> dbt_run


# =============================================================================
# DAG 2: HISTORICAL DATA BACKFILL PIPELINE
# =============================================================================

historical_dag = DAG(
    dag_id="weather_historical_backfill",
    default_args={
        'owner': 'data-engineering',
        'start_date': datetime(2026, 1, 5),
        'retries': 2,
        'retry_delay': timedelta(minutes=10),
        'catchup': False,
    },
    description='One-time historical weather data backfill',
    schedule=None,  # Manual trigger only
    max_active_runs=1,
    tags=['weather', 'historical', 'backfill', 'manual'],
    params={
        'start_date': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
        'end_date': datetime.now().strftime('%Y-%m-%d')
    }
)

with historical_dag:
    extract_hist = PythonOperator(
        task_id='extract_historical_weather',
        python_callable=extract_historical_weather
    )
    
    validate_hist = PythonOperator(
        task_id='validate_data_quality',
        python_callable=validate_data_quality
    )
    
    dbt_run_hist = DockerOperator(
        task_id='run_dbt_transformations',
        image='ghcr.io/dbt-labs/dbt-postgres:1.9.latest',
        command=['-c', 'cd /dbt/my_project && dbt deps && dbt run'],
        entrypoint='bash',
        docker_url='unix://var/run/docker.sock',
        network_mode='weather-data-pipeline_my-network',
        auto_remove='success',
        mounts=[
            Mount(source='/home/toilahd/workspace/weather-data-pipeline/dbt/my_project', target='/dbt/my_project', type='bind'),
            Mount(source='/home/toilahd/workspace/weather-data-pipeline/dbt', target='/root/.dbt', type='bind')
        ],
        environment={'DBT_PROFILES_DIR': '/root/.dbt'},
        mount_tmp_dir=False
    )
    
    cleanup = PythonOperator(
        task_id='cleanup_old_data',
        python_callable=cleanup_old_data,
        trigger_rule='all_done'
    )
    
    extract_hist >> validate_hist >> dbt_run_hist >> cleanup

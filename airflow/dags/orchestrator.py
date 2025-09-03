from datetime import timedelta, datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys

# Add custom path
sys.path.append('/opt/airflow/api-request')

def safe_main_callable():
    from insert_records import main
    return main()

default_args = {
    'description': 'A DAG to orchestrate weather API calls',
    'start_date': datetime(2025, 9, 3),  # datetime object
}

dag = DAG(
    dag_id="weather_api_orchestrator",
    default_args=default_args,
    schedule=timedelta(minutes=1),  
    catchup=False,  # moved here
)

with dag:
    task1 = PythonOperator(
        task_id="call_weather_api",
        python_callable=safe_main_callable,
    )

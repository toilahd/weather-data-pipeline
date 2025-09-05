from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
import sys

sys.path.append('/opt/airflow/api-request')

def callable_main():
    from insert_records import main
    main()


default_args={
    'description':'A DAG to orchestrate weather data pipeline',
    'start_date':datetime(2025, 9, 4),
    'catchup':False,
}

dag = DAG(
    dag_id="orchestrator_dag",
    default_args=default_args,
    schedule=timedelta(minutes=1)
)

with dag:
    task1 = PythonOperator(
        task_id="weather_dag_orchestrator",
        python_callable=callable_main
    )
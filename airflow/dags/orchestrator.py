from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount
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
    dag_id="weather-apit-orchestrator_dag",
    default_args=default_args,
    schedule=timedelta(minutes=1)
)

with dag:
    task1 = PythonOperator(
        task_id="weather_dag_orchestrator",
        python_callable=callable_main
    )
    
    task2 = DockerOperator(
        task_id='transform_data_task',
        image='ghcr.io/dbt-labs/dbt-postgres:1.9.latest',
        command='run',
        working_dir='/usr/app/',
        mounts=[
            Mount(source='/home/toilahd/workspace/weather-data-pipeline/dbt/my_project', target='/usr/app', type='bind'),
            Mount(source='/home/toilahd/workspace/weather-data-pipeline/dbt/profiles.yml', target='/root/.dbt/profiles.yml', type='bind')
        ],
        network_mode='weather-data-pipeline_my-network',
        docker_url='unix://var/run/docker.sock',
        auto_remove='success'
    )
    
    task1 >> task2
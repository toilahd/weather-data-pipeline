CREATE ROLE airflow LOGIN PASSWORD 'airflow';
CREATE DATABASE airflow_db OWNER airflow;

\connect airflow_db;

GRANT ALL PRIVILEGES ON DATABASE airflow_db TO airflow;
GRANT ALL ON SCHEMA public TO airflow;
ALTER SCHEMA public OWNER TO airflow;

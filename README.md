# Weather Data Pipeline project.
*A hands-on project to practice Postgres, DBT, Airflow and Docker.*

## Overview
This project is a simple ETL pipeline that collects **weather data** from WeatherStackAPI, stores in **Postgres**, cleans/transforms the data using **DBT**, and schedules the workflow with **Airflow**, all containerized in **Docker**.
## Tech Stack  
- **Weatherstack API** → Data source (JSON weather data).  
- **PostgreSQL** → Stores raw and transformed weather data.  
- **DBT** → Cleans & transforms the raw data into analytics tables.  
- **Airflow** → Orchestrates the pipeline (extract → load → transform).  
- **Docker Compose** → Runs everything in containers.   
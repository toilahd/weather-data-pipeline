## Makefile for Weather Data Pipeline

.PHONY: help setup start stop restart logs clean test lint format dbt-run dbt-test

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup:  ## Initial setup - create .env file template
	@echo "Creating .env template..."
	@if [ ! -f .env ]; then \
		echo "api_key=YOUR_WEATHERSTACK_API_KEY" > .env; \
		echo "DB_NAME=db" >> .env; \
		echo "DB_USER=db_user" >> .env; \
		echo "DB_PASSWORD=db_password" >> .env; \
		echo "DB_HOST=db" >> .env; \
		echo "DB_PORT=5432" >> .env; \
		echo ".env file created. Please update with your API key."; \
	else \
		echo ".env file already exists."; \
	fi

install:  ## Install Python dependencies
	pip install -r api-request/requirements.txt
	pip install pytest pytest-cov black flake8 pylint

start:  ## Start all containers
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Services started!"
	@echo "Airflow: http://localhost:8000"
	@echo "Superset: http://localhost:8088"

stop:  ## Stop all containers
	docker-compose down

restart:  ## Restart all containers
	docker-compose restart

logs:  ## Show logs from all containers
	docker-compose logs -f

logs-airflow:  ## Show Airflow logs
	docker-compose logs -f af

logs-db:  ## Show database logs
	docker-compose logs -f db

clean:  ## Clean up containers and volumes
	docker-compose down -v
	rm -rf postgres/data
	rm -rf dbt/logs

test:  ## Run unit tests
	cd api-request && pytest test_pipeline.py -v --cov=.

lint:  ## Run linting checks
	flake8 api-request/ --max-line-length=120 --exclude=__pycache__
	pylint api-request/*.py --max-line-length=120 || true

format:  ## Format code with black
	black api-request/

dbt-run:  ## Run dbt models
	docker-compose run --rm dbt run

dbt-test:  ## Run dbt tests
	docker-compose run --rm dbt test

dbt-docs:  ## Generate and serve dbt documentation
	docker-compose run --rm dbt docs generate
	docker-compose run --rm dbt docs serve

db-shell:  ## Open PostgreSQL shell
	docker exec -it postgres psql -U db_user -d db

airflow-shell:  ## Open Airflow container shell
	docker exec -it airflow bash

check-health:  ## Check health of all services
	@echo "Checking service health..."
	@docker-compose ps
	@echo "\nDatabase connection:"
	@docker exec postgres pg_isready -U db_user || echo "Database not ready"

backup-db:  ## Backup database
	@mkdir -p backups
	docker exec postgres pg_dump -U db_user db > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Database backed up to backups/"

stats:  ## Show pipeline statistics
	@echo "Pipeline Statistics:"
	@docker exec postgres psql -U db_user -d db -c "SELECT COUNT(*) as total_records, COUNT(DISTINCT city) as unique_cities, MIN(inserted_at) as first_record, MAX(inserted_at) as last_record FROM dev.raw_weather_data;"

ci:  ## Run CI checks locally
	make lint
	make test
	make dbt-test

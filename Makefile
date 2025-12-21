.PHONY: help build up down restart logs clean init-db test

help:
	@echo "MTBBS Linux - Available Commands:"
	@echo "  make build     - Build Docker images"
	@echo "  make up        - Start all services"
	@echo "  make down      - Stop all services"
	@echo "  make restart   - Restart all services"
	@echo "  make logs      - View logs"
	@echo "  make clean     - Remove all containers and volumes"
	@echo "  make init-db   - Initialize database with test data"
	@echo "  make test      - Run tests"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services started!"
	@echo "Admin UI: http://localhost:3000"
	@echo "API: http://localhost:8000"
	@echo "Telnet: telnet localhost 23"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	@echo "All containers and volumes removed"

init-db:
	docker-compose exec backend python scripts/init_test_data.py

test:
	@echo "Running backend tests..."
	docker-compose exec backend pytest
	@echo "Running frontend tests..."
	docker-compose exec frontend npm test

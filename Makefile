.PHONY: up down logs test clean build

# Build and start services
up:
	docker compose up -d --build

# Build only
build:
	docker compose build

# Stop and remove containers with volumes
down:
	docker compose down -v

# View logs
logs:
	docker compose logs -f api

# Run tests in container
test:
	docker compose run --rm api pytest -v tests/

# Clean up everything
clean:
	docker compose down -v
	rm -rf data/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Help
help:
	@echo "Available targets:"
	@echo "  up     - Build and start services"
	@echo "  down   - Stop and remove containers"
	@echo "  logs   - View container logs"
	@echo "  test   - Run tests"
	@echo "  clean  - Clean up everything"

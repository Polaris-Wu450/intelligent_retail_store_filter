.PHONY: test test-local test-docker test-unit test-integration test-error coverage clean help

# Default target
.DEFAULT_GOAL := help

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

test: test-docker  ## Run all tests in Docker (default)

test-docker:  ## Run tests in Docker containers
	@echo "Running tests in Docker..."
	./run_tests.sh

test-local:  ## Run tests locally
	@echo "Running tests locally..."
	./run_tests_local.sh

test-unit:  ## Run only unit tests
	@echo "Running unit tests..."
	pytest -m unit -v

test-integration:  ## Run only integration tests
	@echo "Running integration tests..."
	pytest -m integration -v

test-error:  ## Run only error handling tests
	@echo "Running error handling tests..."
	pytest -m error_handling -v

test-customer:  ## Run customer duplicate detection tests
	@echo "Running customer tests..."
	pytest tests/unit/test_customer_duplicate_detection.py -v

coverage:  ## Generate and open coverage report
	@echo "Generating coverage report..."
	pytest --cov=retailops --cov-report=html
	@echo "Opening coverage report..."
	@command -v open >/dev/null 2>&1 && open test-reports/htmlcov/index.html || \
	 command -v xdg-open >/dev/null 2>&1 && xdg-open test-reports/htmlcov/index.html || \
	 echo "Please open test-reports/htmlcov/index.html in your browser"

test-watch:  ## Run tests in watch mode (requires pytest-watch)
	@echo "Running tests in watch mode..."
	@command -v ptw >/dev/null 2>&1 || pip install pytest-watch
	ptw -- -v

test-quick:  ## Run tests without coverage (faster)
	@echo "Running quick tests..."
	pytest -v --tb=short

test-verbose:  ## Run tests with extra verbose output
	@echo "Running tests with verbose output..."
	pytest -vv --tb=long

clean:  ## Clean test artifacts and cache
	@echo "Cleaning test artifacts..."
	rm -rf test-reports/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Clean complete!"

install-test-deps:  ## Install test dependencies
	@echo "Installing test dependencies..."
	pip install -r requirements.txt

docker-build:  ## Build test Docker image
	@echo "Building test Docker image..."
	docker-compose -f docker-compose.test.yml build

docker-up:  ## Start test containers
	@echo "Starting test containers..."
	docker-compose -f docker-compose.test.yml up

docker-down:  ## Stop test containers
	@echo "Stopping test containers..."
	docker-compose -f docker-compose.test.yml down

docker-logs:  ## View test container logs
	docker-compose -f docker-compose.test.yml logs -f

lint:  ## Run code linting
	@echo "Running linters..."
	@command -v flake8 >/dev/null 2>&1 || pip install flake8
	flake8 retailops/ tests/ --exclude=migrations,__pycache__

format:  ## Format code with black
	@echo "Formatting code..."
	@command -v black >/dev/null 2>&1 || pip install black
	black retailops/ tests/

check:  ## Run linting and tests
	@$(MAKE) lint
	@$(MAKE) test

ci:  ## Run CI pipeline (lint + test + coverage)
	@echo "Running CI pipeline..."
	@$(MAKE) lint
	@$(MAKE) test-docker
	@$(MAKE) coverage

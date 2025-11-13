.PHONY: install install-dev test lint format clean run help

help:
	@echo "NightOwl - Oura sleep data collection"
	@echo ""
	@echo "Available targets:"
	@echo "  install      Install the package and runtime dependencies"
	@echo "  install-dev  Install the package with development dependencies"
	@echo "  test         Run tests with pytest"
	@echo "  lint         Run linting checks (ruff)"
	@echo "  format       Format code with black"
	@echo "  clean        Remove build artifacts and cache files"
	@echo "  run          Run the CLI script to pull sleep data"

install:
	pip install --upgrade pip
	pip install -e .

install-dev:
	pip install --upgrade pip
	pip install -e .[dev]

test:
	pytest

lint:
	ruff check nightowl/ tests/
	mypy nightowl/

format:
	black nightowl/ tests/ nightowl.py
	ruff check --fix nightowl/ tests/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

run:
	./nightowl.py

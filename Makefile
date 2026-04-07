# Makefile for medical-tender-scraper

.PHONY: help install test test-live lint format clean run

# Default target
help:
	@echo "Available targets:"
	@echo "  install     - Install dependencies"
	@echo "  test        - Run unit tests"
	@echo "  test-live   - Run tests with live network requests"
	@echo "  lint        - Run linting"
	@echo "  format      - Format code with black"
	@echo "  clean       - Clean generated files"
	@echo "  run         - Run the scraper with default settings"
	@echo "  run-verbose - Run with verbose output"

# Install dependencies
install:
	pip install -r requirements.txt

# Run unit tests
test:
	pytest tests/ -v --tb=short -m "not live"

# Run tests with coverage
test-cov:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Run live tests (requires network)
test-live:
	pytest tests/test_live_fetch.py -v --run-live

# Run all tests

test-all:
	pytest tests/ -v

# Lint code
lint:
	flake8 src tests
	mypy src

# Format code
format:
	black src tests --line-length 100

# Check formatting
check-format:
	black src tests --line-length 100 --check

# Clean generated files
clean:
	rm -rf __pycache__
	rm -rf src/__pycache__
	rm -rf src/*/__pycache__
	rm -rf tests/__pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*~" -delete

# Run the scraper
run:
	python run.py

# Run with verbose output
run-verbose:
	python run.py -v

# Run with custom keywords
run-眼科:
	python run.py -k 眼科 -v

run-皮肤科:
	python run.py -k 皮肤科 -v

# Run with multiple keywords
run-all:
	python run.py -k 眼科 皮肤科 口腔科 检验科 -v

# Run with extended time range
run-30d:
	python run.py -d 30 -v

# Run with multi-sheet export
run-multi:
	python run.py --multi-sheet -v

# Development setup
dev-setup:
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

# Windows specific commands (for PowerShell)
win-clean:
	Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force
	Get-ChildItem -Recurse -Filter *.pyc | Remove-Item -Force
	Get-ChildItem -Recurse -Filter .pytest_cache | Remove-Item -Recurse -Force

win-run:
	python run.py

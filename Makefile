.PHONY: install lint format test benchmark clean

install:
	pip install -e ".[dev]"

lint:
	ruff check src tests
	ruff format --check src tests

format:
	ruff check --fix src tests
	ruff format src tests

test:
	pytest -q

benchmark:
	satreg benchmark

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache

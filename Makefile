.PHONY: install install-arosics install-dl lint format test fetch benchmark n1 clean

install:
	pip install -e ".[dev]"

# GDAL's bindings must match the system GDAL (brew install gdal), so they are
# pinned to it before AROSICS pulls them in.
install-arosics:
	pip install "gdal==$$(gdal-config --version)"
	pip install -e ".[dev,arosics]"

# PyTorch, then the pretrained weights, downloaded once to PyTorch's cache
# (~/.cache/torch unless TORCH_HOME says otherwise), outside the repository.
install-dl:
	pip install -e ".[dev,dl]"
	python -c "from satreg.methods.raft import fetch_weights; print(*fetch_weights(), sep='\n')"

lint:
	ruff check src tests
	ruff format --check src tests

format:
	ruff check --fix src tests
	ruff format src tests

test:
	pytest -q

fetch:
	satreg fetch

benchmark:
	satreg benchmark

# The N1 results table, published in docs/evaluation.md.
n1:
	satreg benchmark --config configs/n1.toml

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
